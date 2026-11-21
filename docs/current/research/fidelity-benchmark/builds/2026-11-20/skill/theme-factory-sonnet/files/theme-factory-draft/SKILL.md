---
name: theme-factory
description: Style an artifact (slides, docs, reports, HTML pages) with one of 10 preset color/font themes or a custom theme generated on the fly. Use when asked to theme, style or restyle an artifact.
---

# Theme Factory

```contract
inputs:
  artifact
order:
  show showcase before ask user for the theme choice
  ask user to confirm the theme before apply theme to artifact
```

```logic
theme-factory:
  require artifact exists
    otherwise:
      abort with "Name the slide deck or artifact to style."

  read showcase from theme_assets as showcase
    otherwise:
      abort with "theme-showcase.pdf is missing; cannot show the themes."
  show showcase

  label choosing:
  ask user for the theme choice (a preset name, or custom)

  if the choice is custom:
    ask user for a basic description of the look wanted as description
    generate custom theme from description as theme
    apply custom theme naming with theme as theme
  else:
    require the choice names one of the 10 preset themes
      otherwise:
        return to choosing
    read theme file from themes as theme
      otherwise:
        abort with "The chosen theme's file is missing from themes/."

  label confirming:
  show theme
  ask user to confirm the theme
  require user confirms the theme
    otherwise:
      return to choosing

  apply theme to artifact with theme as styled
  verify the styled artifact has proper contrast and readability and keeps the theme's visual identity on every slide from styled
    otherwise:
      apply theme fix with styled as styled
      retry
  write styled with artifact
  return styled as styled
```

## Step meanings

- **theme_assets**: the skill's `theme-showcase.pdf`, displayed for viewing only; never modified.
- **themes**: the `themes/` directory, one file per preset theme: Ocean Depths, Sunset Boulevard, Forest Canopy, Modern Minimalist, Golden Hour, Arctic Frost, Desert Rose, Tech Innovation, Botanical Garden, Midnight Galaxy.
- **custom theme**: generated in the style of the presets: a hex color palette plus header and body font pairings, chosen from the user's description.
- **custom theme naming**: give the theme a descriptive name like the presets, reflecting what its font/color combination represents.
- **theme to artifact**: apply the theme's colors and fonts consistently throughout the artifact.
- **theme fix**: correct contrast, readability or identity problems found.
