"""Context file generators."""

from agentmd.generators.base import BaseGenerator
from agentmd.generators.claude import ClaudeGenerator
from agentmd.generators.codex import CodexGenerator
from agentmd.generators.copilot import CopilotGenerator
from agentmd.generators.cursor import CursorGenerator

__all__ = [
    "BaseGenerator",
    "ClaudeGenerator",
    "CodexGenerator",
    "CopilotGenerator",
    "CursorGenerator",
]

GENERATOR_MAP: dict[str, type[BaseGenerator]] = {
    "claude": ClaudeGenerator,
    "codex": CodexGenerator,
    "cursor": CursorGenerator,
    "copilot": CopilotGenerator,
}
