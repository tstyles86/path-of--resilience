---
name: deep-research
description: |
  Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.
  When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the
  question is specific enough to research directly — if underspecified (e.g., "what car to buy" without
  budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args,
  weaving the answers in.
triggers:
  - "deep research"
  - "research report"
  - "fact-check"
  - "multi-source research"
  - "cited report"
---

# Deep Research

Run the "deep-research" workflow.

Deep research harness — fan-out web searches, fetch sources, adversarially verify claims, synthesize a cited report.

When the user wants a deep, multi-source, fact-checked research report on any topic. BEFORE invoking, check if the question is specific enough to research directly — if underspecified (e.g., "what car to buy" without budget/use-case/region), ask 2-3 clarifying questions to narrow scope. Then pass the refined question as args, weaving the answers in.

## Phases

- **Scope:** Decompose question (from args) into 5 search angles
- **Search:** 5 parallel WebSearch agents, one per angle
- **Fetch:** URL-dedup, fetch top 15 sources, extract falsifiable claims
- **Verify:** 3-vote adversarial verification per claim (need 2/3 refutes to kill)
- **Synthesize:** Merge semantic dupes, rank by confidence, cite sources

## Invocation

```
Workflow({ name: "deep-research", args: "<your research question>" })
```
