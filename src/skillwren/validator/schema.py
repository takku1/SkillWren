"""Header schema (F1, B1, W7, W11): the SkillWren Frontmatter Profile."""
from .syntax import (BODY_DEFAULT, FORMAT_VERSION, HEADER_MAX, KNOWN_KEYS,
                     REQUIRED_KEYS, Diag, find_key_line, is_kebab,
                     parse_version, valid_type)


def check_schema(header, fm_lines, errors, warnings):
    def check_list_members(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                check_list_members(child, path + [key])
        elif isinstance(value, list) and any(not isinstance(item, str) for item in value):
            errors.append(Diag(find_key_line(fm_lines, path[0]), "F1",
                               f"{'.'.join(path)} entries must be strings",
                               "Use text entries, not nested maps or lists."))

    for section in ("authority", "effects", "requires", "flows", "owns-when"):
        if section in header:
            check_list_members(header[section], [section])
    missing = sorted(REQUIRED_KEYS - set(header.keys()))
    if missing:
        errors.append(Diag(1, "F1", f"frontmatter missing keys: {', '.join(missing)}",
                           "Add every required header field."))
    for key in sorted(set(header.keys()) - KNOWN_KEYS):
        warnings.append(Diag(find_key_line(fm_lines, key), "W7",
                             f"unknown frontmatter field {key!r}",
                             "Remove it or keep it if a tool needs it."))
    if header.get("name") and header.get("skill") \
            and header["name"] != header["skill"]:
        warnings.append(Diag(find_key_line(fm_lines, "name"), "W7",
                             "name should equal skill", "Align the two."))
    for key in ("skill", "description", "purpose", "release"):
        if key in header and (not isinstance(header[key], str)
                              or not header[key].strip()):
            errors.append(Diag(find_key_line(fm_lines, key), "F1",
                               f"{key} must be a non-empty string",
                               "Fill it in."))
    if isinstance(header.get("skill"), str) and header["skill"].strip() \
            and not is_kebab(header["skill"]):
        errors.append(Diag(find_key_line(fm_lines, "skill"), "F1",
                           f"skill id {header['skill']!r} must be kebab-case",
                           "Use lowercase letters, digits, and hyphens."))
    if "version" in header:
        ver = parse_version(header["version"])
        if ver is None:
            errors.append(Diag(find_key_line(fm_lines, "version"), "F1",
                               f"version must look like 0.4, got {header['version']!r}",
                               "Use numeric major.minor[.patch]."))
        elif ver > FORMAT_VERSION:
            errors.append(Diag(find_key_line(fm_lines, "version"), "F1",
                               f"format version {header['version']} is newer than this validator"
                               f" ({FORMAT_VERSION[0]}.{FORMAT_VERSION[1]})",
                               "Upgrade SkillWren to check this skill."))
    auth = header.get("authority")
    if isinstance(auth, dict):
        for sub in ("user-decides", "system-decides", "system-may",
                    "system-must-not"):
            if sub not in auth:
                errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                                   f"authority missing {sub}",
                                   "Add all four lists (empty allowed)."))
            elif not isinstance(auth[sub], list):
                errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                                   f"authority.{sub} must be a list",
                                   "Use [a, b] form."))
    elif "authority" in header:
        errors.append(Diag(find_key_line(fm_lines, "authority"), "F1",
                           "authority must be a map",
                           "Use indented sub-lists."))
    eff = header.get("effects")
    if isinstance(eff, dict):
        for sub in ("reads", "creates", "mutates"):
            if sub not in eff:
                errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                                   f"effects missing {sub}",
                                   "Add reads/creates/mutates lists."))
            elif not isinstance(eff[sub], list):
                errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                                   f"effects.{sub} must be a list",
                                   "Use [a, b] form."))
        if "executes" in eff and not isinstance(eff["executes"], list):
            errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                               "effects.executes must be a list", "Use [a, b] form."))
    elif "effects" in header:
        errors.append(Diag(find_key_line(fm_lines, "effects"), "F1",
                           "effects must be a map", "Use indented sub-lists."))
    for section in ("accepts", "produces"):
        val = header.get(section)
        if isinstance(val, dict):
            for name, entry in val.items():
                if not isinstance(entry, dict) or "type" not in entry:
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"{section}.{name} needs {{ type: ... }}",
                                       "Add the type."))
                elif not valid_type(str(entry["type"])):
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"{section}.{name} has unknown type {entry['type']!r}",
                                       "Use the closed v0.4 type set."))
                if section == "accepts" and isinstance(entry, dict) \
                        and "required" in entry \
                        and entry["required"] not in ("true", "false"):
                    errors.append(Diag(find_key_line(fm_lines, section), "F1",
                                       f"accepts.{name}.required must be true or false",
                                       "Use `true` or `false`."))
        elif section in header:
            errors.append(Diag(find_key_line(fm_lines, section), "F1",
                               f"{section} must be a map",
                               "Use indented name: entries."))
    req = header.get("requires")
    if isinstance(req, dict):
        for flow, conds in req.items():
            if not is_kebab(flow):
                errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                                   f"flow name {flow!r} must be kebab-case",
                                   "Use lowercase letters, digits, and hyphens."))
            if not isinstance(conds, list):
                errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                                   f"requires.{flow} must be a list",
                                   "Use [condition, ...] form."))
    elif "requires" in header:
        errors.append(Diag(find_key_line(fm_lines, "requires"), "F1",
                           "requires must be a map", "Use indented flow: lists."))
    for section in ("flows", "owns-when"):
        if section in header and not isinstance(header[section], list):
            errors.append(Diag(find_key_line(fm_lines, section), "F1",
                               f"{section} must be a list", "Use - items or [a, b]."))
    if isinstance(header.get("flows"), list):
        for flow in header["flows"]:
            if not is_kebab(flow):
                errors.append(Diag(find_key_line(fm_lines, "flows"), "F1",
                                   f"flow name {flow!r} must be kebab-case",
                                   "Use lowercase letters, digits, and hyphens."))
    if "risk" in header and header["risk"] not in ("low", "medium", "high"):
        errors.append(Diag(find_key_line(fm_lines, "risk"), "F1",
                           f"risk must be low|medium|high, got {header['risk']!r}",
                           "Pick a valid level."))
    if "cost" in header and header["cost"] not in ("cheap", "moderate", "expensive"):
        errors.append(Diag(find_key_line(fm_lines, "cost"), "F1",
                           f"cost must be cheap|moderate|expensive, got {header['cost']!r}",
                           "Pick a valid level."))
    budget = header.get("budget")
    if isinstance(budget, dict):
        for sub in ("header", "body"):
            try:
                cap = int(budget.get(sub, "x"))
            except (TypeError, ValueError):
                errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                                   f"budget.{sub} must be an integer",
                                   "Use a token count."))
            else:
                if cap <= 0:
                    errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                                       f"budget.{sub} must be a positive integer",
                                       "Use a token count above zero."))
                elif sub == "header" and cap > HEADER_MAX:
                    errors.append(Diag(find_key_line(fm_lines, "budget"), "B1",
                                       f"budget.header {cap} exceeds the {HEADER_MAX}-token routing maximum",
                                       f"Declare at most {HEADER_MAX}; trim header prose instead."))
                elif sub == "body" and cap > BODY_DEFAULT:
                    warnings.append(Diag(find_key_line(fm_lines, "budget"), "W11",
                                         f"budget.body {cap} is above the {BODY_DEFAULT}-token default",
                                         "Keep it if the body needs it (for example a step glossary); say why in a comment."))
    elif "budget" in header:
        errors.append(Diag(find_key_line(fm_lines, "budget"), "F1",
                           "budget must be a map", "Use { header: N, body: M }."))
