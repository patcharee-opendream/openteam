# tasks/04‑sql‑reasoning/python/queries.py
from pathlib import Path

# --- path to donations.db --------------------------------------------------
DB_PATH = Path(__file__).resolve().parent.parent / "donations.db"

# --- Task A ---------------------------------------------------------------
SQL_A = """
SELECT
  c.id AS campaign_id,
  SUM(p.amount_thb) AS total_thb,
  ROUND(SUM(p.amount_thb) * 1.0 / c.target_thb, 4) AS pct_of_target
FROM campaign c
JOIN pledge p ON p.campaign_id = c.id
GROUP BY c.id, c.target_thb
ORDER BY pct_of_target DESC
LIMIT 10;
"""

# --- Task B ---------------------------------------------------------------
SQL_B = """
WITH all_pledges AS (
  SELECT 'global' AS scope, amount_thb FROM pledge
  UNION ALL
  SELECT 'thailand' AS scope, amount_thb FROM pledge p
    JOIN donor d ON p.donor_id = d.id
    WHERE d.country = 'Thailand'
)
SELECT
  scope,
  CAST(
    (SELECT amount_thb FROM (
      SELECT amount_thb, ROW_NUMBER() OVER (ORDER BY amount_thb) AS rn, COUNT(*) OVER () AS cnt
      FROM all_pledges ap WHERE ap.scope = a.scope
    ) WHERE rn = CAST(0.9 * cnt AS INTEGER) + 1
    ) AS INTEGER
  ) AS p90_thb
FROM (SELECT DISTINCT scope FROM all_pledges) a
ORDER BY scope;
"""

# --- (skipped) indexes -----------------------------------------------------
INDEXES: list[str] = []  # left empty on purpose
