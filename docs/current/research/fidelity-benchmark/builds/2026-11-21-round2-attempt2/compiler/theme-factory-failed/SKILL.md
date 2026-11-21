---
name: theme-factory
description: Style an existing artifact (slide deck, doc, report, HTML landing page) with a professional font and color theme. Pick from 10 preset themes shown in a showcase PDF, or generate a custom theme when none fit. Use when asked to theme, restyle, or apply colors and fonts to a deck or document. Not for building the artifact's content.
---

# Theme factory (SkillWren logic)

The procedure is the `logic` block below. Execute it exactly; it is the only procedure.

```contract
always:
  apply the specified colors and fonts consistently throughout the artifact
  maintain the theme's visual identity across all slides
never:
  modify theme_showcase
inputs:
  artifact, description, theme_showcase
order:
  verify#showcase before ask user
  verify#theme before apply theme colors and fonts
  verify#theme before write#styled
```

```logic
style:
  show theme_showcase
  exec readonly showcase display check from checks as showcase
  verify #showcase theme_showcase was displayed for viewing from showcase
    otherwise:
      return artifact as styled_artifact
  if none of the existing themes work for artifact:
    generate custom theme from description as custom_theme
    exec readonly custom theme check from checks as custom_check
    verify #custom custom_theme has a hex palette and font pairings from custom_check
      otherwise:
        return artifact as styled_artifact
    show custom_theme
    ask user to review and verify the custom theme
    require confirmation
      otherwise:
        return artifact as styled_artifact
    read theme file from custom_theme as theme
  else:
    ask user to choose the theme to apply to artifact
    require confirmation
      otherwise:
        return artifact as styled_artifact
    read theme file from themes as theme
  exec readonly theme load check from checks as themeload
  verify #theme theme has hex palette and font pairings from themeload
    otherwise:
      return artifact as styled_artifact
  apply theme colors and fonts with theme as styled
  exec contrast check from checks as contrast
  verify #contrast styled has proper contrast and readability from contrast
    otherwise:
      apply contrast fix with styled as styled
      exec contrast check from checks as contrast
      retry
  write #styled styled with artifact
  return styled as styled_artifact
```

## Context

This skill provides a curated collection of professional font and color themes. Once a theme is chosen it can be applied to any artifact (slides, docs, reports, HTML landing pages).

Its main purpose is to apply consistent, professional styling to presentation slide decks. Each theme includes a cohesive color palette with hex codes, complementary font pairings for headers and body text, and a distinct visual identity suitable for different contexts and audiences.

## Themes available

All 10 are showcased in `theme-showcase.pdf` (the `theme_showcase` input):

1. **Ocean Depths** - professional and calming maritime
2. **Sunset Boulevard** - warm and vibrant sunset colors
3. **Forest Canopy** - natural and grounded earth tones
4. **Modern Minimalist** - clean and contemporary grayscale
5. **Golden Hour** - rich and warm autumnal palette
6. **Arctic Frost** - cool and crisp winter-inspired
7. **Desert Rose** - soft and sophisticated dusty tones
8. **Tech Innovation** - bold and modern tech aesthetic
9. **Botanical Garden** - fresh and organic garden colors
10. **Midnight Galaxy** - dramatic and cosmic deep tones

Each theme is defined in the `themes/` directory with its full specification: hex color palette, header and body font pairings, and visual identity.

## Step meanings

- **show theme_showcase**: display `theme-showcase.pdf` so the user can see all themes visually; view only, never edit it.
- **read theme file**: load the chosen theme's specification from the `themes/` directory (for a custom theme, the reviewed custom specification).
- **custom theme**: generate a new theme similar in form to the presets (hex palette plus font pairings), using any basic description provided to choose colors and fonts. Give it a similar-style name describing what the font/color combination represents. Show it for review and verification before applying.
- **theme colors and fonts**: apply the colors and fonts specified in the theme binding to the artifact, consistently throughout the deck or artifact.
- **contrast fix**: adjust colors so text keeps proper contrast and readability while preserving the theme's visual identity.

## Taste

"Professional", "cohesive", "complementary", "appropriate" and "adequate contrast" are subjective judgments; use design taste and the user's description rather than a fixed rubric.
