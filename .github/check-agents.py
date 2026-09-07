"""Check the shipped Claude-native role carriers (issue #201)."""

from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "worker": "reference/worker.md",
    "reviewer": "reference/code-review-prompt.md",
}

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
    raw_tools = metadata.get("tools")
    assert isinstance(raw_tools, str), f"{name}: tools must be a comma-separated allowlist"
    tools = {tool.strip() for tool in raw_tools.split(",")}
    expected_tools = {"Read", "Glob", "Grep"}
    if name == "worker":
        expected_tools |= {"Bash", "Edit", "Write", "Skill"}
    assert tools == expected_tools, f"{name}: unexpected tool surface: {tools}"
    binding_source = (ROOT / 'reference/worker.md').read_text().split(
        '<!-- BEGIN WORKER SKILLS -->', 1)[1].split('<!-- END WORKER SKILLS -->', 1)[0]
    worker_skills = re.findall(r'`(superpowers:[^`]+)`', binding_source)
    assert len(worker_skills) == 3 and len(set(worker_skills)) == 3, 'missing worker bindings'
    expected_skills = worker_skills if name == "worker" else []
    assert metadata.get("skills") == expected_skills, f"{name}: incorrect skill bindings"
    assert (ROOT / source).is_file(), f"{name}: missing role source {source}"
    if name == "worker":
        assert "${CLAUDE_PLUGIN_ROOT}/" + source in parts[2], f"{name}: missing portable source pointer"
    else:
        assert "supplied packet's filled fence is your sole judging contract" in parts[2], \
            "reviewer: must bind the supplied contract"
        assert "IN FULL" not in parts[2] and "${CLAUDE_PLUGIN_ROOT}/" + source not in parts[2], \
            "reviewer: must not route to a second installed contract"
    print(f"{name}: frontmatter, tools, skills, opus alias, and {source} delivery OK")
