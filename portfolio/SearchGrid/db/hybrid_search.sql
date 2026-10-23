-- $1 = text query, $2 = vector(384) query embedding, $3 = result limit
WITH lexical AS (
  SELECT id, row_number() OVER (ORDER BY ts_rank_cd(search_tsv, websearch_to_tsquery('english', $1)) DESC) AS rank
  FROM documents
  WHERE search_tsv @@ websearch_to_tsquery('english', $1)
  LIMIT 100
), semantic AS (
  SELECT id, row_number() OVER (ORDER BY embedding <=> $2) AS rank
  FROM documents
  WHERE embedding IS NOT NULL
  LIMIT 100
), fused AS (
  SELECT COALESCE(l.id, s.id) AS id,
         COALESCE(1.0 / (60 + l.rank), 0) + COALESCE(1.0 / (60 + s.rank), 0) AS rrf_score
  FROM lexical l FULL OUTER JOIN semantic s USING (id)
)
SELECT d.id, d.title, d.body, f.rrf_score
FROM fused f JOIN documents d USING (id)
ORDER BY f.rrf_score DESC
LIMIT $3;
