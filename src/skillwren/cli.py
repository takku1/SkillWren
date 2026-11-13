"""SkillWren console entry point: one table of subcommands.

`check` takes the full argv (it predates the table); every other
subcommand receives the arguments after its name. Modules load lazily so
`check` stays stdlib-only and fast.
"""
import importlib
import sys

COMMANDS = {
    "audit": ("skillwren.audit", "check retained log against an independent checkpoint"),
    "sandbox": ("skillwren.sandbox", "observe command effects in an offline restricted container"),
    "guard": ("skillwren.guard", "mediate policy-bound verified writes on a trusted host"),
    "measure": ("skillwren.metrics", "compare measured context sizes"),
    "build": ("skillwren.compiler", "compile and package a reviewed skill"),
    "conform": ("skillwren.conform", "run a skill headless and compare effects"),
    "ledger": ("skillwren.ledger", "record a run's steps and check its order rules"),
    "explain-workflow": ("skillwren.validator.workflow", "describe a workflow's meaning deterministically"),
    "approve": ("skillwren.validator.approval", "record or check human approval of a workflow"),
    "draft": ("skillwren.validator.draft", "propose a workflow from intent via a model adapter"),
}


def dispatch(argv):
    name = argv[1] if len(argv) > 1 else None
    if name is None or name in ("--help", "-h"):
        print("usage: skillwren <command> [<args>] | check [flags] <file>...")
        for command in sorted(COMMANDS):
            print(f"  {command}: {COMMANDS[command][1]}")
        return 0
    if name in COMMANDS:
        module = importlib.import_module(COMMANDS[name][0])
        return module.main(argv[2:])
    from .validator import main as check_main
    code = check_main(argv)
    if code == 2 and name not in (None, "check"):
        print("other commands: " + ", ".join(
            f"{cmd} ({text})" for cmd, (_module, text) in COMMANDS.items()))
    return code


def main() -> None:
    sys.exit(dispatch(sys.argv))
