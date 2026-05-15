#!/usr/bin/env bash
# announce-plugin-loaded.sh
# SessionStart hook: outputs additionalContext for the economics paper pipeline plugin.
#
# Behavior:
#   startup / clear  → Full welcome + command list + project status
#   resume / compact → Brief one-liner with current project progress

set -e

# ---- Detect session source ----
SOURCE="${CLAUDE_SESSION_SOURCE:-$1}"
if [ -z "$SOURCE" ]; then
  SOURCE="startup"
fi

# ---- Helper: read JSON value (no jq dependency) ----
read_json_field() {
  local file="$1"
  local field="$2"
  if [ -f "$file" ]; then
    grep -o "\"$field\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" \
      | sed "s/\"$field\"[[:space:]]*:[[:space:]]*\"//" \
      | sed 's/"//'
  fi
}

# ---- Paths ----
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$ROOT/config/current_project.json"
PIPELINE="$ROOT/scripts/pipeline.py"

# ---- startup / clear: full welcome ----
if [ "$SOURCE" = "startup" ] || [ "$SOURCE" = "clear" ]; then
  echo "additionalContext::"
  echo "additionalContext::## 📋 经济学实证论文自动化工作流已加载"
  echo "additionalContext::"
  echo "additionalContext::可用命令："
  echo "additionalContext::  /econ-help       显示所有命令"
  echo "additionalContext::  /econ-status     查看项目进度"
  echo "additionalContext::  /econ-list       列出所有论文项目"
  echo "additionalContext::  /econ-new        创建新项目"
  echo "additionalContext::  /econ-use        切换项目"
  echo "additionalContext::  /econ-topic      选题研究"
  echo "additionalContext::  /econ-literature 文献综述"
  echo "additionalContext::  /econ-stata      Stata 实证回归"
  echo "additionalContext::  /econ-paper      LaTeX 论文撰写"
  echo "additionalContext::  /econ-advance    推进到下一阶段"
  echo "additionalContext::"

  # Show current project status if exists
  if [ -f "$CONFIG_FILE" ]; then
    PROJECT_NAME=$(read_json_field "$CONFIG_FILE" "current_project")
    if [ -n "$PROJECT_NAME" ] && [ -f "$PIPELINE" ]; then
      STATUS=$(python "$PIPELINE" status 2>/dev/null || true)
      if [ -n "$STATUS" ]; then
        echo "additionalContext::当前项目：$PROJECT_NAME"
        echo "additionalContext::$STATUS" | head -5
        echo "additionalContext::"
      fi
    fi
  fi

  echo "additionalContext::输入 /econ-help 查看所有命令，或者直接告诉我你想做什么！"

# ---- resume / compact: brief progress (read stage directly from state file) ----
else
  echo "additionalContext::"
  if [ -f "$CONFIG_FILE" ]; then
    PROJECT_NAME=$(read_json_field "$CONFIG_FILE" "current_project")
    if [ -n "$PROJECT_NAME" ]; then
      STATE_FILE="$ROOT/papers/$PROJECT_NAME/pipeline_state.json"
      if [ -f "$STATE_FILE" ]; then
        STATE_ID=$(read_json_field "$STATE_FILE" "current_micro_state")
        if [ -n "$STATE_ID" ]; then
          STAGE_ID="${STATE_ID%%-*}"
          case "$STAGE_ID" in
            topic) STAGE_NAME="选题研究" ;;
            literature) STAGE_NAME="文献综述" ;;
            data) STAGE_NAME="数据清洗" ;;
            stata) STAGE_NAME="Stata实证" ;;
            robustness) STAGE_NAME="稳健性检验" ;;
            conclusion) STAGE_NAME="结论验证" ;;
            paper) STAGE_NAME="论文撰写" ;;
            completed) STAGE_NAME="已完成" ;;
            *) STAGE_NAME="$STAGE_ID" ;;
          esac
          echo "additionalContext::📋 回到「$PROJECT_NAME」—— 当前阶段：$STAGE_NAME"
          echo "additionalContext::"
          echo "additionalContext::输入 /econ-status 查看详情，或直接告诉我你想做什么。"
        fi
      fi
    fi
  fi
fi
