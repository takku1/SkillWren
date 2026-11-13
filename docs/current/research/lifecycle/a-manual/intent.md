# Skill A intent (manual): dependency audit with enforced reporting

Audit a Python repository for risky dependencies: run the dependency
check, verify its findings show no banned dependencies, and write the
findings report only after verification. Never write the report if
verification fails; a failed check produces blocked findings, which
the verifier rejects.
