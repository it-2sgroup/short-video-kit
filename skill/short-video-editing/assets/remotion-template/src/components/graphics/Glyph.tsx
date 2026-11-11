// Pictograms drawn as SVG (viewBox 0 0 110 100) in the theme's colours: target, megaphone, bang (!!!), search, check.
import React from "react";
import { palette } from "../../theme";

export const Glyph: React.FC<{ name: string }> = ({ name }) => {
  const R = palette.royal;
  const W = palette.white;
  const Y = palette.sky;
  switch (name) {
    case "target":
      return (
        <g>
          <circle cx={46} cy={54} r={40} fill={R} stroke={W} strokeWidth={5} />
          <circle cx={46} cy={54} r={28} fill={W} />
          <circle cx={46} cy={54} r={17} fill={R} />
          <circle cx={46} cy={54} r={6} fill={W} />
          <path d="M 46 54 L 86 14" stroke={palette.ink} strokeWidth={6} strokeLinecap="round" />
          <path d="M 86 14 L 80 28 M 86 14 L 72 20" stroke={Y} strokeWidth={6} strokeLinecap="round" />
        </g>
      );
    case "megaphone":
      return (
        <g strokeLinejoin="round" strokeLinecap="round">
          <path d="M 14 38 L 48 38 L 80 18 L 80 82 L 48 62 L 14 62 Z" fill={R} stroke={W} strokeWidth={6} />
          <path d="M 26 62 L 32 88 L 46 88 L 42 62" fill={R} stroke={W} strokeWidth={5} />
          <path d="M 90 36 Q 98 50 90 64 M 96 28 Q 110 50 96 72" fill="none" stroke={Y} strokeWidth={5} />
          <path d="M 92 14 L 100 26 M 104 8 L 106 24 M 112 26 L 100 34" fill="none" stroke={Y} strokeWidth={5} />
        </g>
      );
    case "bang":
      return (
        <g>
          {[18, 50, 82].map((x, i) => (
            <g key={x} transform={`rotate(${14 - i * 2} ${x} 50)`}>
              <rect x={x - 8} y={10} width={16} height={52} rx={8} fill={R} stroke={W} strokeWidth={4} />
              <circle cx={x} cy={82} r={9} fill={R} stroke={W} strokeWidth={4} />
            </g>
          ))}
        </g>
      );
    case "search":
      return (
        <g strokeLinejoin="round" strokeLinecap="round">
          <rect x={6} y={14} width={84} height={64} rx={9} fill={W} stroke={R} strokeWidth={5} />
          <path d="M 6 32 L 90 32" stroke={R} strokeWidth={4} />
          {[16, 26, 36].map((x) => (
            <circle key={x} cx={x} cy={23} r={3.2} fill={R} />
          ))}
          <path d="M 18 46 L 52 46 M 18 58 L 44 58" stroke={palette.ice} strokeWidth={6} />
          <circle cx={66} cy={56} r={20} fill="rgba(255,255,255,0.55)" stroke={palette.ink} strokeWidth={7} />
          <path d="M 80 70 L 98 90" stroke={palette.ink} strokeWidth={9} />
        </g>
      );
    case "check":
    default:
      return (
        <g>
          <circle cx={50} cy={50} r={42} fill={R} stroke={W} strokeWidth={5} />
          <path d="M 28 52 L 44 68 L 74 34" fill="none" stroke={Y} strokeWidth={11} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      );
  }
};

