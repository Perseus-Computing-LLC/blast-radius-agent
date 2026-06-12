# Demo Video Script — Blast Radius Analyzer

> **Note (issue #12):** `demo/demo_terminal.html` is a scripted **simulation**
> with hard-coded output, intended only as a storyboard for recording. The
> "Live Demo" scene below should be captured from a real agent invocation (or
> the local engine: `blast-radius <path>`), not from the simulated terminal.

**Target:** 2:45-2:55 (under 3-minute limit)
**Style:** Screen recording of GitLab UI + voiceover (simulated terminal)
**Upload:** YouTube (public)
**Note:** This demo uses a terminal simulation to illustrate the agent flow. In a production environment, the agent would be invoked by mentioning @blast-radius in a real GitLab issue or MR.

---

## Scene 1: The Problem (0:00-0:35)

**Visual:** GitLab issue showing a simple code change request. On screen: "Change `checkToken` to return `Result<Token, Error>` instead of `Token | null`"

**Narration:**
> Every developer knows this feeling. You need to make a small change — update a function signature, rename a constant, move a file.
>
> It's one line. You make the change, push, merge.
>
> [Cut to: CI pipeline turning red, Slack notifications firing]
>
> Three hours later, CI catches what you missed. Your "one-line change" broke six downstream services. Three projects, twelve files, one function signature change. Nobody saw it coming.
>
> This happens because developers can't see the blast radius of their changes. You can find-references in your IDE, but that shows immediate callers — not what depends on THEM. Not across projects. Not across repositories.

---

## Scene 2: The Solution — Meet Blast Radius Analyzer (0:35-1:00)

**Visual:** GitLab project page → AI Catalog → Blast Radius Analyzer agent card. Show the agent description, system prompt snippet, and Orbit integration.

**Narration:**
> Meet Blast Radius Analyzer — a GitLab Duo custom agent powered by GitLab Orbit's knowledge graph.
>
> It answers the question every developer needs answered before making a change: what depends on this code?
>
> The agent is published to the GitLab AI Catalog. Enable it on any project in one click. It works where you already work — inside GitLab issues and merge requests.

---

## Scene 3: Live Demo (1:00-2:15)

**Visual:** GitLab issue for the `checkToken` refactor. Type `@blast-radius src/auth/tokens.py -- checkToken function` in the comment box. Submit.

**Narration:**
> Here's how it works. I'm in a GitLab issue for a token refactor. I want to change the `checkToken` function in `src/auth/tokens.py`.
>
> Before I write a single line, I'll ask Blast Radius what depends on it. Just mention the agent with the file path.

**[Visual: Agent thinking indicator, then the report appears as a comment]**

**Narration:**
> In seconds, Blast Radius queries GitLab Orbit's knowledge graph. It finds the `checkToken` definition, then traces every `gl_reference` edge backwards to find everything that imports or calls it.
>
> Let me walk through the report.

**Visual:** Highlight parts of the report as they're mentioned.

**Narration:**
> **Direct impact** — three files directly import `checkToken`. The API middleware, the GraphQL resolvers, and the Stripe webhook handler. If you change the return type, all three break.
>
> **Transitive impact** — twelve files depend on those direct dependents. All API routes use the middleware. All GraphQL schemas import the resolvers. Three microservices call the webhook handler.
>
> **Project impact** — your change touches the core API, the billing service, AND the notifications service.
>
> **Risk score: HIGH.** Before this report, you'd ship the change and find out about the transitive impact from CI — hours later. Now you know before you write the code.

---

## Scene 4: How It Works Under the Hood (2:15-2:35)

**Visual:** Architecture diagram overlay showing the flow: Developer → Issue → Duo Agent Platform → Blast Radius Agent → Orbit Knowledge Graph → Report. Highlight each component as it's mentioned.

**Narration:**
> Under the hood, Blast Radius Analyzer uses GitLab Orbit's structured code graph. Every file, function, and dependency is a node in the graph with typed edges between them.
>
> The agent uses Orbit's MCP tools — `get_graph_schema` to discover node types, then `query_graph` to recursively traverse dependencies with cycle detection and depth limits.
>
> The reusable blast-radius skill teaches any Duo agent how to perform this analysis. It's open source, MIT licensed, and ready for you to use.

---

## Scene 5: The Impact + Call to Action (2:35-2:55)

**Visual:** Back to the issue. Show the developer adding a comment: "Notifying @backend-team and @billing-team before landing. Risk score: HIGH. Need review from both teams." Merge request is created with the blast radius report linked.

**Narration:**
> This is what changes for developers. Instead of shipping breakage and catching it in CI, you see the blast radius before you commit. You notify the right teams. You plan the rollout. You ship with confidence.
>
> Blast Radius Analyzer is free, open source, and published to the GitLab AI Catalog. Enable it on your project today.
>
> Built for the GitLab Transcend Hackathon. Link in the description.
>
> [End screen: GitHub URL, AI Catalog link, MIT license badge]

---

## Production Notes

- **Record at 1080p, 16:9**
- **No background music** (per Devpost rules: no copyrighted music)
- **Cursor visible** during typing
- **Voiceover can be recorded separately** and synced in post
- **YouTube title:** `Blast Radius Analyzer — Trace Dependencies with GitLab Orbit #GitLabTranscend #GitLabOrbit #AI`
