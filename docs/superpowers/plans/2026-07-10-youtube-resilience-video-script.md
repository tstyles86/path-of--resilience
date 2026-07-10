# YouTube Video Script: "How I Rewrote My Story After Losing My Leg"

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a complete, ready-to-record script for a 10–12 minute YouTube video with 3 Shorts scripts cut from it.

**Architecture:** Four narrative sections written as spoken monologue. Story-first: open raw, let the framework emerge through the story, name it explicitly in Section 3, close with a direct viewer challenge. No generic motivational language — every line anchored in Travis's specific experience.

**Spec:** `docs/superpowers/specs/2026-07-10-youtube-resilience-video-design.md`

**Output:** `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

---

## Speaking Pace Reference

~140 words/minute (conversational YouTube tone)

| Section | Time | Target Word Count |
|---|---|---|
| Section 1 — The Raw Moment | 0:00–1:30 | 180–210 words |
| Section 2 — The Shift | 1:30–4:30 | 380–420 words |
| Section 3 — Writing the New Story | 4:30–8:00 | 460–520 words |
| Section 4 — The Challenge | 8:00–end | 240–280 words |
| **Total** | **10–12 min** | **1,260–1,430 words** |

---

## File Structure

- **Create:** `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`
  - The complete script, all four sections + Shorts variants
- **Reference:** `docs/superpowers/specs/2026-07-10-youtube-resilience-video-design.md`
  - Design decisions, tone rules, section goals — consult before each task

---

## Task 1: Script Setup + Section 1 — The Raw Moment

**Files:**
- Create: `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

**Goal:** Hook the viewer emotionally in the first 30 seconds. Drop them into the specific moment the old story broke — not surgery, not the hospital, but the instant Travis looked down and knew the person he was before wasn't coming back. No intro, no channel branding. Just truth.

**Tone check:** First-person, present-tense feeling even if past-tense grammar. Specific over general. The viewer should feel recognition before they know why.

- [ ] **Step 1: Create the script file with header**

Create `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md` with this skeleton:

```markdown
# Script: How I Rewrote My Story After Losing My Leg

**Title:** How I Rewrote My Story After Losing My Leg
**Format:** Long-form YouTube (10–12 min) + 3 Shorts
**Status:** DRAFT

---

## [SECTION 1 — THE RAW MOMENT] 0:00–1:30
*(Target: 180–210 words | No intro. Camera on Travis. Truth first.)*

[SCRIPT HERE]

---

## [SECTION 2 — THE SHIFT] 1:30–4:30
*(Target: 380–420 words | Framework emerges through story, not lecture)*

[SCRIPT HERE]

---

## [SECTION 3 — WRITING THE NEW STORY] 4:30–8:00
*(Target: 460–520 words | Name the framework. Proof of concept.)*

[SCRIPT HERE]

---

## [SECTION 4 — THE CHALLENGE] 8:00–end
*(Target: 240–280 words | Direct address. Movement ending. One concrete next step.)*

[SCRIPT HERE]

---

## SHORTS SCRIPTS

### Short 1 — The Raw Moment
*(Hook: "The day I stopped trying to be who I was before...")*

[SCRIPT HERE]

### Short 2 — The Shift
*(Hook: "Your support group is your superpower — here's why")*

[SCRIPT HERE]

### Short 3 — The Challenge
*(Hook: "Nobody tells you THIS about starting over after a major loss")*

[SCRIPT HERE]
```

- [ ] **Step 2: Write Section 1 — The Raw Moment**

Replace `[SCRIPT HERE]` under Section 1 with a 180–210 word spoken monologue draft. The script should:

- Open mid-moment — a specific memory, not a setup
- Use short sentences. Pauses are okay. This is meant to be spoken.
- Land one emotional truth by the end of the section that makes the viewer think "I know that feeling"
- NOT include channel intro, "hey guys", subscribe asks, or any preamble
- End with a line that creates a bridge into the shift — something that signals: *but something changed*

Example opening rhythm (not the actual words — Travis fills those in):
> "There was this one moment. I don't talk about it a lot. [specific detail]. And I just... sat there. Because I realized [emotional truth]. That was the moment I knew the person I used to be wasn't coming back."

- [ ] **Step 3: Word count check**

