# branch
COUNT_BRANCHES = """
SELECT COUNT(*)
FROM branches
WHERE active = TRUE;
"""

GET_BRANCHES = """
SELECT id, name, location
FROM branches
WHERE active = TRUE
ORDER BY name;
"""

# pitch
GET_ALL_PITCHES_WITH_BRANCH = """
SELECT
    p.id,
    p.name,
    p.location,
    b.id AS branch_id,
    b.name AS branch_name
FROM pitches p
JOIN branches b ON p.branch_id = b.id
WHERE p.active = TRUE
  AND b.active = TRUE
ORDER BY b.name, p.name;
"""

GET_PITCHES_BY_BRANCH_ID = """
SELECT
    p.id,
    p.name,
    p.location
FROM pitches p
WHERE p.branch_id = %s
  AND p.active = TRUE
ORDER BY p.name;
"""

GET_PITCHES_BY_BRANCH_NAME = """
SELECT
    p.id,
    p.name,
    p.location,
    b.id AS branch_id,
    b.name AS branch_name
FROM pitches p
JOIN branches b ON p.branch_id = b.id
WHERE LOWER(b.name) = LOWER(%s)
  AND p.active = TRUE
  AND b.active = TRUE
ORDER BY p.name;
"""

GET_BRANCHES_WITH_PITCH_COUNT = """
SELECT
    b.id,
    b.name,
    COUNT(p.id) AS pitch_count
FROM branches b
LEFT JOIN pitches p
    ON p.branch_id = b.id
   AND p.active = TRUE
WHERE b.active = TRUE
GROUP BY b.id, b.name
ORDER BY b.name;
"""