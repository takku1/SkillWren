"""Scripted stand-in for a model adapter: valid proposal, no model calls."""
import json
import sys

request = json.load(sys.stdin)
assert isinstance(request.get("intent"), str) and request["intent"].strip()
print(json.dumps({
    "flow": ("# Proposed from intent\n\n```logic\ndraft:\n"
             "  return notes as notes\n```\n"),
    "assumptions": ["scripted adapter assumes a trivial single-step flow"],
    "questions": ["is a single return step what you meant?"],
}))
