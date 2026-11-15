-- Reproduces the figures in references/niche-winning-patterns.md
-- Source: Supabase project "SISMO - KHACH HANG" (id cnlsipzreupurxptvbxt), table public.videos
-- Product: SAIZA mould remover, product id 1731438356080002524, shop 'SAIZA.VN'
--
-- READ FIRST - 3 traps:
--  1. USE the `videos` table (a snapshot). Do NOT sum `video_metrics_daily`: it repeats on a 7-day
--     cycle, so adding it up overstates the totals by more than 100 times.
--  2. Duration and CTR have no columns of their own - they live in raw_json:
--       (raw_json->>'duration')::numeric          seconds
--       (raw_json->>'click_through_rate')::numeric
--  3. When you JOIN shops, the column name `raw_json` is ambiguous -> always write v.raw_json.
-- The data does NOT have: retention / watch-through rate, hook type, cutting pace, audio.

-- 0. Scale: 16,242 videos, 45.5 million views, ~2.97 billion VND GMV, 33,067 products
SELECT COUNT(*) n_videos, SUM(views) total_views, ROUND(SUM(gmv)) total_gmv, SUM(units_sold) total_units
FROM videos v JOIN shops s ON s.id = v.shop_id
WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids);

-- 1. Top 20% by views vs the rest  -> the top 20% hold 95.1% of GMV
WITH base AS (
  SELECT v.*, NTILE(5) OVER (ORDER BY v.views DESC) AS q
  FROM videos v JOIN shops s ON s.id = v.shop_id
  WHERE s.shop_name = 'SAIZA.VN' AND '1731438356080002524' = ANY(v.product_ids) AND v.views > 0)
SELECT CASE WHEN q = 1 THEN 'TOP 20%' ELSE 'BOTTOM 80%' END grp, COUNT(*) n,
       ROUND(AVG(views)) avg_views, ROUND(SUM(gmv)) total_gmv,
       ROUND(100.0 * COUNT(*) FILTER (WHERE gmv > 0) / COUNT(*), 1) pct_with_sales
FROM base GROUP BY 1 ORDER BY 1 DESC;

-- 2. Duration -> CTR and the share of videos with orders both peak at 35-44s
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

-- 3. Control for the creator (KOC): does the 35-44s peak hold when only proven KOCs are counted?
--    (>=30 videos and >20 million VND GMV each)
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

-- 4. Concentration by KOC -> 9 KOCs hold 59.3% of GMV
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

-- 5. Posting hour (a weak hypothesis - small sample, no control for KOCs who post at night)
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
