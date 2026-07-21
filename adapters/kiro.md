# Kiro (AWS) Adapter

## Loading

Kiro reads `.kiro/steering/` files for project-level instructions.
Create a steering file that points to the skill:

```markdown
---
inclusion: auto
---

# Paper Assistant Steering

This project uses the Paper Assistant skill. Read `SKILL.md` for the
full protocol. Key rules:

1. Use `epp` CLI for all workflow operations
2. Evidence status must be tracked (planned/user_supplied/executed/verified)
3. Run `epp inspect . --json` on session start to diagnose project state
4. Do not mark LLM output as executed or verified
```

Save as `.kiro/steering/paper-assistant.md`.

## Capability Declaration

```python
from scripts.workflow import atomic_save
from scripts.shared.state import load as load_state, get_current_project
from scripts.shared.paths import PAPERS_DIR

project = get_current_project()
state = load_state(project)
state["agent_capabilities"] = {
    "agent_type": "kiro",
    "web_search": True,      # Kiro has web search tools
    "mcp_servers": [],       # populated from .kiro/settings/mcp.json
    "file_edit": True,
    "shell_exec": True,
    "texlive": False,        # detect via: shutil.which("xelatex")
}
atomic_save(project, state)
```

## Behavior Notes

- Kiro supports hooks → can auto-run `epp inspect` on file changes
- Kiro has web search and fetch tools → `research` module works fully
- MCP servers configured in `.kiro/settings/mcp.json` are available
- Steering files guide behavior across sessions
- Specs mode can drive the golden path step-by-step

## Hook Integration (Optional)

Create a hook to auto-diagnose on session start:

```json
{
  "name": "Paper Diagnose on Prompt",
  "version": "1.0.0",
  "when": { "type": "promptSubmit" },
  "then": {
    "type": "askAgent",
    "prompt": "If this is a paper project, run epp inspect . --json silently and incorporate the state into your response."
  }
}
```

## What This Adapter Does NOT Do

- Does not re-implement any analysis logic
- Does not override evidence status rules
- Does not bypass input validation gates
