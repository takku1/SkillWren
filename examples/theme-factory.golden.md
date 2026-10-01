---
skill: theme-factory
name: theme-factory
description: Style an artifact using a coherent visual theme.
version: 0.4
purpose: Style an artifact using a coherent visual theme.
accepts:
  artifact: { type: Artifact, required: true }
  theme: { type: Text, required: false }
  description: { type: Text, required: false }
produces:
  styled_artifact: { type: Artifact }
  theme_spec: { type: ThemeSpec, when: creating a theme }
  theme_listing: { type: List<Text>, when: listing themes }
owns-when:
  - user wants to change the visual styling of an artifact
  - user wants to apply an existing theme
  - user wants to create a new visual theme
requires:
  apply-theme: [artifact exists]
  create-theme: [artifact exists, description exists]
  show-themes: []
flows: [apply-theme, create-theme, show-themes]
authority:
  user-decides: [which theme to choose, whether the chosen theme is correct, whether a generated theme matches the intended direction, whether to accept a font substitution or color correction]
  system-decides: [whether resources exist, whether colors satisfy readability, whether fonts are available, whether the artifact is structurally valid]
  system-may: [suggest nearest readable colors, suggest available font substitutes, repair objective validity defects]
  system-must-not: [infer user approval, silently choose a theme]
effects:
  reads: [theme-showcase.pdf, themes/*.md, source artifact]
  creates: [styled artifact, themes/{name}.md]
  mutates: []
risk: medium
cost: moderate
budget: { header: 400, body: 2500 }
---

```contract
resources:
  showcase:
    path: theme-showcase.pdf
    access: read
    immutable: true
  themes:
    path: themes/*.md
    access: read+create
  source:
    path: source artifact
    access: read
  styled:
    path: styled artifact
    access: create
always:
  preserve artifact content
  apply the theme consistently
  maintain readable text/background relationships
  validate the result before returning
never:
  modify theme-showcase.pdf
  modify the source artifact
  choose a theme without user confirmation
  sacrifice readability for theme fidelity
  treat user confirmation as proof of technical validity
```

```logic
apply-theme:
  require artifact exists
    otherwise:
      abort with "An artifact is required."

  label theme selection:

  unless theme is known:
    open showcase as preview
    show preview
    ask user to choose a theme as theme
    ask user to confirm the chosen theme
    require user confirms chosen theme
      otherwise:
        abort with "Dismissed; nothing changed."

  read themes/{theme}.md as spec
    otherwise:
      read theme list from themes as available
      show available
      ask user to choose another theme as theme
      return to theme selection

  require spec is structurally valid
    otherwise:
      abort with "Invalid theme specification."

  require theme fonts are available
    otherwise:
      generate nearest available substitutes from spec as suggestion
      show suggestion
      ask user to accept the font substitution
      require user accepts font substitution
        otherwise:
          abort with "Dismissed; nothing changed."
      apply suggestion with spec as spec
      retry

  require theme colors satisfy readability
    otherwise:
      generate nearest readable correction from spec as correction
      show correction
      ask user to accept the color correction
      require user accepts color correction
        otherwise:
          abort with "Dismissed; nothing changed."
      apply correction with spec as spec
      retry

  apply spec with artifact as styled

  verify styled is structurally valid
    otherwise:
      discard styled
      abort with "Validation failed; source unchanged."

  verify theme is applied consistently
    otherwise:
      apply consistency correction with styled as styled
      retry

  verify artifact content is preserved
    otherwise:
      discard styled
      abort with "Content changed; source unchanged."

  return styled as styled_artifact
```

```logic
create-theme:
  require artifact exists
    otherwise:
      abort with "An artifact is required."

  require description exists
    otherwise:
      ask user to describe the desired visual direction as description
      require confirmation
        otherwise:
          abort with "Dismissed; nothing changed."
      retry

  label validation:

  generate cohesive theme from description as spec

  require spec is structurally valid
    otherwise:
      apply validity repair with spec as spec
      retry

  require spec colors satisfy readability
    otherwise:
      apply readable palette correction with spec as spec
      retry

  require spec fonts are available
    otherwise:
      apply nearest available font pairing with spec as spec
      retry

  generate preview from spec as preview
  show preview
  ask user to approve generated theme
  require user confirms spec
    otherwise:
      ask user what should change as feedback
      generate revised spec from feedback as spec
      return to validation

  generate theme name from spec as name
  save spec as themes/{name}.md

  run apply-theme with:
    artifact = artifact
    theme = name

  return:
    styled_artifact
    theme_spec = spec
```

```logic
show-themes:
  open showcase as preview
  show preview
  read theme list from showcase as listing
  return listing as theme_listing
```

## Appendix: creative guidance

Guidance only; no control semantics. When generating a theme from a
description, prefer a cohesive palette with explicit color values, one heading
font plus one body font, and a one-paragraph visual-identity note. When a
generated theme is rejected, revise from the user's stated feedback rather than
regenerating from scratch. Theme names are plain `Text`; structured
`Theme` objects are a future type refinement.

