# Nested Claude Code CLI: Setup and Usage from Within a Claude Code Web Session

## Overview

When running inside a Claude Code web/remote session, you (the AI agent) can spawn
additional Claude Code CLI instances as child processes. This gives you:

- **Context window management**: Offload work to agents with fresh/separate context windows,
  preserving your own for the main conversation
- **Parallel execution**: Run multiple agents simultaneously for concurrent tasks
- **Model flexibility**: Route tasks to cheaper/faster models (Haiku, Sonnet) when Opus isn't needed
- **Persistent sessions**: Resume agent conversations across invocations using session IDs
- **Sub-agent architecture**: Use custom sub-agents with specialized prompts and tool restrictions
- **Agent teams** (experimental): Coordinate multiple agents that communicate with each other

## The Problem

In a Claude Code web session, authentication flows through pipe-based file descriptors
(`CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR=4`) from the `environment-manager` parent process.
Child processes cannot inherit these pipes, so naively running `claude -p "..."` hangs
indefinitely waiting for auth.

## The Solution

Use the session ingress token (already present in the container) as an OAuth token
environment variable, and unset the file descriptor variable:

```bash
TOKEN=$(cat /home/claude/.claude/remote/.session_ingress_token)
env \
  CLAUDE_CODE_OAUTH_TOKEN="$TOKEN" \
  CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR="" \
  claude -p "your prompt here"
```

### Why This Works

- `CLAUDE_CODE_OAUTH_TOKEN` provides the auth token directly as an env var (no FD needed)
- Setting `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR=""` prevents the CLI from trying to
  read from a non-existent pipe
- The session ingress token (`sk-ant-si-...`) is already tied to the user's account and
  subscription -- no separate API key billing
- This does NOT interfere with the parent Claude Code session (separate process, separate
  session ID)

### Helper Function

Add this to your workflow for convenience:

```bash
claude_agent() {
  local token
  token=$(cat /home/claude/.claude/remote/.session_ingress_token)
  env \
    CLAUDE_CODE_OAUTH_TOKEN="$token" \
    CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR="" \
    claude "$@"
}
```

Usage: `claude_agent -p "What is 2+2?" --model claude-haiku-4-5-20251001`

---

## CLI Reference (Key Flags)

| Flag | Description |
|------|-------------|
| `-p, --print` | **Required for non-interactive use.** Print response and exit |
| `--model <model>` | Model selection: `sonnet`, `opus`, `haiku`, or full ID like `claude-sonnet-4-5-20250929` |
| `--output-format <fmt>` | `text` (default), `json` (structured result), `stream-json` (realtime) |
| `-r, --resume <id>` | Resume a previous session by session ID |
| `-c, --continue` | Continue the most recent conversation |
| `--allowedTools <tools>` | Restrict which tools the agent can use |
| `--disallowedTools <tools>` | Deny specific tools |
| `--system-prompt <prompt>` | Override system prompt entirely |
| `--append-system-prompt <prompt>` | Append to default system prompt |
| `--max-budget-usd <amount>` | Cap spending for this invocation |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `bypassPermissions`, `dontAsk`, `plan` |
| `--agents <json>` | Define inline sub-agents as JSON |
| `--dangerously-skip-permissions` | Skip all permission checks (sandbox only) |
| `--no-session-persistence` | Don't save session to disk (ephemeral) |
| `--fallback-model <model>` | Auto-fallback when primary model is overloaded |

---

## Model Selection

You can select which model your child agents use. This is critical for cost management.

```bash
# Cheapest -- use for simple tasks, searches, summaries
claude_agent -p "Summarize this file" --model haiku

# Balanced -- good for most coding tasks
claude_agent -p "Refactor this function" --model sonnet

# Most capable -- for complex reasoning (also the most expensive)
claude_agent -p "Design the architecture" --model opus
```

### Cost Comparison (approximate)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| Haiku 4.5 | $0.80 | $4.00 | Search, simple tasks, triage |
| Sonnet 4.5 | $3.00 | $15.00 | Most coding, analysis, review |
| Opus 4.6 | $15.00 | $75.00 | Complex reasoning, architecture |

**Note**: The child agent's model is independent of the parent session's model.
Using Haiku for a search task costs ~20x less than Opus for the same task.

---

## Session Management

### Ephemeral Agents (Default Sub-Agent Pattern)

Runs, returns results, context is discarded:

```bash
# One-shot: result returns, context is lost
RESULT=$(claude_agent -p "Find all TODO comments in this project" \
  --model haiku --output-format json 2>/dev/null)
echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])"
```

### Persistent Sessions (Continuable Threads)

Create and resume conversations -- the agent retains full context:

```bash
# First call -- capture the session ID
claude_agent -p "Analyze src/auth/ for security issues. List them." \
  --model sonnet --output-format json 2>/dev/null > /tmp/analysis.json
SESSION_ID=$(python3 -c "import json; print(json.load(open('/tmp/analysis.json'))['session_id'])")

# Follow-up -- resumes with full prior context
claude_agent -p "Now fix issue #1 from your analysis" \
  --resume "$SESSION_ID" --model sonnet --output-format json 2>/dev/null
```

This is powerful because the resumed agent remembers everything from the prior conversation
without you re-explaining context. It also means their context window fills up gradually
across calls, just like a real conversation.

---

## Sub-Agents with Custom Prompts

### Inline Sub-Agents (via --agents flag)

Define specialized agents at invocation time:

```bash
claude_agent -p "Review the recent changes" \
  --model sonnet \
  --agents '{
    "reviewer": {
      "description": "Expert code reviewer",
      "prompt": "You are a senior code reviewer. Focus on security and performance.",
      "tools": ["Read", "Grep", "Glob", "Bash"],
      "model": "sonnet"
    }
  }'
```

