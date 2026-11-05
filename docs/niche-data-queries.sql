-- Tái hiện số liệu trong references/niche-winning-patterns.md
-- Nguồn: Supabase project "SISMO - KHACH HANG" (id cnlsipzreupurxptvbxt), bảng public.videos
-- Sản phẩm: SAIZA tẩy mốc, product id 1731438356080002524, shop 'SAIZA.VN'
--
-- ĐỌC TRƯỚC — 3 cái bẫy:
--  1. DÙNG bảng `videos` (ảnh chụp). KHÔNG cộng `video_metrics_daily`: nó lặp theo chu kỳ 7 ngày
--     nên cộng dồn sai hơn 100 lần.
--  2. Thời lượng và CTR không có cột riêng — nằm trong raw_json:
--       (raw_json->>'duration')::numeric          giây
--       (raw_json->>'click_through_rate')::numeric
--  3. Khi JOIN shops, tên cột `raw_json` bị trùng -> luôn ghi rõ v.raw_json.
-- Dữ liệu KHÔNG có: retention / tỉ lệ xem hết, loại hook, nhịp cắt, âm thanh.

-- 0. Quy mô: 16.242 video, 45,5 triệu view, ~2,97 tỷ VNĐ GMV, 33.067 sản phẩm
SELECT COUNT(*) n_videos, SUM(views) total_views, ROUND(SUM(gmv)) total_gmv, SUM(units_sold) total_units
FROM videos v JOIN shops s ON s.id = v.shop_id
WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids);

-- 1. Top 20% theo view vs phần còn lại  -> top 20% chiếm 95,1% GMV
WITH base AS (
  SELECT v.*, NTILE(5) OVER (ORDER BY v.views DESC) AS q
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids) AND v.views > 0)
SELECT CASE WHEN q = 1 THEN 'TOP 20%' ELSE 'BOTTOM 80%' END grp, COUNT(*) n,
       ROUND(AVG(views)) avg_views, ROUND(SUM(gmv)) total_gmv,
       ROUND(100.0 * COUNT(*) FILTER (WHERE gmv > 0) / COUNT(*), 1) pct_with_sales
FROM base GROUP BY 1 ORDER BY 1 DESC;

-- 2. Thời lượng -> CTR và tỉ lệ có đơn đạt đỉnh ở 35-44s
WITH b AS (
  SELECT v.views, v.gmv, (v.raw_json->>'duration')::numeric dur,
         (v.raw_json->>'click_through_rate')::numeric ctr
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids)
    AND v.views > 0 AND v.raw_json->>'duration' IS NOT NULL)
SELECT CASE WHEN dur<15 THEN 'a: <15s' WHEN dur<25 THEN 'b: 15-24s' WHEN dur<35 THEN 'c: 25-34s'
            WHEN dur<45 THEN 'd: 35-44s' WHEN dur<60 THEN 'e: 45-59s' WHEN dur<90 THEN 'f: 60-89s'
            ELSE 'g: 90s+' END band,
       COUNT(*) n, ROUND(AVG(views)) avg_views, ROUND(AVG(ctr)::numeric, 4) avg_ctr,
       ROUND(100.0 * COUNT(*) FILTER (WHERE gmv > 0) / COUNT(*), 1) pct_with_sales
FROM b GROUP BY 1 ORDER BY 1;

-- 3. Kiểm soát theo KOC: giữ nguyên đỉnh 35-44s khi chỉ xét KOC đã chứng minh được?
--    (>=30 video và >20 triệu VNĐ GMV mỗi người)
WITH b AS (
  SELECT v.creator_name, v.views, v.gmv, (v.raw_json->>'duration')::numeric dur,
         (v.raw_json->>'click_through_rate')::numeric ctr
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids)
    AND v.views >= 100 AND v.raw_json->>'duration' IS NOT NULL),
top_creators AS (
  SELECT creator_name FROM b GROUP BY creator_name HAVING COUNT(*) >= 30 AND SUM(gmv) > 20000000)
SELECT CASE WHEN dur<25 THEN 'a: <25s' WHEN dur<35 THEN 'b: 25-34s' WHEN dur<45 THEN 'c: 35-44s'
            ELSE 'd: 45s+' END band,
       COUNT(*) n, COUNT(DISTINCT b.creator_name) n_creators,
       ROUND(AVG(ctr)::numeric, 4) avg_ctr,
       ROUND(100.0 * COUNT(*) FILTER (WHERE gmv > 0) / COUNT(*), 1) pct_with_sales
FROM b JOIN top_creators t USING (creator_name) GROUP BY 1 ORDER BY 1;

-- 4. Mức tập trung theo KOC -> 9 KOC chiếm 59,3% GMV
WITH base AS (
  SELECT v.creator_name, v.views, v.gmv
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids) AND v.views > 0),
agg AS (SELECT creator_name, COUNT(*) n_videos, SUM(views) tot_views, SUM(gmv) tot_gmv
        FROM base GROUP BY creator_name)
SELECT creator_name, n_videos, tot_views, ROUND(tot_gmv) tot_gmv,
       ROUND(tot_gmv / NULLIF(tot_views, 0) * 1000) gmv_per_1k_views,
       ROUND(100.0 * SUM(tot_gmv) OVER (ORDER BY tot_gmv DESC) / SUM(tot_gmv) OVER (), 1) cumulative_pct
FROM agg ORDER BY tot_gmv DESC LIMIT 15;

-- 5. Giờ đăng (giả thuyết yếu — mẫu nhỏ, chưa kiểm soát KOC nào đăng đêm)
WITH b AS (
  SELECT v.views, v.gmv, EXTRACT(HOUR FROM v.post_time AT TIME ZONE 'Asia/Ho_Chi_Minh') hr
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids)
    AND v.views >= 100 AND v.post_time IS NOT NULL)
SELECT CASE WHEN hr BETWEEN 5 AND 9 THEN '05-09' WHEN hr BETWEEN 10 AND 13 THEN '10-13'
            WHEN hr BETWEEN 14 AND 17 THEN '14-17' WHEN hr BETWEEN 18 AND 21 THEN '18-21'
            ELSE '22-04' END slot, COUNT(*) n, ROUND(AVG(views)) avg_views,
       ROUND(100.0 * COUNT(*) FILTER (WHERE gmv > 0) / COUNT(*), 1) pct_sales
FROM b GROUP BY 1 ORDER BY avg_views DESC;
