# Requirement review: theme-factory

Source: sources/theme-factory/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>

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
- [x] TF-3 | ordering | Ask the user which theme to apply. | "Ask which theme to apply to the deck"
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
