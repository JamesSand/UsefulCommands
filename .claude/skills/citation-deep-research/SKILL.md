---
name: citation-deep-research
description: >
  Deep literature research by tracing a paper's citation graph. Starting from a
  seed paper, follow forward citations (papers that cite it) using the Semantic
  Scholar Graph API plus web search, VERIFY every reported paper against
  arXiv/OpenReview/PMLR/DBLP, and produce a structured progress report. Use when
  the user wants to survey research progress, trace how a field evolved from a
  seed paper, do a citation-based literature review, or focus on specific venues
  (e.g. NeurIPS/ICML/ICLR) or sub-topics. Triggers: "follow this paper's
  citations", "deep research on X", "what's the progress since this paper",
  "调研一下…现在到什么地步了", "沿着引用往下看".
---

# Citation Deep Research

A reproducible method for tracing the research frontier downstream of a seed
paper. The whole value of this skill is **citation-graph coverage + ruthless
source verification** — most of the cost of a bad literature survey is
hallucinated or mis-attributed papers, so the verification discipline below is
not optional.

## 0. Do NOT scrape Google Scholar

Google Scholar blocks automated access (CAPTCHA + IP bans) and returns unstable
results. Even when the user says "use Google Scholar", **use these sources
instead** and say so:

- **Semantic Scholar Graph API** — the primary citation-graph engine.
- **OpenAlex / arXiv / OpenReview / PMLR / DBLP** — metadata + verification.
- **WebSearch / WebFetch** — for very recent work and reading specific pages.

## 1. Pin down the request (ask only what you can't infer)

Gather, then proceed with sensible defaults rather than over-asking:

1. **Seed paper** — exact title, arXiv ID, or DOI. Disambiguate (many papers
   share titles).
2. **Direction** — *forward* citations (papers citing the seed → "what came
   after / current progress", the usual ask) vs *backward* references
   (what it built on). Default: **forward**.
3. **Scope** — breadth (map all major branches, survey-style) vs depth (track
   the few most important SOTA lines to the latest). Default: **breadth first,
   then depth on the strongest lines**.
4. **Focus filters** — specific venues (e.g. the big three: NeurIPS, ICML,
   ICLR), sub-topic, year range. Honor these aggressively when filtering.

If a seed PDF is local and unreadable, install a text extractor on the fly:
`python3 -m pip install --quiet --user pymupdf` then extract with `fitz`.

## 2. Pull the citation graph (Semantic Scholar)

Fetch citing papers via WebFetch on the Graph API. Template:

```
https://api.semanticscholar.org/graph/v1/paper/arXiv:<ID>/citations?fields=title,year,venue,publicationVenue,citationCount,abstract,externalIds,authors&limit=100&offset=0
```

- Replace `arXiv:<ID>` with the seed (e.g. `arXiv:2212.13345`). For a DOI use
  `DOI:<doi>`; for a Semantic Scholar ID use it directly.
- **Paginate**: re-fetch with `offset=100`, `offset=200`, … until coverage is
  enough (3–4 pages of 100 usually covers the substantive work; the long tail is
  low-quality application papers).
- If it **rate-limits (HTTP 429)**: wait and retry, or reduce `fields`. A
  Semantic Scholar API key (env `S2_API_KEY`, header `x-api-key`) raises limits
  if available.
- `citationCount` is a *relative* impact signal only — it undercounts very
  recent venue acceptances. Use it to rank, not to judge.

Use `citationCount` + `year` to prioritize which citing papers to read.

## 3. Targeted web search to fill gaps

The citation graph misses the newest and the venue-specific. Run WebSearch for:

- `"<topic>" <venue> <year>` (e.g. `"Forward-Forward" ICLR 2024`)
- `"<seed concept>" <sub-topic>` (e.g. `forward-forward catastrophic forgetting`)
- `<topic> OpenReview` / `<topic> site:openreview.net`

## 4. VERIFY everything (the part that matters)

For every paper you intend to report:

- Confirm **title + venue + year** on a real landing page (arXiv abstract page,
  OpenReview forum, PMLR proceedings, DBLP, or publisher DOI).
- **Never fabricate or guess** titles, authors, venues, or IDs.
- Watch for **DB artifacts**: Semantic Scholar sometimes returns implausible
  future-dated arXiv IDs or phantom entries. If an ID looks wrong or you can't
  open it, **do not report it in the body** — quarantine it in the verification
  notes.
- Prefer **fewer verified papers over many unverified ones.**

Track three tiers explicitly: ✅ opened & confirmed · ⚠️ venue per Semantic
Scholar but not re-opened (likely correct, flag for a 30-sec DBLP/OpenReview
check) · ❌ could not verify / suspect (exclude from body).

## 5. Parallelize with a background agent (optional but recommended)

For a wide fan-out, launch a **background `general-purpose` agent** to gather
candidates while you do other work (e.g. reading the seed paper or writing
diagrams), then **verify its key claims yourself** before finalizing — don't
trust a sub-agent's citations blindly. Give the agent: the seed ID, the exact
Semantic Scholar URL template above, the focus filters, the verification rules,
and the required output structure. Spawn with `run_in_background: true`; you'll
be notified on completion.

## 6. Deliverable

Write a single markdown file. Follow the project's file-naming convention if one
exists (e.g. zero-padded number prefix + English kebab-case name like
`002-<topic>.md`). Structure:

```markdown
# <Topic> 研究进展调研（侧重 <focus>）

> 种子论文 · 调研方法（S2 引用图谱 N 页 + WebSearch + 逐篇核实）· 引用数来源 · 调研日期

## TL;DR            # 4-6 bullet honest bottom-line, including what is NOT true
## 一、整体格局      # momentum, consensus limitations, where the field's center of gravity is
## 二、<重点维度>    # e.g. a table organized by venue (NeurIPS/ICML/ICLR) if venues were the focus
## 三、<焦点专题>    # deep synthesis of the user's specific angle: what's tried / what works / open problems
## 四、按主题分类的完整列表   # grouped by theme; each: **title** — authors, venue+year, 1-2 sentence what+result, URL, (~cites)
## 五、信源可信度 & 注意事项  # the ✅/⚠️/❌ tiers from step 4 — REQUIRED, never omit
## 六、判断 + 下一步可追什么   # honest take + 2-3 candidate next seed papers to go deeper
```

Each paper entry must carry: **title**, authors (first-author et al. ok),
**venue + year**, one or two sentences on what it does and its result, a **URL**,
and citation count if known. Group by theme (e.g. variants/objectives, scaling,
architecture, theory, hardware, applications, and the user's focus topic).

## 7. Honesty rules

- Lead with the bottom line even when it contradicts the framing of the request
  (e.g. "X is not actually the story; Y is"). Don't pad a thin result.
- Distinguish the strict topic (e.g. the seed method itself) from the broader
  framing (e.g. the general paradigm) when the evidence splits between them.
- The verification-notes section is mandatory — the user needs to know what to
  trust.

## Pitfalls cheat-sheet

- Google Scholar → blocked; use Semantic Scholar.
- Semantic Scholar 429 → retry / fewer fields / API key.
- Future-dated or odd arXiv IDs from the API → likely phantom; verify or drop.
- Sub-agent output → verify before citing.
- Local PDF won't open → `pip install --user pymupdf`, read with `fitz`.
