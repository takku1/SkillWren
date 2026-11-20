# Requirement review: internal-comms

Source: sources/internal-comms/SKILL.md
Reviewed by: <your name>
Date: <YYYY-MM-DD>

**How to review.** These are model-drafted candidates. For each line: keep it
(`[x]`), drop it (change to `[ ]`), or edit the requirement text so it says
what the source really requires. Add anything missing as a new line with the
next free ID (`IC-7`, ...); quote the source span, or write `inferred` if you
accept it without one. Kinds: obligation, prohibition, exception, ordering,
authority, output. Then fill in the two lines above.

Note for the reviewer: the source routes "anything else" to
`general-comms.md` (IC-3) and also says to ask when the type matches no
guideline (IC-5). Decide how a faithful conversion should read these
together, and edit IC-3 or IC-5 to say it.

- [x] IC-1 | obligation | Identify the communication type from the request. | "Identify the communication type"
- [x] IC-2 | ordering | Load the matching guideline file from `examples/` before writing. | "Load the appropriate guideline file"
- [x] IC-3 | obligation | Route by type: 3P updates to `3p-updates.md`, newsletters to `company-newsletter.md`, FAQs to `faq-answers.md`, anything else to `general-comms.md`. | "For anything else that doesn't explicitly match one of the above"
- [x] IC-4 | obligation | Follow the loaded file's instructions for formatting, tone and content gathering. | "Follow the specific instructions"
- [x] IC-5 | exception | If the communication type matches no guideline, ask for clarification or more context about the desired format. | "ask for clarification or more context about the desired format"
- [x] IC-6 | authority | The skill applies to internal communications: 3P updates, newsletters, FAQ responses, status reports, leadership updates, project updates, incident reports. | "To write internal communications, use this skill for:"