### File-Based Sub-Agents (Persistent Configuration)

Create markdown files with YAML frontmatter under `.claude/agents/` (project-level)
or `~/.claude/agents/` (user-level):

```markdown
<!-- .claude/agents/security-reviewer.md -->
---
name: security-reviewer
description: Reviews code for security vulnerabilities. Use proactively after code changes.
tools: Read, Grep, Glob, Bash
model: sonnet
memory: project
---

You are a security specialist. When invoked:
1. Run git diff to see recent changes
2. Check for OWASP Top 10 vulnerabilities
3. Look for exposed secrets, injection risks, auth issues
4. Report findings by severity (critical/warning/info)
```

Sub-agents defined in files are loaded at session start. They can have:
- **Restricted tools**: Only the tools listed in `tools`
- **Persistent memory**: Set `memory: user|project|local` for cross-session learning
- **Hooks**: Lifecycle hooks for validation (e.g., block write queries)
- **Skills**: Preloaded skill content for domain knowledge
- **Custom permission modes**: Independent of the parent session

---

## Parallel Execution

Run multiple agents concurrently for independent tasks:

```bash
TOKEN=$(cat /home/claude/.claude/remote/.session_ingress_token)
export CLAUDE_CODE_OAUTH_TOKEN="$TOKEN"
export CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR=""

# Launch 3 agents in parallel
claude -p "Review src/auth/ for security issues" --model sonnet \
  --output-format json > /tmp/review1.json 2>/dev/null &
PID1=$!

claude -p "Review src/api/ for performance issues" --model sonnet \
  --output-format json > /tmp/review2.json 2>/dev/null &
PID2=$!

claude -p "Check test coverage gaps" --model haiku \
  --output-format json > /tmp/review3.json 2>/dev/null &
PID3=$!

# Wait for all to complete
wait $PID1 $PID2 $PID3

# Collect results
for f in /tmp/review1.json /tmp/review2.json /tmp/review3.json; do
  echo "=== $f ==="
  python3 -c "import json; print(json.load(open('$f'))['result'])"
done
```

### Why Parallel Agents Save Tokens

Each child agent starts with a nearly empty context window (~19K tokens of system prompt).
Compare this to your main session which may have 100K+ tokens of accumulated context.
Every API call in the main session sends all that context; child agents avoid this overhead.

---

## Agent Teams (Experimental)

Agent teams allow multiple agents to **communicate directly with each other**, not just
report back to you. This is more powerful than parallel sub-agents but uses significantly
more tokens.

### Prerequisites

Agent teams require the experimental flag. Set it via environment or settings:

```json
// In settings.json or .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### How Teams Work

| Component | Role |
|-----------|------|
| **Team lead** | Creates the team, spawns teammates, coordinates work |
| **Teammates** | Independent Claude Code instances working on assigned tasks |
| **Task list** | Shared list of work items that teammates claim and complete |
| **Mailbox** | Messaging system for inter-agent communication |

### Key Differences from Sub-Agents

| | Sub-Agents | Agent Teams |
|---|---|---|
| **Context** | Own window; results return to caller | Own window; fully independent |
| **Communication** | Report back to parent only | Teammates message each other directly |
| **Coordination** | Parent manages all work | Shared task list with self-coordination |
| **Best for** | Focused tasks where only the result matters | Complex work requiring discussion |
| **Token cost** | Lower | Higher (each teammate is a full instance) |

### Best Use Cases for Teams

- **Research and review**: Multiple teammates investigate different aspects simultaneously
- **Competing hypotheses**: Teammates test different theories and debate findings
- **New modules/features**: Each teammate owns a separate component
- **Cross-layer work**: Frontend, backend, and tests each owned by different teammates

### Display Modes

- **In-process**: All teammates in one terminal (default)
- **Split panes**: Each teammate in its own pane (requires tmux or iTerm2)

### Limitations (Current)

- No session resumption with in-process teammates
- One team per session
- No nested teams (teammates can't spawn their own teams)
- Leader is fixed for the team's lifetime

Full documentation: https://code.claude.com/docs/en/agent-teams

---

## Token Economics and Strategy

### When to Use Child Agents vs. Your Own Context

**Use your own context when:**
- The task needs iterative back-and-forth with the user
- Context from prior conversation steps is essential
- The task is quick and simple

**Use child agents when:**
- The task produces verbose output (test results, logs, large searches)
- The work is self-contained and can return a summary
- You want to preserve your own context window lifetime
- You need parallel execution
- You want to use a cheaper model for the task

### Cost-Saving Patterns

1. **Route by complexity**: Use Haiku for search/triage, Sonnet for implementation, Opus only
   for complex architecture decisions
2. **Ephemeral agents for one-shots**: Use `--no-session-persistence` for throwaway queries
3. **Resume instead of re-explain**: Use `--resume <session-id>` to continue work without
   re-sending all context
4. **Fresh context = cheaper calls**: A child agent with 19K system prompt tokens costs far
   less per turn than your main session at 150K+ tokens

---

## Important Notes

- **Token file expiry**: The session ingress token has an expiration time (check the JWT `exp`
  claim). If agents stop authenticating, the token may have expired.
- **Version**: This was tested with Claude Code CLI v2.1.37. Newer versions may have
  additional features or different behavior.
- **No interference**: Child agents run as separate processes with separate session IDs.
  They do not affect the parent session.
- **Billing**: Uses the same subscription/account as the parent session (not separate API billing).
- **Permissions**: Child agents inherit the environment's permission context. Use
  `--permission-mode` or `--dangerously-skip-permissions` as appropriate for your sandbox.
