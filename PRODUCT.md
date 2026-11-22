# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (GitHub profile README: GitHub-flavored Markdown plus the HTML subset GitHub allows; no CSS or scripts)

## Users

Recruiters and hiring managers (pharma and healthcare analytics, private equity, applied AI) skimming for who Michael is, what he has built and how to reach him; and technical peers who click through to repos. Weighted equally.

## Product Purpose

Michael Chen's GitHub profile page: identity, selected projects, toolkit and contact, in one scroll.

## Capabilities and Constraints

- Display type lives in SVGs built by `scripts/build_assets.py` (Fraunces embedded as subset WOFF2). Body copy stays real text so it reads at phone width.
- Light/dark variants are switched with `<picture>` + `prefers-color-scheme`, which GitHub maps to the viewer's GitHub theme.
- A standalone portfolio site is a possible later step, not yet decided.

## Brand Commitments

- Hero GIF: young Goku on the Flying Nimbus (`assets/nimbus.gif`, from the user's chosen Pinterest pin). Its palette (sky blue, Nimbus gold) sets the page's colors.
- The toolkit keeps every listed tool, grouped by area.

## Evidence on Hand

Project facts come from each repo's own README: PharmAgentics, Qual2Cast, AI Pulse, optimized-llm-planning-memory. No metrics, employers or roles beyond those are stated.
