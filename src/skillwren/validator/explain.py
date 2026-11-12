"""Plain-language explanations for every diagnostic code (`check --explain`)."""

RULE_EXPLAIN = {
    "P2": "Stable operation IDs must be unique within a document so an ordering"
          " rule cannot silently refer to two different operations.",
    "F1": "The contract header is machine-readable metadata with a strict"
          " schema, so every required field, type, and flag must be"
          " well-formed (SPEC Section 5).",
    "F2": "Fences and the contract block carry control meaning, so"
          " mislabeled fences, misordered blocks, and malformed resources"
          " are errors (SPEC Sections 8 and 10).",
    "F3": "Every declared flow needs a body and vice versa, so the header"
          " flow list and the logic fences must match exactly"
          " (SPEC Section 6).",
    "V1": "Flow bodies use a closed control vocabulary, so anything outside"
          " it is an error rather than prose (SPEC Section 6).",
    "R1": "Header requires duplicates each flow's leading require lines so"
          " routing stays header-only; the two must match exactly"
          " (SPEC Section 5).",
    "R2": "Flows return declared produces entries and end every path in"
          " return or abort, so the caller always gets what was promised"
          " (SPEC Section 6).",
    "R3": "A run names a flow in the same file, so an unknown target is"
          " rejected before execution (SPEC Section 11).",
    "R4": "Required inputs a flow consumes must be gated by a leading"
          " require, so missing input fails fast at entry (SPEC Section 6).",
    "T1": "For-each iterates List-typed bindings, so looping over a known"
          " non-List type is an error (SPEC Section 6).",
    "T2": "Run arguments bind by name into the callee, so a known-typed"
          " value that mismatches the declared accepts type is rejected"
          " (SPEC Section 11).",
    "U1": "A binding must exist on every path to its use, so a"
          " possibly-unbound reference is rejected (SPEC Section 6).",
    "E1": "Every effect target must name a declared resource, path, or"
          " input, so undeclared touches are visible before execution"
          " (SPEC Section 8).",
    "E2": "Touched resources must be covered by header effects, and"
          " same-path read-plus-write means mutates, so audits stay honest"
          " (SPEC Section 8).",
    "E3": "Immutable resources must never be a write target"
          " (SPEC Section 8).",
    "E4": "Apply is a pure in-memory transform, so it cannot name a"
          " resource target (SPEC Section 6).",
    "A1": "An allow narrows exactly one never invariant, so an allow"
          " matching none is an error (SPEC Section 8).",
    "A2": "User decisions need a decision ask before the gate and a"
          " confirmation after it, so authority is structural, not implied"
          " (SPEC Section 7).",
    "L1": "Labels must be unique and declared, and loop variables and"
          " iterated collections must not be rebound inside the loop"
          " (SPEC Section 6).",
    "L2": "Flows cannot recurse through run cycles (SPEC Section 11).",
    "L3": "Retry re-executes the failed gate, so it may only appear inside"
          " an otherwise repair block (SPEC Section 12).",
    "O1": "Otherwise repairs nest directly under a fallible gate, and only"
          " branches, loops, repairs, returns, and run args take indented"
          " bodies (SPEC Sections 6 and 12).",
    "B1": "Headers and bodies have token ceilings so discovery stays cheap;"
          " overruns fail validation (SPEC Section 10).",
    "M1": "Dismissing an ask must mutate nothing, so no write may precede a"
          " dismissible ask on any path (SPEC Section 12).",
    "W1": "Owns-when triggers are the routing surface, so two skills whose"
          " triggers overlap will compete for the same requests"
          " (SPEC Section 5).",
    "W2": "Authority the header grants should be authority the flows use,"
          " so a system-may entry no flow exercises is flagged as stale"
          " (SPEC Section 7).",
    "W3": "Decision asks and user-decides entries must name each other, so"
          " an ask with no matching entry (or an entry no ask exercises)"
          " leaves authority ambiguous (SPEC Section 7).",
    "W4": "Generate steps are creative, so the appendix is where their"
          " guidance lives; a generate with no appendix section is"
          " unguided (SPEC Section 6).",
    "W5": "A binding nothing reads is dead weight in the flow, so it is"
          " flagged for removal (SPEC Section 6).",
    "W6": "Effects entries audit against declared resources, so an entry"
          " matching no resource cannot be checked (SPEC Section 8).",
    "W7": "The header profile is closed, so unknown fields are ignored by"
          " tooling and a name that differs from the skill id confuses"
          " routing (SPEC Section 5).",
    "W8": "A cross-skill run's effects live in another file, so the"
          " single-file validator marks it as an unverified boundary"
          " rather than a checked call (SPEC Section 11).",
    "W9": "An otherwise repair must end in retry, return to, abort, or"
          " return, so a repair that falls through continues in a state"
          " the gate rejected (SPEC Section 12).",
    "W10": "A statement no path reaches is dead control flow, usually a"
           " sign the branch structure is not what the author meant"
           " (SPEC Section 6).",
    "W11": "Body ceilings default to 2500 tokens so skills stay cheap to"
           " load; a higher declared ceiling is allowed but should be"
           " justified in a comment (SPEC Section 10).",
    "W12": "Apply specs are defined by appendix anchors, so a spec no"
           " appendix item defines is prose the reader cannot resolve"
           " (SPEC Section 13).",
    "P1": "An order rule `A before B` says B may start only after A has"
          " completed on every path, so a path that reaches B without A (or"
          " only through a failed A gate) is an error (SPEC Section 20).",
    "W13": "An order rule whose later step matches no statement never"
           " constrains anything, which usually means the pattern is"
           " misspelled (SPEC Section 20).",
    "W14": "Fragment checking only reads ```logic blocks, so a file without"
           " one passed nothing; prose-only flows are allowed but unchecked"
           " (SPEC Section 20).",
    "W15": "An order rule is only as checkable as its earlier step. If every"
           " statement that completes it is the model's own judgment (no"
           " exec, no evidence-backed verify, no artifact, no user"
           " decision), nothing outside the model can observe it, so the"
           " rule is a self-report (SPEC Section 20; game-theory review).",
}
