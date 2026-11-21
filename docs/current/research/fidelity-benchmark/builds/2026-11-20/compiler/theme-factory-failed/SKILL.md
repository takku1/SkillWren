---
name: theme-factory
description: Style an existing artifact (slide deck, doc, report, HTML landing page) with one of 10 preset font and color themes, or generate a custom theme when none fits. Use when asked to theme, restyle, or apply colors and fonts to a deck or document. Not for building the artifact's content.
---

# Theme factory (SkillWren logic)

The procedure is the `logic` block below. Execute it exactly; it is the only procedure.

```contract
always:
  ensure proper contrast and readability of the themed artifact
  maintain the theme's visual identity across all slides
never:
  modify theme-showcase.pdf
inputs:
  artifact, description
order:
  verify#showcase before ask user to choose which theme to apply
  ask user to choose which theme to apply before write#themed
  ask user to choose which theme to apply before write#customthemed
  ask user to review and verify the custom theme before write#customthemed
```

```logic
style:
  read theme-showcase.pdf as showcase
  show showcase
  exec readonly showcase display check from checks as showcasecheck
  verify #showcase the theme showcase was shown unmodified from showcasecheck
    otherwise:
      show showcase
  ask user to choose which theme to apply
  require confirmation

  if none of the existing themes work for the artifact:
    generate custom theme from description as theme
    show theme
    ask user to review and verify the custom theme
    require confirmation
    apply theme application with theme as themed_artifact
    write #customthemed themed_artifact with artifact
    return themed_artifact as styled_artifact
  else:
    read the chosen theme file from themes as theme
    exec theme file check from checks as themecheck
    verify #themefile the chosen theme file was read from themes from themecheck
      otherwise:
        apply theme gap record with artifact as gap_note
        return gap_note as styled_artifact
    apply theme application with theme as themed_artifact
    write #themed themed_artifact with artifact
    return themed_artifact as styled_artifact
```

## Context

This skill offers a curated collection of professional font and color themes. Each has a cohesive hex color palette, complementary header and body font pairings, and a distinct visual identity suited to different contexts and audiences. Once chosen, a theme can be applied to any artifact (slides, docs, reports, HTML landing pages). The main purpose is consistent, professional styling of presentation slide decks.

## Themes available

All ten are showcased in `theme-showcase.pdf`. Full specifications (hex palette, header/body fonts, visual identity) live one file per theme in the `themes/` directory.

1. **Ocean Depths** - Professional and calming maritime theme
2. **Sunset Boulevard** - Warm and vibrant sunset colors
3. **Forest Canopy** - Natural and grounded earth tones
4. **Modern Minimalist** - Clean and contemporary grayscale
5. **Golden Hour** - Rich and warm autumnal palette
6. **Arctic Frost** - Cool and crisp winter-inspired theme
7. **Desert Rose** - Soft and sophisticated dusty tones
8. **Tech Innovation** - Bold and modern tech aesthetic
9. **Botanical Garden** - Fresh and organic garden colors
10. **Midnight Galaxy** - Dramatic and cosmic deep tones

## Step meanings

- **show showcase**: display `theme-showcase.pdf` for viewing only, so the user sees all themes visually. Never modify it.
- **custom theme** (the `generate` step): create a theme in the same form as the presets (hex palette, header and body fonts). Give it a descriptive name, like the presets, that reflects what the font/color combination represents. Use any basic description provided to choose appropriate colors and fonts.
- **theme application**: apply the specified colors and fonts consistently throughout the deck or artifact, ensure proper contrast and readability, and maintain the theme's visual identity across all slides.
- **theme gap record**: produce a result stating that the chosen theme file could not be confirmed as read, so the theme was not applied.
