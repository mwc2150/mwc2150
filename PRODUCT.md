# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (GitHub profile README: GitHub-flavored Markdown plus the HTML subset GitHub allows; no CSS or scripts)

## Users

Recruiters and hiring managers (pharma and healthcare analytics, private equity, applied AI) skimming for who Michael is, what Michael has built and how to get in touch; and technical peers who click through to repos. Weighted equally.

## Product Purpose

Michael Chen's GitHub profile page: identity, selected projects, toolkit and contact, in one scroll.

## Capabilities and Constraints

- Project picker SVGs are built by `scripts/build_assets.py` ("Pick an emoji, any emoji ;)" in EB Garamond Italic embedded as subset WOFF2; Noto Emoji bobbing via CSS animation inside each SVG, stopped under `prefers-reduced-motion`). GitHub strips `target="_blank"`, so links can't be forced into a new tab. Body copy stays real text so it reads at phone width.
- Light/dark variants are switched with `<picture>` + `prefers-color-scheme`, which GitHub maps to the viewer's GitHub theme.
- A standalone portfolio site is a possible later step, not yet decided.

## Brand Commitments

- Hero GIF: young Goku on the Flying Nimbus (`assets/nimbus.gif`, from the user's chosen Pinterest pin). The page itself does not borrow the GIF's blue/gold; the picker uses GitHub's neutral text colors, and the floating emoji echo the Nimbus.
- The GIF sits beside the About text (floated right), not as a full-width banner; no separate name/tagline card.
- The only title is the "Hello, I'm Michael!" greeting (EB Garamond, neutral ink); no other section titles. Warm, first-person intro below it.
- Projects are a mystery pick: a muted italic "Pick an emoji, any emoji ;)" (a nod to "pick a card, any card", with the wink here rather than in the greeting) over four bare floating emoji (💊 💼 📡 🧠), each linked to its repo, with no names, subtitles or boxes. The owner found the old name-plus-blurb buttons too AI-looking. Alt and `title` name each project, so hovering shows the name as the browser's native tooltip (the only hover effect a README allows; none on phones). No spoiler list.
- The toolkit frames the picker as two bands of icons, ungrouped, one above drifting left and one below drifting right (one SVG each with the icons embedded, built from `TOOLS` in `scripts/build_assets.py`; still under reduced motion). Tools lose individual hover names; each band's alt text lists its tools.
- Education and Rexi Self-Care (co-founded) are woven into the intro prose, not listed as separate title lines.

## Evidence on Hand

Project facts come from each repo's own README: PharmAgentics, Qual2Cast, AI Pulse, optimized-llm-planning-memory. No metrics, employers or roles beyond those are stated.
