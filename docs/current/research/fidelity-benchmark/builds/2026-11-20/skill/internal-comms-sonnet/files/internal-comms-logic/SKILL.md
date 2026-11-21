---
name: internal-comms
description: Write internal communications in the company's preferred formats - 3P updates (Progress, Plans, Problems), company newsletters, FAQ answers, status reports, leadership updates, project updates and incident reports. Use whenever asked to write internal comms, a weekly update, company comms, FAQs or common questions. License terms are in LICENSE.txt in the original skill.
---

# Internal comms

```contract
inputs:
  request
order:
  verify the guideline file was loaded before generate communication
```

```logic
internal-comms:
  require request exists
    otherwise:
      abort with "Say which internal communication to write."

  label classifying:
  generate request classification from request as comm_type
  show comm_type

  if comm_type is too unclear to classify at all:
    ask user for more context about the desired format as clarification
    apply update with clarification as request
    return to classifying

  if comm_type is a 3P update (Progress, Plans, Problems):
    read 3p updates guideline from examples as guideline
      otherwise:
        abort with "examples/3p-updates.md is missing."
  else:
    if comm_type is a company newsletter:
      read newsletter guideline from examples as guideline
        otherwise:
          abort with "examples/company-newsletter.md is missing."
    else:
      if comm_type is an FAQ answer:
        read faq guideline from examples as guideline
          otherwise:
            abort with "examples/faq-answers.md is missing."
      else:
        read general guideline from examples as guideline
          otherwise:
            abort with "examples/general-comms.md is missing."

  verify the guideline file was loaded and is not empty from guideline
    otherwise:
      abort with "No guideline loaded; cannot write the communication."

  generate communication from request, guideline as communication
  apply guideline instructions with guideline as communication
  show communication
  return communication as communication
```

## Step meanings

- **update**: fold the user's answer into the request.
- **guideline instructions**: follow the loaded guideline file for formatting, tone and content gathering.
- **examples**: the `examples/` directory of this skill.
