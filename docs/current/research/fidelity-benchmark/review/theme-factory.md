# Requirement review: theme-factory

Source: sources/theme-factory/SKILL.md
Reviewed by: ChatGPT (GPT-6, AI reviewer), as stated in its review relayed by the repository owner
Date: 2026-11-20
Approval: AI-reviewed baseline
Candidate status: AI-drafted, AI-reviewed three times (drafting session; external AI
reviews 2026-11-20, revisions 2 and 3). Not human-approved: freezing needs the human
reviewer's name and date.

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`TF-14`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

Ask of each line: if a converted skill lost or weakened this, would the skill
be wrong? If not, drop it.

- [x] TF-1 | ordering | Show the theme showcase (`theme-showcase.pdf`) before asking for a choice. | "Display the `theme-showcase.pdf` file to allow users to see all available themes visually."
- [x] TF-2 | prohibition | Never modify the showcase file; only show it. | "Do not make any modifications to it; simply show the file for viewing."
- [x] TF-3 | ordering | The sequence is showcase, then ask which theme to apply, then explicit confirmation of the choice, then apply; no step is skipped or reordered. | "Display the `theme-showcase.pdf` file ... Ask which theme to apply to the deck ... Get explicit confirmation about the chosen theme ... Once a theme has been chosen, apply the selected theme's colors and fonts to the deck/artifact"
- [x] TF-4 | authority | Apply a theme only after the user explicitly confirms the choice. | "Get explicit confirmation about the chosen theme"
- [x] TF-5 | ordering | After a theme is chosen, read its file from `themes/` before applying it. | "Read the corresponding theme file from the `themes/` directory"
- [x] TF-6 | obligation | Apply the theme's colors and fonts consistently throughout the artifact. | "Apply the specified colors and fonts consistently throughout the deck"
- [x] TF-7 | obligation | Ensure proper contrast and readability. | "Ensure proper contrast and readability"
- [x] TF-8 | obligation | Keep the theme's visual identity across all slides. | "Maintain the theme's visual identity across all slides"
- [x] TF-9 | exception | When none of the existing themes fits, create a custom theme from the provided inputs. | "To handle cases where none of the existing themes work for an artifact, create a custom theme."
- [x] TF-10 | obligation | A custom theme uses any provided description to choose colors and fonts. | "Use any basic description provided to choose appropriate colors/fonts."
- [x] TF-11 | obligation | Name a custom theme for what its font and color combination represents. | "Give the theme a similar name describing what the font/color combinations represent."
- [x] TF-12 | ordering | Show a custom theme for review and verification before applying it. | "After generating the theme, show it for review and verification."
- [x] TF-13 | obligation | The ten preset themes are Ocean Depths, Sunset Boulevard, Forest Canopy, Modern Minimalist, Golden Hour, Arctic Frost, Desert Rose, Tech Innovation, Botanical Garden and Midnight Galaxy. | "The following 10 themes are available"

## Revision log

- TF-3 restated as the full sequence (showcase, ask, explicit confirmation, apply); it was labelled ordering but only said to ask (external AI review).
- Revision 3: TF-3's quote now covers all four steps of the sequence (multi-span quote, each span verified) instead of only the ask (external AI review).
- Approval: the owner relayed an AI reviewer's approval of revision 3 as an AI-reviewed baseline, explicitly not human-approved ground truth. The reviewer identity is as the review states it; it was not independently verified.
