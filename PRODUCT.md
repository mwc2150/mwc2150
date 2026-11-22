# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (GitHub profile README: GitHub-flavored Markdown plus the HTML subset GitHub allows; no CSS or scripts)

## Users

Recruiters and hiring managers (pharma and healthcare analytics, private equity, applied AI) skimming for who Michael is, what Michael has built and how to get in touch; and technical peers who click through to repos. Weighted equally.

## Product Purpose

Michael Chen's GitHub profile page: identity, selected projects, toolkit and contact, in one scroll.

## Capabilities and Constraints

- Display type lives in SVGs built by `scripts/build_assets.py` (EB Garamond embedded as subset WOFF2; the user asked for Georgia or EB Garamond). Body copy stays real text so it reads at phone width.
- Light/dark variants are switched with `<picture>` + `prefers-color-scheme`, which GitHub maps to the viewer's GitHub theme.
- A standalone portfolio site is a possible later step, not yet decided.

## Brand Commitments

- Hero GIF: young Goku on the Flying Nimbus (`assets/nimbus.gif`, from the user's chosen Pinterest pin). Its palette (sky blue, Nimbus gold) sets the page's colors.
- The GIF sits beside the About text (floated right), not as a full-width banner; no separate name/tagline card.
- Section titles are plain serif type with no ornament. The page opens with "Hello, I'm Michael" and a warm, first-person intro.
- Selected work is a 2x2 grid of short project boxes (title and one sentence, no tool icons).
- The toolkit is the original single centered strip of icons, ungrouped.
- Education and Rexi Self-Care (co-founded) are woven into the intro prose, not listed as separate title lines.

## Evidence on Hand

Project facts come from each repo's own README: PharmAgentics, Qual2Cast, AI Pulse, optimized-llm-planning-memory. No metrics, employers or roles beyond those are stated.
