---
name: add-section
description: Add a new HTML section to the Path of Resilience website, matching the existing navy/gold design system. Pass a description of the section as args (e.g. "FAQ", "testimonials", "about Travis").
---

Add a new section to the appropriate HTML file in this repository.

Design system to match:
- Background: `var(--navy)` (#0B1628) or `var(--navy-mid)` (#0F2040)
- Accent color: `var(--gold)` (#C9A84C) / `var(--gold-bright)` (#E2BE6A)
- Text: `var(--off-white)` (#F5F0E8), muted text `var(--text-muted)`
- Font: Inter (already loaded via Google Fonts)
- Cards use `var(--gold-card)` background with `var(--gold-border)` border
- Animations: GSAP ScrollTrigger (already loaded) — fade-up on scroll preferred

Section to add: $ARGUMENTS

Steps:
1. Read the target HTML file to understand the existing structure and where the new section fits.
2. Write the HTML using the design tokens above — no inline hex values, use CSS variables.
3. Add matching CSS within the existing `<style>` block.
4. Add a GSAP ScrollTrigger animation consistent with the page's existing animation patterns.
5. If the section has a nav anchor, add it to the `<nav>` links.
