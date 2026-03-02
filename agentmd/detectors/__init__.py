"""Detection modules for project analysis."""

from agentmd.detectors.ci import detect_ci_systems
from agentmd.detectors.framework import detect_frameworks
from agentmd.detectors.language import detect_languages
from agentmd.detectors.lint import detect_linters
from agentmd.detectors.package_manager import detect_package_managers
from agentmd.detectors.go import detect_go_project
from agentmd.detectors.rust import detect_rust_project
from agentmd.detectors.swift import detect_swift_project
from agentmd.detectors.test_runner import detect_test_runners

__all__ = [
    "detect_ci_systems",
    "detect_frameworks",
    "detect_go_project",
    "detect_languages",
    "detect_linters",
    "detect_package_managers",
    "detect_rust_project",
    "detect_swift_project",
    "detect_test_runners",
]