Count the words in Section 1. If under 180: add one more specific detail or beat. If over 210: trim adjectives and compound sentences first.

- [ ] **Step 4: Read it aloud**

Read Section 1 out loud at a natural pace. Time it. Should land between 1:10–1:30. Adjust if needed.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md
git commit -m "script: add Section 1 raw moment draft"
```

---

## Task 2: Section 2 — The Shift

**Files:**
- Modify: `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

**Goal:** Show the mindset reframe arriving gradually through two specific sources — the support group and the things Travis loves. The framework ("lean into your people + your passions") must land through story, never as a list or lesson. The viewer should feel the formula before it's named.

**Structure within this section:**
1. Brief bridge from Section 1 — the moment something started to change
2. Support group: name specific people, name the specific moment(s) they showed up
3. The things you love: what Travis returned to, what it reminded him of — not who he was, who he *is*
4. Close with a line that hints at the formula without stating it outright

- [ ] **Step 1: Write the bridge sentence**

One or two sentences that connect Section 1's ending to this section's beginning. Should feel like movement — something shifted, something or someone appeared.

- [ ] **Step 2: Write the support group beat (180–210 words)**

Write the support group portion of Section 2. Requirements:
- Name at least one real person by first name or relationship ("my brother", "my coach", "my friend Marcus")
- Describe one specific moment — not "they were there for me" but what they actually did or said
- Avoid "I'm so grateful" and other gratitude clichés — show it through the moment
- The emotional payoff: the viewer should feel what it's like to be held up by someone who refuses to let you disappear

- [ ] **Step 3: Write the passions beat (180–210 words)**

Write the "things you love" portion of Section 2. Requirements:
- Name the specific thing(s) Travis returned to
- Describe the first time going back to it — the resistance, the awkwardness, or the surprising ease
- The emotional payoff: "this is still me" — identity reclaimed through action, not declaration
- Ends with a line that quietly completes the two-part formula: *you have people, and you have what you love*

- [ ] **Step 4: Combine and read aloud**

Paste bridge + support group beat + passions beat together. Read aloud. Time it — target 3:00 (range: 2:45–3:15). Check that the transition between beats feels natural, not like topic changes.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md
git commit -m "script: add Section 2 the shift draft"
```

---

## Task 3: Section 3 — Writing the New Story

**Files:**
- Modify: `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

**Goal:** Show what rebuilding actually looks like. This is where "resilience mindset shift" gets named explicitly for the first time. Not a how-to — Travis's journey as the proof of concept. End with a specific first-step moment, not a finish line.

**This section names the framework directly.** Everything before this was the felt sense of it. Here it gets a name. That name should feel earned, not imported.

- [ ] **Step 1: Write the "what rebuilding looks like" segment (200–240 words)**

Write the practical-but-personal first half of Section 3. Requirements:
- Describe a specific period or phase of rebuilding — not a summary, a scene
- Include at least one moment of doubt, resistance, or failure *within* the rebuilding — it shouldn't feel easy
- No generic "one day at a time" or "just keep going" language
- The viewer should think: "that's what it actually looks like"

- [ ] **Step 2: Name the framework (60–80 words)**

Write the moment where Travis explicitly names what he's been describing. Requirements:
- The phrase "resilience mindset shift" should appear here or very close to it
- Frame it as something discovered, not something taught — "I didn't have a name for it at the time, but..."
- Keep it conversational — one or two sentences max before moving on

- [ ] **Step 3: Write the "first step, not finish line" closing beat (200–220 words)**

Write the closing beat of Section 3. Requirements:
- Name the specific moment Travis *felt* the new story beginning — a small, concrete thing
- Not the peak of the journey — the first step of it
- Close with a bridge to Section 4: make the viewer feel like they're being handed something

- [ ] **Step 4: Combine and read aloud**

Read Section 3 in full. Time it — target 3:30 (range: 3:10–3:45). Check that naming the framework feels natural, not like a gear-shift.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md
git commit -m "script: add Section 3 writing the new story draft"
```

---

## Task 4: Section 4 — The Challenge

**Files:**
- Modify: `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

**Goal:** Direct address to camera. This is not a wrap-up — it's the beginning of a movement. Leave the viewer with one concrete next step. The comments section becomes the community thread. End the video feeling like something just started, not finished.

