# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (GitHub profile README: GitHub-flavored Markdown plus the HTML subset GitHub allows; no CSS or scripts)

## Users

Recruiters and hiring managers (pharma and healthcare analytics, private equity, applied AI) skimming for who Michael is, what Michael has built and how to get in touch; and technical peers who click through to repos. Weighted equally.

## Product Purpose

Michael Chen's GitHub profile page: identity, selected projects, toolkit and contact, in one scroll.

## Capabilities and Constraints

- Project buttons are SVGs built by `scripts/build_assets.py` (EB Garamond names embedded as subset WOFF2, system-font blurbs, Noto Emoji). GitHub strips `target="_blank"`, so links can't be forced into a new tab. Body copy stays real text so it reads at phone width.
- Light/dark variants are switched with `<picture>` + `prefers-color-scheme`, which GitHub maps to the viewer's GitHub theme.
- A standalone portfolio site is a possible later step, not yet decided.

## Brand Commitments

- Hero GIF: young Goku on the Flying Nimbus (`assets/nimbus.gif`, from the user's chosen Pinterest pin). The page itself does not borrow the GIF's blue/gold; buttons use GitHub's neutral surface colors.
- The GIF sits beside the About text (floated right), not as a full-width banner; no separate name/tagline card.
- The only title is the "Hello, I'm Michael" greeting (EB Garamond, neutral ink); no other section titles. Warm, first-person intro below it.
- Projects are link buttons (original emoji 💊 💼 📡 🧠, name, one-line blurb), two per row, stacking on phones.
- The toolkit is the original single centered strip of icons, ungrouped.
- Education and Rexi Self-Care (co-founded) are woven into the intro prose, not listed as separate title lines.

## Evidence on Hand

Project facts come from each repo's own README: PharmAgentics, Qual2Cast, AI Pulse, optimized-llm-planning-memory. No metrics, employers or roles beyond those are stated.
