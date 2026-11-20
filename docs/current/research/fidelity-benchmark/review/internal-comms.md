# Requirement review: internal-comms

Source: sources/internal-comms/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>
Candidate status: AI-drafted, AI-reviewed three times (drafting session; external AI
reviews 2026-11-20, revisions 2 and 3). Not human-approved: freezing needs the human
reviewer's name and date.

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`IC-7`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

Note for the reviewer: IC-3 and IC-5 now read the source as "the general
template is the fallback; ask when the format is still unclear or
unsupported" (external AI review). Confirm or correct that reading.

- [x] IC-1 | obligation | Identify the communication type from the request. | "Identify the communication type"
- [x] IC-2 | ordering | Load the matching guideline file from `examples/` before writing. | "Load the appropriate guideline file"
- [x] IC-3 | obligation | Route by type: 3P updates to `3p-updates.md`, newsletters to `company-newsletter.md`, FAQs to `faq-answers.md`; `general-comms.md` is the fallback for any other internal communication (reviewer interpretation of an ambiguous source). | "For anything else that doesn't explicitly match one of the above"
- [x] IC-4 | obligation | Follow the loaded file's instructions for formatting, tone and content gathering. | "Follow the specific instructions"
- [x] IC-5 | exception | When the desired format is still unclear or unsupported after routing (including the general fallback), ask for clarification or more context about it (reviewer interpretation of an ambiguous source). | "ask for clarification or more context about the desired format"
- [x] IC-6 | authority | The skill applies to internal communications: 3P updates, newsletters, FAQ responses, status reports, leadership updates, project updates, incident reports. | "To write internal communications, use this skill for:"

## Revision log

- IC-3 makes `general-comms.md` the fallback; IC-5 asks only when the format is still unclear or unsupported, resolving their overlap (external AI review). The reading is an interpretation: the human reviewer decides.
- Revision 3: IC-3 and IC-5 are marked in the requirement text as reviewer interpretations, so the frozen key says so (external AI review agreed with the reading).