**Tone shift:** This is the only section where Travis speaks *to* the viewer rather than *for* them. More direct. Shorter sentences. Eye contact energy.

- [ ] **Step 1: Write the "I see what you're carrying" opening (60–80 words)**

Open Section 4 by naming what the viewer might be sitting with right now. Not presumptuous — more like: "If you're watching this, chances are you're dealing with something." Specific enough to land, general enough to be universal. Establish that Travis is talking *to* them now, not about himself.

- [ ] **Step 2: Write the challenge (80–100 words)**

Deliver the two-question challenge:
- "Who in your life is your support group?" — make it land as a real question, not a rhetorical device
- "What's the thing you love that you've been putting off?" — same
- Then: "Start there. That's where your new story begins."
- These words (or very close to them) should appear verbatim — they're the core of the Short

- [ ] **Step 3: Write the CTA (80–100 words)**

Write the comments CTA. Requirements:
- Ask the viewer to share *one thing* — not a vague "comment below"
- Specific prompt: something like "Tell me one person in your corner, or one thing you love that you're going back to"
- Frame the comments as the community — "I read every one" or similar
- Light subscribe ask if natural — never forced
- End the video feeling open, not closed. Movement, not conclusion.

- [ ] **Step 4: Combine and read aloud**

Read Section 4 in full. Time it — target 2:00 (range: 1:45–2:15). The energy should feel different from Sections 1–3 — more direct, more alive. If it sounds like the other sections, punch it up.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md
git commit -m "script: add Section 4 the challenge draft"
```

---

## Task 5: Shorts Scripts

**Files:**
- Modify: `docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md`

**Goal:** Write three standalone Short scripts (45–60 seconds each) cut from the long-form content. Each Short opens with its hook line and is self-contained — the viewer should not need to have watched the long-form to understand it.

**Shorts pacing:** ~120 words/minute (faster than long-form). Target: 54–72 words per Short.

- [ ] **Step 1: Write Short 1 — The Raw Moment**

Hook: *"The day I stopped trying to be who I was before..."*

Extract or adapt the strongest 54–72 words from Section 1. The Short must:
- Open with the hook line verbatim (or a direct variant)
- Land one emotional truth
- End with a line that leaves the viewer wanting more (drives them to the long-form or to comment)
- No CTA required — the hook and ending do the work

- [ ] **Step 2: Write Short 2 — The Shift**

Hook: *"Your support group is your superpower — here's why"*

Extract or adapt the strongest 54–72 words from Section 2's support group beat. The Short must:
- Open with the hook line
- Include the specific person/moment that best illustrates the point
- End on the emotional payoff line

- [ ] **Step 3: Write Short 3 — The Challenge**

Hook: *"Nobody tells you THIS about starting over after a major loss"*

Extract or adapt Section 4's challenge beat. The Short must:
- Open with the hook line
- Deliver both questions ("who is your support group" + "what do you love")
- End with: "Start there. That's where your new story begins."
- 54–72 words — tight, punchy, no filler

- [ ] **Step 4: Read all three Shorts aloud**

Each Short should feel complete and punchy at under 60 seconds. If any runs over: cut adjectives and compound sentences first.

- [ ] **Step 5: Final commit**

```bash
git add docs/superpowers/scripts/2026-07-10-youtube-resilience-video-script.md
git commit -m "script: add Shorts scripts — complete draft"
git push -u origin claude/superpowers-repo-GCGOM
```

---

## Self-Review Checklist

After completing all tasks, verify:

- [ ] Section 1 contains no channel intro, subscribe ask, or preamble
- [ ] Section 2 names at least one specific person and one specific moment
- [ ] Section 3 contains the phrase "resilience mindset shift" (or close variant)
- [ ] Section 4 contains the two challenge questions and "Start there. That's where your new story begins."
- [ ] No section contains: "one day at a time", "just keep going", "I'm so grateful", or similar clichés
- [ ] Total word count: 1,260–1,430 words
- [ ] All three Shorts open with their designated hook line
- [ ] All three Shorts are 54–72 words
- [ ] B-roll notes added as inline `[B-ROLL: ...]` markers where footage will be needed
