---
name: internal-comms
description: Write internal communications in the company's preferred formats: 3P updates (Progress, Plans, Problems), company newsletters, FAQ answers, status reports, leadership updates, project updates, incident reports. Use when asked to write any internal comms or weekly update. Not for external or customer-facing writing.
---

# Internal communications (SkillWren logic)

The procedure is the `logic` block below. Execute it exactly; it is the only procedure.

```contract
inputs:
  request
order:
  verify#loaded3p before apply#draft3p
  verify#loadednews before apply#draftnews
  verify#loadedfaq before apply#draftfaq
  verify#loadedgen before apply#draftgen
```

```logic
write-internal-comms:
  apply identify communication type with request as comm_type

  unless comm_type matches a known guideline or general comms:
    ask user to clarify the desired communication format
    require confirmation
      otherwise:
        apply gap record with request as gap
        return gap as communication
    apply identify communication type with request as comm_type

  if comm_type is a 3P update:
    read examples/3p-updates.md as guideline
      otherwise:
        apply gap record with request as gap
        return gap as communication
    exec 3P guideline load check from checks as loaded3p
    verify #loaded3p 3P guideline is loaded from loaded3p
      otherwise:
        apply gap record with request as gap
        return gap as communication
    apply #draft3p draft communication with guideline as communication
  else:
    if comm_type is a company newsletter:
      read examples/company-newsletter.md as guideline
        otherwise:
          apply gap record with request as gap
          return gap as communication
      exec newsletter guideline load check from checks as loadednews
      verify #loadednews newsletter guideline is loaded from loadednews
        otherwise:
          apply gap record with request as gap
          return gap as communication
      apply #draftnews draft communication with guideline as communication
    else:
      if comm_type is an FAQ answer:
        read examples/faq-answers.md as guideline
          otherwise:
            apply gap record with request as gap
            return gap as communication
        exec FAQ guideline load check from checks as loadedfaq
        verify #loadedfaq FAQ guideline is loaded from loadedfaq
          otherwise:
            apply gap record with request as gap
            return gap as communication
        apply #draftfaq draft communication with guideline as communication
      else:
        read examples/general-comms.md as guideline
          otherwise:
            apply gap record with request as gap
            return gap as communication
        exec general guideline load check from checks as loadedgen
        verify #loadedgen general guideline is loaded from loadedgen
          otherwise:
            apply gap record with request as gap
            return gap as communication
        apply #draftgen draft communication with guideline as communication

  return communication as communication
```

## Step meanings

- **identify communication type**: decide from the request which kind of internal communication is wanted: 3P update (Progress/Plans/Problems), company newsletter, FAQ answer, or anything else (status report, leadership update, project update, incident report), which uses general comms.
- **gap record**: state which guideline or format information is missing or was not clarified, and that no communication was drafted because of it.
- **draft communication**: write the communication for the identified type following the loaded guideline file's specific instructions for formatting, tone, and content gathering.

## Context

This skill applies whenever asked to write internal communications in the company's preferred formats: status reports, leadership updates, 3P updates, company newsletters, FAQs, incident reports, project updates, and similar. Keywords: 3P updates, company newsletter, company comms, weekly update, faqs, common questions, updates, internal comms.

The guideline files in `examples/` are external resources whose contents this skill does not carry. The formatting, tone, and content-gathering behavior depends on them, so read the file fully before drafting and defer to it over any default style.

## Commands

| Step | Command |
|---|---|
| `exec 3P guideline load check` | confirm `examples/3p-updates.md` was read and is non-empty |
| `exec newsletter guideline load check` | confirm `examples/company-newsletter.md` was read and is non-empty |
| `exec FAQ guideline load check` | confirm `examples/faq-answers.md` was read and is non-empty |
| `exec general guideline load check` | confirm `examples/general-comms.md` was read and is non-empty |
