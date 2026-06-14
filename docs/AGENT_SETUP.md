# GitLab Duo Agent Setup — Blast Radius Analyzer

**Status:** Repo fully synced (36 files). Awaiting Duo agent creation in GitLab UI.

## The Problem

Your project (`prestige-worldwidest/blast-radius-agent`) is in your personal namespace
which has `duoAgenticChatAvailable: false`. The hackathon-provisioned project should
land in `gitlab-ai-hackathon/transcend/` where AI features are enabled.

## What's Already Done

- [x] Full 36-file repo synced to GitLab (engine, tests, CI, docs, demo)
- [x] Agent manifest (`agent.yml`) follows GitLab Duo format
- [x] Agent skill (`skills/blast-radius/SKILL.md`) follows Agent Skills spec
- [x] System prompt ready (below)
- [x] GitHub CI all green (29/29 tests)
- [x] Demo video fixed and uploaded
- [x] Devpost entry live
- [x] Submission helper page (`submit.html`) in repo

## Step 1: Get the Hackathon Project Provisioned

Go to https://contributors.gitlab.com/transcend-hackathon
→ Showcase Track → Register (if not already done)
→ Wait for project provisioning in `gitlab-ai-hackathon/transcend/` namespace

Once provisioned, I'll sync this repo there and the AI features will be available.

## Step 2: Create the Agent (Browser UI)

Once in the correct namespace with AI features enabled:

1. Go to project → **Automate** → **Agents** (or **AI** → **Agents**)
2. Click **New agent**
3. Fill in:

**Display name:** `Blast Radius Analyzer`

**Description:**
```
Traces cross-file dependencies using GitLab Orbit to show you everything
that will break before you make a change.
```

**Visibility:** Public (required for AI Catalog publishing)

**System prompt (paste this):**
```
You are a dependency analysis expert. Your job is to help developers understand
the blast radius of code changes before they make them.

When a developer gives you a file path or function name, use GitLab Orbit's
knowledge graph to trace all dependencies:
1. Call get_graph_schema to understand available node types
2. Use query_graph to find:
   - Where this file/function is defined (gl_definition nodes)
   - What files reference it (cross-file imports via gl_reference edges)
   - What projects contain dependents
3. Summarize findings in a clear risk report

Always organize your response as:
- DIRECT IMPACT: Files that directly reference the changed code
- TRANSITIVE IMPACT: Files that depend on direct dependents
- PROJECT IMPACT: Projects affected
- RISK SCORE: Low/Medium/High/Critical based on dependency depth

Risk classification:
- Low: 0-2 direct dependents, no transitive
- Medium: 3-10 direct or 1-5 transitive
- High: 10-50 direct or 5-20 transitive
- Critical: 50+ dependents, or cross-project impact
```

**Tools to enable:**
- Create issue comment (to post risk reports)
- GitLab Orbit tools if available in the tool selector

## Step 3: Verify in AI Catalog

After creating:
1. Visit https://gitlab.com/explore/ai-catalog/agents/
2. Search for "Blast Radius Analyzer"
3. Confirm it appears and is Public
4. Enable it on a test project
5. Try: mention `@blast-radius src/auth/tokens.py` in an issue comment
