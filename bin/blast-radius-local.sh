#!/usr/bin/env bash
# Blast Radius Analyzer — Orbit CLI Local Fallback
#
# Usage: ./bin/blast-radius-local.sh <file-path> [max-depth]
#
# Requires: orbit CLI installed and a project indexed with `orbit index`
#
# Example:
#   ./bin/blast-radius-local.sh src/auth/tokens.py 3

set -euo pipefail

TARGET="${1:?Usage: blast-radius-local.sh <file-path> [max-depth]}"
MAX_DEPTH="${2:-3}"

echo "◆ Blast Radius Analysis (local — Orbit CLI)"
echo "   Target: $TARGET"
echo "   Depth:  $MAX_DEPTH"
echo ""

# Step 1: Find the definition
echo "○ Finding definition..."
DEF_QUERY="SELECT id, name, path, language FROM gl_definition WHERE path LIKE '%$TARGET%' OR name LIKE '%$TARGET%' LIMIT 5"
orbit sql "$DEF_QUERY" 2>/dev/null || {
    echo "✗ No matching definition found for '$TARGET'"
    echo "  Tips: Use a full file path like 'src/auth/tokens.py'"
    echo "        Make sure the project is indexed: orbit index /path/to/project"
    exit 1
}

# Step 2: Direct dependents
echo ""
echo "○ Tracing direct dependents..."
DIRECT_QUERY="SELECT DISTINCT t2.path, t2.name FROM gl_definition t1 JOIN gl_reference ON t1.id = gl_reference.target_id JOIN gl_definition t2 ON gl_reference.source_id = t2.id WHERE t1.path LIKE '%$TARGET%'"
orbit sql "$DIRECT_QUERY" 2>/dev/null || echo "(no direct dependents found)"

# Step 3: Transitive dependents (up to MAX_DEPTH)
echo ""
echo "○ Tracing transitive dependents (depth: $MAX_DEPTH)..."

for ((depth=2; depth<=MAX_DEPTH; depth++)); do
  echo "  Level $depth..."
  # Build a CTE-like query for transitive traversal
  TRANSITIVE_QUERY="
    WITH RECURSIVE dep_chain(id, path, depth) AS (
      SELECT t2.id, t2.path, 1
      FROM gl_definition t1
      JOIN gl_reference ON t1.id = gl_reference.target_id
      JOIN gl_definition t2 ON gl_reference.source_id = t2.id
      WHERE t1.path LIKE '%$TARGET%'
      UNION
      SELECT t3.id, t3.path, dep_chain.depth + 1
      FROM dep_chain
      JOIN gl_reference ON dep_chain.id = gl_reference.target_id
      JOIN gl_definition t3 ON gl_reference.source_id = t3.id
      WHERE dep_chain.depth < $depth
        AND t3.id NOT IN (SELECT id FROM dep_chain)
    )
    SELECT DISTINCT path FROM dep_chain WHERE depth = $depth
  "
  orbit sql "$TRANSITIVE_QUERY" 2>/dev/null || echo "  (no transitive dependents at level $depth)"
done

echo ""
echo "✓ Analysis complete"
