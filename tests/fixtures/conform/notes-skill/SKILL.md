---
skill: notes-skill
name: notes-skill
description: Append a dated line to notes.txt. Fixture for skillwren conform.
version: 0.5
accepts:
  request: { type: Text, required: true }
produces:
  note: { type: Text }
owns-when:
  - user wants a line added to the notes file
requires:
  append: [request exists]
flows: [append]
authority:
  user-decides: []
  system-decides: [whether the request is a note]
  system-may: []
  system-must-not: [edit any file except notes.txt]
effects:
  reads: [notes]
  creates: []
  mutates: [notes]
risk: low
cost: cheap
budget: { header: 400, body: 2500 }
---

# Notes skill

```contract
resources:
  notes:
    path: notes.txt
    access: read+write
    glob: notes.txt
always:
  touch only notes.txt
never:
  create or edit any other file
```

```logic
append:
  require request exists
    otherwise:
      abort with "A request is required."

  read notes.txt as notes
  generate note from request as note
  apply append with note as notes
  write notes with notes.txt
  return note as note
```

## Appendix

- **append**: add the note as one new last line of notes.txt, keeping
  every existing line as it is.
