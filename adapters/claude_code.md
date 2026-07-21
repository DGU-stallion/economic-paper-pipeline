# Claude Code Adapter

## Loading

Claude Code loads `CLAUDE.md` as the project instruction file automatically.
No additional configuration is needed beyond cloning and installing.

## Capability Declaration

On first session, write to project state:

```python
from scripts.workflow import supply_user_input, atomic_save
from scripts.shared.state import load as load_state, get_current_project
from scripts.shared.paths import PAPERS_DIR

project = get_current_project()
state = load_state(project)
state["agent_capabilities"] = {
    "agent_type": "claude-code",
    "web_search": True,     # Claude Code has built-in web search
    "mcp_servers": [],      # populated from .mcp.json if available
    "file_edit": True,
    "shell_exec": True,
    "texlive": False,       # detect via: shutil.which("xelatex")
}
atomic_save(project, state)
```

## Behavior Notes

- Claude Code supports `/` slash commands → use `commands/` directory
- CLAUDE.md is read automatically as project instructions
- Bash tool is available → all `epp` CLI commands work directly
- Web search is native → `research` module uses agent's built-in search
- MCP servers declared in `.mcp.json` are available

## What This Adapter Does NOT Do

- Does not re-implement any analysis logic
- Does not override evidence status rules
- Does not bypass input validation gates
