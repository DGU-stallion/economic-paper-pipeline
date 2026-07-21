# Codex (OpenAI) Adapter

## Loading

Codex reads `AGENTS.md` or repository documentation. Copy the key behavioral
rules from `SKILL.md` into `AGENTS.md` if your Codex setup requires it.

Alternatively, instruct Codex to read `SKILL.md` at session start.

## Capability Declaration

```python
from scripts.workflow import atomic_save
from scripts.shared.state import load as load_state, get_current_project
from scripts.shared.paths import PAPERS_DIR

project = get_current_project()
state = load_state(project)
state["agent_capabilities"] = {
    "agent_type": "codex",
    "web_search": False,    # Codex CLI does not have native web search
    "mcp_servers": [],
    "file_edit": True,
    "shell_exec": True,
    "texlive": False,       # detect via: shutil.which("xelatex")
}
atomic_save(project, state)
```

## Behavior Notes

- Codex operates in a sandboxed environment with internet disabled
- `research` module degrades to manual guidance (no web search)
- All file operations and Python execution work normally
- State is persisted in `pipeline_state.json` → sessions can resume
- Use `epp inspect . --json` to resume from where the last session left off

## Resuming Without Chat History

```bash
epp inspect . --json
```

This outputs the full project state. Codex can read it and continue from
the current readiness level without needing prior conversation context.

## What This Adapter Does NOT Do

- Does not re-implement any analysis logic
- Does not override evidence status rules
- Does not pretend web search is available when it is not
