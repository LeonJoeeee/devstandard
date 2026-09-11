"""Check the shipped Claude-native role carriers (issues #201, #334, #339)."""

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "worker": "reference/worker.md",
    "reviewer": "reference/code-review-prompt.md",
}
# The hook role a definition pins in its own frontmatter. The reviewer pins none: it is spawned
# by an orchestrator, whose hook maps the reviewer agent type onto the reviewer role.
HOOK_ROLE = {"worker": "worker"}
HOOK_COMMAND = '"${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use" --role '

binding_source = (ROOT / 'reference/worker.md').read_text().split(
    '<!-- BEGIN WORKER SKILLS -->', 1)[1].split('<!-- END WORKER SKILLS -->', 1)[0]
worker_skills = re.findall(r'`(superpowers:[^`]+)`', binding_source)
assert len(worker_skills) == 3 and len(set(worker_skills)) == 3, 'missing worker bindings'

for name, source in ROLES.items():
    path = ROOT / "agents" / f"{name}.md"
    assert path.is_file(), f"missing agent definition: {path.relative_to(ROOT)}"
    parts = path.read_text().split("---\n", 2)
    assert len(parts) == 3 and parts[0] == "", f"{name}: missing YAML frontmatter"
    metadata = yaml.safe_load(parts[1])
    assert isinstance(metadata, dict), f"{name}: frontmatter must be a mapping"
    assert metadata.get("name") == name, f"{name}: use an unscoped role name"
    description = metadata.get("description")
    assert isinstance(description, str) and description.strip(), f"{name}: missing description"
    assert metadata.get("model") == "opus", f"{name}: model must use the opus tier alias"
    # No tool allowlist anywhere (#334). A definition with no `tools` field inherits the
    # session's whole tool set, MCP servers included — which is how a worker reaches `Agent`
    # to spawn subagents of its own (#339). The reviewer forbids the built-in writers by name
    # and is read-only by contract; the worker forbids nothing.
    assert "tools" not in metadata, f"{name}: must carry no tool allowlist"
    expected_disallowed = None if name == "worker" else "Write, Edit, NotebookEdit"
    assert metadata.get("disallowedTools") == expected_disallowed, \
        f"{name}: disallowedTools must be {expected_disallowed!r}"
    hook_role = HOOK_ROLE.get(name)
    hooks = metadata.get("hooks")
    if hook_role is None:
        assert hooks is None, f"{name}: must pin no role hook of its own"
    else:
        commands = [h["command"] for entry in hooks["PreToolUse"] for h in entry["hooks"]]
        assert commands == [HOOK_COMMAND + hook_role], \
            f"{name}: must pin the {hook_role} role hook, got {commands}"
    expected_skills = worker_skills if name == "worker" else []
    assert metadata.get("skills") == expected_skills, f"{name}: incorrect skill bindings"
    assert (ROOT / source).is_file(), f"{name}: missing role source {source}"
    if name == "worker":
        assert "${CLAUDE_PLUGIN_ROOT}/" + source in parts[2], f"{name}: missing portable source pointer"
    else:
        # The judge routes to no second installed contract: the caller supplies what it judges.
        assert "IN FULL" not in parts[2] and "${CLAUDE_PLUGIN_ROOT}/" + source not in parts[2], \
            f"{name}: must not route to a second installed contract"
        assert "supplied packet's filled fence is your sole judging contract" in parts[2], \
            "reviewer: must bind the supplied contract"
    print(f"{name}: frontmatter, no allowlist, writer denial, skills, opus alias, hook "
          f"and {source} binding OK")
