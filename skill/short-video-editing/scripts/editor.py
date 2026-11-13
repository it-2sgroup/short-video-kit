#!/usr/bin/env python3
"""A browser timeline editor for a render project's project.json ("trình sửa video"). Standard library only.

    python scripts/editor.py RENDER_DIR [--project v1.json] [--port 5174] [--no-open]

RENDER_DIR is a render project made by new_remotion_project.py (it holds src/, public/, out/ and the
project JSON files). The server prints a URL on 127.0.0.1; open it in a browser. The page (assets/editor/)
shows the latest render (or the proxy clip of the current scene) in a phone frame, a timeline of scenes,
overlays, captions, voice, music and sound cues, and a properties panel. Edits live in the browser until
"Lưu project"; saving keeps the previous file in RENDER_DIR/.editor-history/ (the last 50 per project) and
"Render lại" runs the template's render command for the saved project. See references/editor.md.

What the server does, and nothing else:
  * serves the page from assets/editor/, media from RENDER_DIR/public (/media/...) and renders from
    RENDER_DIR/out (/out/...), with HTTP Range support; every path is resolved and refused if it leaves
    those folders (traversal, absolute paths, dot-files, symlinks pointing outside);
  * reads and saves the project JSON files that sit directly in RENDER_DIR (validated, history first, atomic);
  * computes waveform peaks with ffmpeg and caches them in the temp folder;
  * runs one fixed command, `npx remotion render ...`, one render at a time, in the background.
It binds to 127.0.0.1 only, accepts only its own Host and Origin, and runs no other program.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

HERE = Path(__file__).resolve().parent
ASSET_DIR = HERE.parent / "assets" / "editor"
SHARE = Path.home() / ".local" / "share" / "short-video-kit"
REPO_ROOT = HERE.parents[2]

HISTORY_KEEP = 50                    # snapshots kept per project file
MAX_BODY = 64 * 1024 * 1024          # largest request body accepted (a project with long word lists is well under 1 MB)
WAVE_RATE = 8000                     # Hz the audio is decoded to for the waveform
WAVE_PEAKS_PER_SECOND = 100
WAVE_VERSION = 1                     # bump to invalidate cached peaks
CACHE_DIR = Path(tempfile.gettempdir()) / "short-video-editor-cache"
NOT_PROJECTS = {"package.json", "package-lock.json", "tsconfig.json"}
PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.json$")
HISTORY_TS = r"\d{8}-\d{6}-\d{3}"
HISTORY_FILE = re.compile(rf"^(?P<stem>[A-Za-z0-9][A-Za-z0-9._-]*)-(?P<ts>{HISTORY_TS})\.json$")
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
PROGRESS = re.compile(r"(Rendered|Rendering|Encoded|Encoding|Stitched|Stitching)\D{0,40}?(\d+)\s*/\s*(\d+)")

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("audio/wav", ".wav")
mimetypes.add_type("audio/mpeg", ".mp3")
mimetypes.add_type("text/javascript", ".js")


class ApiError(Exception):
    def __init__(self, status: int, message: str, extra: dict | None = None):
        super().__init__(message)
        self.status, self.message, self.extra = status, message, extra or {}


# ----------------------------------------------------------------------------- paths and tools
def safe_join(base: Path, rel: str) -> Path | None:
    """Resolve `rel` under `base`. None when it would leave `base`: `..` segments, absolute or drive paths,
    NUL bytes, dot-files, or a symlink that points outside. The check is on the fully resolved path."""
    if not rel or "\x00" in rel:
        return None
    rel = rel.replace("\\", "/")
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        return None
    parts = [p for p in rel.split("/") if p not in ("", ".")]
    if not parts or any(p == ".." or p.startswith(".") for p in parts):
        return None
    root = base.resolve()
    target = root.joinpath(*parts).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def find_tool(name: str) -> str | None:
    """ffmpeg / ffprobe: on PATH, else where setup.sh --download-ffmpeg puts them."""
    found = shutil.which(name)
    if found:
        return found
    exe = name + (".exe" if os.name == "nt" else "")
    for folder in (SHARE / "bin", REPO_ROOT / "bin"):
        if (folder / exe).is_file():
            return str(folder / exe)
    return None


def mtime_ms(path: Path) -> int:
    return path.stat().st_mtime_ns // 1_000_000  # milliseconds fit a JS number exactly; nanoseconds do not


def atomic_write(path: Path, text: str) -> None:
    """Write beside the target, then rename over it, so a crash never leaves half a project file."""
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if path.exists():
            shutil.copymode(path, tmp)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def validate_project(obj) -> None:
    if not isinstance(obj, dict):
        raise ApiError(400, "Project phải là một đối tượng JSON.")
    scenes = obj.get("scenes")
    if not isinstance(scenes, list) or not all(isinstance(s, dict) for s in scenes):
        raise ApiError(400, "Project cần có danh sách `scenes` (mỗi cảnh là một đối tượng).")
    for key in ("overlays", "captions", "sfx", "captionBands", "words", "punches"):
        if key in obj and not isinstance(obj[key], list):
            raise ApiError(400, f"`{key}` phải là một danh sách.")
    if "duration" in obj and (isinstance(obj["duration"], bool) or not isinstance(obj["duration"], (int, float))):
        raise ApiError(400, "`duration` phải là số giây.")


def file_format(text: str) -> tuple[int, bool]:
    """Indent width and trailing newline of an existing project file, so a save changes only what was edited."""
    m = re.search(r"^( +)\S", text, re.M)
    return (len(m.group(1)) if m else 2), text.endswith("\n")


def dump_project(obj: dict, indent: int, newline: bool) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=indent, allow_nan=False) + ("\n" if newline else "")
    except ValueError as e:
        raise ApiError(400, f"Project có giá trị không hợp lệ: {e}")


# ----------------------------------------------------------------------------- the editor's model of a render project
class Editor:
    def __init__(self, render_dir: Path, project: str | None):
        self.dir = render_dir.resolve()
        self.public = self.dir / "public"
        self.out = self.dir / "out"
        self.history = self.dir / ".editor-history"
        self.lock = threading.RLock()
        self.default_project = project or self.pick_project()
        self.render = RenderJob(self)
        self._probe_cache: dict[tuple[str, int], float | None] = {}

    # ---- project files
    def read_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            return None

    def project_files(self) -> list[dict]:
        """Every JSON directly in the render folder that looks like a project (has a `scenes` list)."""
        out = []
        for p in sorted(self.dir.glob("*.json")):
            if p.name in NOT_PROJECTS or not PROJECT_NAME.match(p.name):
                continue
            obj = self.read_json(p)
            if isinstance(obj, dict) and isinstance(obj.get("scenes"), list):
                out.append({"name": p.name, "mtime": mtime_ms(p), "scenes": len(obj["scenes"]), "duration": obj.get("duration")})
        return out

    def pick_project(self) -> str:
        files = self.project_files()
        if not files:
            raise SystemExit(f"No project JSON (a file with a `scenes` list) in {self.dir}. Build one with plan_to_project.py first.")
        real = [f for f in files if f["name"] != "project.example.json"] or files
        return max(real, key=lambda f: f["mtime"])["name"]

    def project_path(self, name: str | None) -> Path:
        name = name or self.default_project
        if not PROJECT_NAME.match(name or "") or name in NOT_PROJECTS:
            raise ApiError(400, "Tên file project không hợp lệ.")
        path = self.dir / name
        if not path.is_file():
            raise ApiError(404, f"Không thấy {name} trong thư mục render.")
        return path

    def load(self, name: str | None) -> dict:
        path = self.project_path(name)
        obj = self.read_json(path)
        validate_project(obj)
        stem = path.stem
        render = self.render_for(stem)
        baseline, state = None, "none"
        if render:
            baseline = self.read_baseline(stem, render)
            state = "exact" if baseline is not None else ("synced" if mtime_ms(path) <= render["mtime"] else "stale")
        return {"name": path.name, "mtime": mtime_ms(path), "project": obj, "render": render,
                "baseline": baseline, "renderState": state}

    def save(self, name: str | None, obj, base_mtime: int | None, force: bool) -> dict:
        validate_project(obj)
        path = self.project_path(name)
        with self.lock:
            old_text = path.read_text(encoding="utf-8-sig")
            if base_mtime is not None and not force and abs(mtime_ms(path) - base_mtime) > 2:
                raise ApiError(409, "File project đã bị sửa ở nơi khác kể từ lúc mở (ví dụ plan_to_project.py chạy lại).",
                               {"mtime": mtime_ms(path)})
            if self.read_json(path) == obj:
                return {"ok": True, "unchanged": True, "mtime": mtime_ms(path)}
            indent, newline = file_format(old_text)
            new_text = dump_project(obj, indent, newline)
            snap = self.snapshot(path)
            atomic_write(path, new_text)
            return {"ok": True, "unchanged": False, "mtime": mtime_ms(path), "snapshot": snap.name if snap else None}

    # ---- history
    def snapshot(self, path: Path) -> Path | None:
        """Copy the current file into .editor-history/ and drop the oldest beyond HISTORY_KEEP."""
        self.history.mkdir(exist_ok=True)
        ns = time.time_ns()
        while True:
            when = datetime.fromtimestamp(ns / 1e9)
            snap = self.history / f"{path.stem}-{when:%Y%m%d-%H%M%S}-{(ns // 1_000_000) % 1000:03d}.json"
            if not snap.exists():
                break
            ns += 1_000_000
        shutil.copyfile(path, snap)
        mine = sorted(p for p in self.history.glob(f"{path.stem}-*.json")
                      if (m := HISTORY_FILE.match(p.name)) and m.group("stem") == path.stem)
        for old in mine[:-HISTORY_KEEP]:
            old.unlink(missing_ok=True)
        return snap

    def history_list(self, name: str | None) -> list[dict]:
        stem = self.project_path(name).stem
        items = []
        for p in sorted(self.history.glob(f"{stem}-*.json"), reverse=True) if self.history.is_dir() else []:
            m = HISTORY_FILE.match(p.name)
            if not m or m.group("stem") != stem:
                continue
            obj = self.read_json(p) or {}
            ts = datetime.strptime(m.group("ts")[:15], "%Y%m%d-%H%M%S")
            items.append({"id": p.name, "time": ts.strftime("%Y-%m-%d %H:%M:%S"), "size": p.stat().st_size,
                          "scenes": len(obj.get("scenes", [])), "overlays": len(obj.get("overlays", [])),
                          "duration": obj.get("duration")})
        return items

    def history_item(self, name: str | None, hid: str) -> tuple[Path, dict]:
        stem = self.project_path(name).stem
        m = HISTORY_FILE.match(hid or "")
        if not m or m.group("stem") != stem:
            raise ApiError(400, "Mã bản lịch sử không hợp lệ.")
        path = self.history / hid
        if not path.is_file():
            raise ApiError(404, "Không thấy bản lịch sử này.")
        obj = self.read_json(path)
        validate_project(obj)
        return path, obj

    def restore(self, name: str | None, hid: str) -> dict:
        snap, obj = self.history_item(name, hid)
        path = self.project_path(name)
        with self.lock:
            if self.read_json(path) != obj:
                self.snapshot(path)  # restoring is itself undoable
            atomic_write(path, snap.read_text(encoding="utf-8-sig"))
        return {"ok": True, "mtime": mtime_ms(path), "project": obj}

    # ---- renders
    def renders(self) -> list[dict]:
        if not self.out.is_dir():
            return []
        items = [{"name": p.name, "size": p.stat().st_size, "mtime": mtime_ms(p), "url": f"/out/{p.name}"}
                 for p in self.out.glob("*.mp4") if p.is_file()]
        return sorted(items, key=lambda r: r["mtime"], reverse=True)

    def render_for(self, stem: str) -> dict | None:
        """The render the preview plays for this project: out/<stem>.mp4, else the newest mp4 in out/."""
        items = self.renders()
        mine = [r for r in items if r["name"] == f"{stem}.mp4"]
        return (mine or items or [None])[0]

    def read_baseline(self, stem: str, render: dict) -> dict | None:
        """The project exactly as the last editor-started render saw it, when it belongs to this very mp4."""
        if render["name"] != f"{stem}.mp4":
            return None
        data = self.read_json(self.history / f"{stem}.rendered.json")
        if isinstance(data, dict) and isinstance(data.get("project"), dict) and abs(data.get("mp4_mtime", -1) - render["mtime"]) <= 1500:
            return data["project"]
        return None

    # ---- assets the pickers offer
    def probe_duration(self, path: Path) -> float | None:
        key = (str(path), path.stat().st_mtime_ns)
        if key not in self._probe_cache:
            ffprobe, dur = find_tool("ffprobe"), None
            if ffprobe:
                try:
                    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                       capture_output=True, text=True, timeout=20)
                    dur = round(float(r.stdout.strip()), 3)
                except (OSError, ValueError, subprocess.SubprocessError):
                    dur = None
            self._probe_cache[key] = dur
        return self._probe_cache[key]

    def assets(self) -> dict:
        def listing(sub: str, exts: tuple[str, ...]) -> list[Path]:
            folder = self.public / sub
            return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts and not p.name.startswith(".")) if folder.is_dir() else []
        clips = [{"name": p.stem, "file": p.name, "duration": self.probe_duration(p)} for p in listing("clips", (".mp4", ".mov", ".m4v", ".webm"))]
        audio_ext = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac")
        return {"clips": clips,
                "audio": [f"audio/{p.name}" for p in listing("audio", audio_ext)],
                "sfx": [f"sfx/{p.name}" for p in listing("sfx", audio_ext)],
                "images": [f"images/{p.name}" for p in listing("images", (".png", ".jpg", ".jpeg", ".webp", ".svg"))]}

    def schema(self) -> dict:
        """Component names and the string unions of the template's types, read from RENDER_DIR/src so the editor
        follows the template; the page has its own fallbacks when a file is missing."""
        components, unions = [], {}
        reg = self.dir / "src" / "components" / "registry.tsx"
        if reg.is_file():
            m = re.search(r"registry\s*:\s*Record<[^>]*>\s*=\s*\{(.*?)\n\};", reg.read_text(encoding="utf-8"), re.S)
            components = re.findall(r"^\s*(\w+)\s*:", m.group(1), re.M) if m else []
        proj = self.dir / "src" / "project.ts"
        if proj.is_file():
            text = re.sub(r"//[^\n]*", "", proj.read_text(encoding="utf-8"))
            for name in ("TransitionType", "Direction", "CameraMove", "CameraEase", "Layout", "Zone", "Tone", "CaptionStyle", "CaptionHighlight"):
                m = re.search(rf"export type {name}\s*=(.*?);", text, re.S)
                if m:
                    unions[name] = re.findall(r'"([\w-]+)"', m.group(1))
        return {"components": components, "unions": unions}

    # ---- waveform
    def waveform(self, src: str) -> dict:
        path = safe_join(self.public, src)
        if not path or not path.is_file():
            raise ApiError(404, "Không thấy file âm thanh trong public/.")
        ffmpeg = find_tool("ffmpeg")
        if not ffmpeg:
            raise ApiError(503, "Chưa có ffmpeg (chạy ./setup.sh --check).")
        st = path.stat()
        key = hashlib.sha1(f"{path}|{st.st_mtime_ns}|{st.st_size}|{WAVE_VERSION}".encode()).hexdigest()[:24]
        cached = CACHE_DIR / f"{key}.json"
        try:
            return json.loads(cached.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        try:
            r = subprocess.run([ffmpeg, "-v", "error", "-nostdin", "-i", str(path), "-vn", "-ac", "1", "-ar", str(WAVE_RATE), "-f", "s16le", "-"],
                               capture_output=True, timeout=180)
        except (OSError, subprocess.SubprocessError) as e:
            raise ApiError(500, f"ffmpeg không đọc được file: {e}")
        if r.returncode != 0:
            raise ApiError(422, "ffmpeg không giải mã được file này.")
        samples = array.array("h")
        samples.frombytes(r.stdout[: len(r.stdout) // 2 * 2])
        if sys.byteorder == "big":
            samples.byteswap()
        step = WAVE_RATE // WAVE_PEAKS_PER_SECOND
        raw = [max(map(abs, samples[i:i + step])) for i in range(0, len(samples), step)]
        top = max(raw, default=0)
        result = {"src": src, "rate": WAVE_PEAKS_PER_SECOND, "duration": round(len(samples) / WAVE_RATE, 3),
                  "level": round(top / 32768, 4), "peaks": [round(v * 255 / top) for v in raw] if top else raw}
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            atomic_write(cached, json.dumps(result))
        except OSError:
            pass  # the cache is an optimisation only
        return result


# ----------------------------------------------------------------------------- the one command we run
class RenderJob:
    """`npx remotion render src/index.ts Short out/<name>.mp4 --props=<project> ...` in the render folder, in the
    background, one at a time. The only user-supplied part is the project file name, which must be a project
    JSON that exists in the render folder; concurrency is 5, or the core count when that is lower."""

    def __init__(self, editor: Editor):
        self.ed = editor
        self.lock = threading.Lock()
        self.proc: subprocess.Popen | None = None
        self.state = "idle"  # idle | running | done | failed | cancelled
        self.name = self.output = ""
        self.started = self.finished = 0.0
        self.returncode: int | None = None
        self.log: deque[str] = deque(maxlen=300)
        self.progress: dict = {}
        self.cancelled = False

    def start(self, name: str | None) -> dict:
        path = self.ed.project_path(name)
        npx = shutil.which("npx")
        if not npx or not (self.ed.dir / "node_modules" / ".bin").is_dir():
            raise ApiError(412, "Chưa cài Node/npm packages cho thư mục render: chạy `npm install` trong đó (tải ~300 MB, hãy hỏi chủ dự án trước).")
        with self.lock:
            if self.state == "running":
                raise ApiError(409, "Đang có một lần render chạy.")
            stem = path.stem
            cmd = [npx, "remotion", "render", "src/index.ts", "Short", f"out/{stem}.mp4", f"--props={path.name}",
                   "--codec=h264", "--crf=18", f"--concurrency={min(5, os.cpu_count() or 1)}"]  # Remotion refuses more workers than cores
            with self.ed.lock:  # the exact project the render will read, kept to count later edits
                self.ed.history.mkdir(exist_ok=True)
                shutil.copyfile(path, self.ed.history / f"{stem}.rendering.json")
            kwargs: dict = {"start_new_session": True} if os.name != "nt" else {"creationflags": getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)}
            env = {**os.environ, "FORCE_COLOR": "0", "NO_COLOR": "1", "CI": "1"}
            try:
                self.proc = subprocess.Popen(cmd, cwd=self.ed.dir, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, env=env, **kwargs)
            except OSError as e:
                raise ApiError(500, f"Không chạy được lệnh render: {e}")
            self.state, self.name, self.output = "running", path.name, f"out/{stem}.mp4"
            self.started, self.finished, self.returncode, self.cancelled = time.time(), 0.0, None, False
            self.log.clear()
            self.log.append("$ " + " ".join(["npx"] + cmd[1:]))
            self.progress = {}
            threading.Thread(target=self._pump, args=(self.proc, stem), daemon=True).start()
        return self.status()

    def _pump(self, proc: subprocess.Popen, stem: str) -> None:
        buf = ""
        while True:
            chunk = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
            if not chunk:
                break
            buf += chunk.decode("utf-8", "replace")
            *lines, buf = re.split(r"[\r\n]+", buf)
            for line in lines:
                self._line(ANSI.sub("", line).strip())
        self._line(ANSI.sub("", buf).strip())
        code = proc.wait()
        with self.lock:
            self.returncode, self.finished = code, time.time()
            out = self.ed.dir / self.output
            if self.cancelled:
                self.state = "cancelled"
            elif code == 0 and out.is_file():
                self.state = "done"
            else:
                self.state = "failed"
        rendering = self.ed.history / f"{stem}.rendering.json"
        if self.state == "done":
            self._promote_baseline(stem, rendering, out)
        rendering.unlink(missing_ok=True)

    def _line(self, line: str) -> None:
        if not line:
            return
        m = PROGRESS.search(line)
        with self.lock:
            if m:
                self.progress = {"stage": m.group(1), "done": int(m.group(2)), "total": int(m.group(3))}
                if self.log and PROGRESS.search(self.log[-1]):
                    self.log[-1] = line  # progress lines replace each other instead of flooding the log
                    return
            self.log.append(line)

    def _promote_baseline(self, stem: str, rendering: Path, out: Path) -> None:
        obj = self.ed.read_json(rendering)
        if isinstance(obj, dict):
            atomic_write(self.ed.history / f"{stem}.rendered.json", json.dumps({"mp4_mtime": mtime_ms(out), "project": obj}, ensure_ascii=False))

    def cancel(self) -> dict:
        with self.lock:
            if self.state != "running" or not self.proc:
                raise ApiError(409, "Không có lần render nào đang chạy.")
            self.cancelled = True
            self.terminate()
        return self.status()

    def terminate(self) -> None:
        proc = self.proc
        if not proc or proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                proc.terminate()
            else:
                os.killpg(proc.pid, signal.SIGTERM)  # npx starts node and chrome: stop the whole group
        except (OSError, ProcessLookupError):
            pass

    def status(self) -> dict:
        with self.lock:
            end = self.finished or time.time()
            return {"state": self.state, "name": self.name, "output": self.output, "returncode": self.returncode,
                    "elapsed": round(end - self.started, 1) if self.started else 0, "progress": dict(self.progress),
                    "log": list(self.log)[-40:]}


# ----------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "svk-editor"
    protocol_version = "HTTP/1.1"

    @property
    def ed(self) -> Editor:
        return self.server.editor  # type: ignore[attr-defined]

    def log_request(self, code="-", size="-"):  # quiet unless something went wrong
        if str(code).isdigit() and int(code) >= 400:
            sys.stderr.write(f"[editor] {code} {self.command} {self.path}\n")

    def log_message(self, fmt, *args):
        pass

    # ---- plumbing
    def send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def fail(self, status: int, message: str, extra: dict | None = None) -> None:
        self.send_json({"error": message, **(extra or {})}, status)

    def guard(self) -> bool:
        """Refuse requests that did not come from this page on this machine (DNS rebinding, cross-site forms)."""
        host = (self.headers.get("Host") or "").lower()
        origin = (self.headers.get("Origin") or "").lower()
        if host not in self.server.allowed_hosts or (origin and origin not in self.server.allowed_origins):  # type: ignore[attr-defined]
            self.fail(403, "Yêu cầu không đến từ trang trình sửa này.")
            return False
        return True

    def read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0 or length > MAX_BODY:
            self.close_connection = True  # the body stays unread, so the connection cannot be reused
            raise ApiError(413 if length > 0 else 400, "Nội dung gửi lên không hợp lệ hoặc quá lớn.")
        raw = self.rfile.read(length)  # always consume the body so the keep-alive connection stays in step
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
            raise ApiError(415, "Cần Content-Type: application/json.")
        try:
            return json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "Không đọc được JSON gửi lên.")

    def send_file(self, path: Path) -> None:
        """Serve a file with ETag and single-range support (browsers seek in video and audio with Range)."""
        try:
            st = path.stat()
            size = st.st_size
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            etag = f'"{st.st_mtime_ns:x}-{size:x}"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return
            start, end, status = 0, size - 1, 200
            header = self.headers.get("Range")
            if header:
                m = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
                if m and (m.group(1) or m.group(2)):
                    if m.group(1):
                        start = int(m.group(1))
                        end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
                    else:  # suffix range: the last N bytes
                        start, end = max(0, size - int(m.group(2))), size - 1
                    if start >= size or start > end:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    status = 206
            length = end - start + 1 if size else 0
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(length))
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if self.command == "HEAD" or not length:
                return
            with open(path, "rb") as f:
                f.seek(start)
                left = length
                while left > 0:
                    data = f.read(min(1 << 16, left))
                    if not data:
                        break
                    self.wfile.write(data)
                    left -= len(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            self.close_connection = True  # the browser cancelled a seek: normal

    def serve_under(self, base: Path, rel: str) -> None:
        target = safe_join(base, rel)
        if target is None:
            return self.fail(403, "Đường dẫn không được phép.")
        if not target.is_file():
            return self.fail(404, "Không thấy file.")
        self.send_file(target)

    # ---- routing
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self.guard():
            return
        url = urlsplit(self.path)
        path, query = unquote(url.path), {k: v[-1] for k, v in parse_qs(url.query).items()}
        try:
            if path.startswith("/media/"):
                return self.serve_under(self.ed.public, path[len("/media/"):])
            if path.startswith("/out/"):
                return self.serve_under(self.ed.out, path[len("/out/"):])
            if path.startswith("/api/"):
                return self.api_get(path, query)
            name = "index.html" if path == "/" else path.lstrip("/")
            if "/" in name or name.startswith(".") or name not in {p.name for p in ASSET_DIR.iterdir() if p.is_file()}:
                return self.fail(404, "Không thấy trang.")
            self.send_file(ASSET_DIR / name)
        except ApiError as e:
            self.fail(e.status, e.message, e.extra)
        except Exception as e:  # keep the server alive; the page shows the message
            self.fail(500, f"Lỗi máy chủ: {e}")

    def api_get(self, path: str, q: dict) -> None:
        ed = self.ed
        if path == "/api/info":
            return self.send_json({"dir": ed.dir.name, "default": ed.default_project, "projects": ed.project_files(),
                                   "renders": ed.renders(), "ffmpeg": bool(find_tool("ffmpeg")),
                                   "canRender": bool(shutil.which("npx") and (ed.dir / "node_modules" / ".bin").is_dir()),
                                   "historyKeep": HISTORY_KEEP})
        if path == "/api/project":
            return self.send_json(ed.load(q.get("name")))
        if path == "/api/history":
            return self.send_json({"items": ed.history_list(q.get("name"))})
        if path == "/api/history/item":
            return self.send_json({"project": ed.history_item(q.get("name"), q.get("id", ""))[1]})
        if path == "/api/assets":
            return self.send_json(ed.assets())
        if path == "/api/schema":
            return self.send_json(ed.schema())
        if path == "/api/waveform":
            return self.send_json(ed.waveform(q.get("src", "")))
        if path == "/api/render/status":
            return self.send_json(ed.render.status())
        self.fail(404, "Không có API này.")

    def do_POST(self):
        if not self.guard():
            return
        url = urlsplit(self.path)
        path, q = unquote(url.path), {k: v[-1] for k, v in parse_qs(url.query).items()}
        try:
            body = self.read_json_body()
            ed = self.ed
            if path == "/api/project":
                base = int(q["base"]) if q.get("base", "").lstrip("-").isdigit() else None
                return self.send_json(ed.save(q.get("name"), body, base, q.get("force") == "1"))
            if path == "/api/history/restore":
                return self.send_json(ed.restore(body.get("name"), body.get("id", "")) if isinstance(body, dict) else {})
            if path == "/api/render":
                return self.send_json(ed.render.start(body.get("name") if isinstance(body, dict) else None), 202)
            if path == "/api/render/cancel":
                return self.send_json(ed.render.cancel())
            self.fail(404, "Không có API này.")
        except ApiError as e:
            self.fail(e.status, e.message, e.extra)
        except Exception as e:
            self.fail(500, f"Lỗi máy chủ: {e}")


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(editor: Editor, port: int) -> Server:
    """Bind 127.0.0.1 only; when the port is taken try the next ones (port 0 = any free port)."""
    last: OSError | None = None
    for p in ([0] if port == 0 else range(port, port + 20)):
        try:
            srv = Server(("127.0.0.1", p), Handler)
            break
        except OSError as e:
            last = e
    else:
        raise SystemExit(f"Cannot bind a port from {port}: {last}")
    srv.editor = editor  # type: ignore[attr-defined]
    actual = srv.server_address[1]
    srv.allowed_hosts = {f"127.0.0.1:{actual}", f"localhost:{actual}"}  # type: ignore[attr-defined]
    srv.allowed_origins = {f"http://{h}" for h in srv.allowed_hosts}  # type: ignore[attr-defined]
    return srv


def main() -> None:
    ap = argparse.ArgumentParser(description="Browser timeline editor for a render project's project.json.")
    ap.add_argument("render_dir", type=Path, help="render project folder (src/, public/, out/, v1.json ...)")
    ap.add_argument("--project", help="project JSON to open (default: the newest one in the folder)")
    ap.add_argument("--port", type=int, default=5174, help="port on 127.0.0.1 (default 5174; 0 = any free port)")
    ap.add_argument("--no-open", action="store_true", help="do not open the browser")
    args = ap.parse_args()
    if not args.render_dir.is_dir():
        sys.exit(f"{args.render_dir} is not a folder.")
    if not (ASSET_DIR / "index.html").is_file():
        sys.exit(f"Editor page missing: {ASSET_DIR}")
    editor = Editor(args.render_dir, Path(args.project).name if args.project else None)
    editor.project_path(editor.default_project)  # fail early on a wrong --project
    srv = make_server(editor, args.port)
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"Video editor for {editor.dir.name}/{editor.default_project}: {url}", flush=True)
    print("Ctrl+C to stop (a running render is stopped too).", flush=True)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    if not args.no_open:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        editor.render.terminate()
        srv.server_close()


if __name__ == "__main__":
    main()
