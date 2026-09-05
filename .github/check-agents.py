"""Check the shipped Claude-native role carriers (issue #201)."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROLES = {
    "worker": "reference/worker-brief.md",
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
    expected_skills = (
        ["superpowers:test-driven-development", "superpowers:systematic-debugging"]
        if name == "worker" else []
    )
    assert metadata.get("skills") == expected_skills, f"{name}: incorrect skill bindings"
    assert (ROOT / source).is_file(), f"{name}: missing role source {source}"
    assert "${CLAUDE_PLUGIN_ROOT}/" + source in parts[2], f"{name}: missing portable source pointer"
    print(f"{name}: frontmatter, tools, skills, opus alias, and {source} pointer OK")
