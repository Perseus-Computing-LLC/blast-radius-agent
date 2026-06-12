# Orbit/Duo Tool Contract

This document defines the external tool contracts that the Blast Radius
Analyzer agent depends on. Because the agent is deployed to the GitLab
Duo Agent Platform (where these tools are provided at runtime), they are
declared here for reference, versioning, and validation.

## 1. GitLab Orbit — query_graph

**Purpose:** Traverse the codebase knowledge graph.

**Input:** A Cypher-style query string.

**Output:** JSON nodes and edges matching the query.

**Expected schema:**

| Node Type | Properties |
|---|---|
| `gl_definition` | `id`, `name`, `path`, `language`, `project_path` |
| `gl_documentation` | `id`, `content`, `definition_id` |

| Edge Type | Properties |
|---|---|
| `gl_reference` | `source_id`, `target_id`, `relationship_type` |
| `gl_documents` | `source_id`, `target_id` |

**Query examples:**

```
query_graph("MATCH (d:gl_definition) WHERE d.path CONTAINS 'target' RETURN d.id, d.name, d.path")
query_graph("MATCH (s)-[r:gl_reference]->(d:gl_definition) WHERE d.id = 42 RETURN s.id, s.path")
```

**Error states:**
- Empty result set → no matching definitions found
- Timeout → graph query took too long (complex traversal across many nodes)
- Cycle detected → infinite loop in recursive traversal (depth limit enforced)

## 2. GitLab Orbit — get_graph_schema

**Purpose:** Discover available node types and relationships.

**Input:** None.

**Output:** JSON describing all node types, edge types, and their properties.

**Behavior:** Returns a static schema. Called once per agent session for
schema introspection.

## 3. GitLab Duo Agent Platform — Create Issue Comment

**Purpose:** Post analysis results back to the triggering issue or MR.

**Input:** String content (the risk report).

**Output:** Comment posted on the issue/MR thread.

**Behavior:**
- Agent must have this tool enabled in its configuration
- Content is rendered as a standard GitLab comment (Markdown-supported)
- The comment appears under the agent's identity on the issue/MR

## 4. Orbit CLI — `orbit sql` (Local Fallback)

**Purpose:** Run SQL queries against a locally indexed Orbit database.

**Syntax:** `orbit sql "<query>"`

**Database schema:** SQLite-backed. Same `gl_definition` / `gl_reference` tables as the Remote mode.

**Fallback condition:** Used when Orbit Remote is unavailable (no Premium/Ultimate group, no network access to GitLab.com).

## 5. Contract Verification

To validate these contracts against a real GitLab instance:

```bash
# Verify Orbit Remote is accessible
curl -s -H "Authorization: Bearer $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/83196759/orbit/mcp/schema" \
  | python3 -m json.tool

# Verify Orbit CLI fallback
orbit sql "SELECT name FROM gl_definition WHERE path LIKE '%test%' LIMIT 1"

# Verify agent tool enabled
# Check: Project → AI → Agents → Blast Radius Analyzer → Tools → "Create issue comment" enabled
```

## 6. Version History

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-06-11 | Initial contract definition for GitLab Transcend Hackathon |
