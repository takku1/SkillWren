---
name: internal-comms
description: Write internal communications in the company's preferred formats by loading the matching guideline file: 3P updates (Progress, Plans, Problems), company newsletters, FAQ answers, status reports, leadership updates, project updates, incident reports. Use when asked to write any internal communication. Not for external or customer-facing writing.
---

# Internal comms (SkillWren logic)

The procedure is the `logic` block below. Execute it exactly; it is the only procedure.

```contract
inputs:
  request
order:
  apply identify type before read examples/
  verify#loaded before apply follow guideline
```

```logic
comms:
  apply identify type with request as comm_type

  if comm_type is unclear or matches no existing guideline:
    ask user to clarify the communication type or desired format
    require confirmation
      otherwise:
        apply record unresolved format with request as gap
        return gap as result
    apply identify type with request as comm_type

  if comm_type is a 3P (Progress, Plans, Problems) team update:
    read examples/3p-updates.md as guideline
      otherwise:
        apply record missing guideline with comm_type as gap
        return gap as result
  else:
    if comm_type is a company-wide newsletter:
      read examples/company-newsletter.md as guideline
        otherwise:
          apply record missing guideline with comm_type as gap
          return gap as result
    else:
      if comm_type is answering frequently asked questions:
        read examples/faq-answers.md as guideline
          otherwise:
            apply record missing guideline with comm_type as gap
            return gap as result
      else:
        read examples/general-comms.md as guideline
          otherwise:
            apply record missing guideline with comm_type as gap
            return gap as result

  exec guideline load check from checks as loaded
  verify #loaded the guideline file matching the type was loaded from loaded
    otherwise:
      apply record missing guideline with comm_type as gap
      return gap as result

  apply follow guideline with guideline as draft
  return draft as draft
```

## Step meanings

- **identify type**: determine the communication type from the user's request (3P update, company newsletter, FAQ answer, or something else such as a status report, leadership update, project update, or incident report). When the user has answered a clarification, use that answer too.
- **follow guideline**: follow the specific instructions in the loaded guideline file for formatting, tone, and content gathering, and write the communication for the user's request.
- **record unresolved format**: state that the desired format could not be determined and what context is still needed.
- **record missing guideline**: state which guideline file could not be loaded for the identified communication type, so the result says what was not done.

The guideline files live in `examples/` beside this file. Anything that does not explicitly match a 3P update, newsletter, or FAQ (status reports, leadership updates, project updates, incident reports) uses `examples/general-comms.md`.

| Flow step | Command |
|---|---|
| `exec guideline load check` | a check in `checks` that confirms the chosen `examples/` guideline file was read; passes iff exit 0 |
