"""Swift/Xcode project detection heuristics."""

from __future__ import annotations

from pathlib import Path

from agentmd.detectors.common import read_text
from agentmd.types import DetectorFindings

# Ordered lists for deterministic output
PROJECT_TYPE_ORDER = ["xcodeproj", "xcworkspace", "spm", "cocoapods"]
FRAMEWORK_ORDER = ["SwiftUI", "UIKit", "AppKit", "Combine"]
LINTER_ORDER = ["SwiftLint", "swift-format"]

# Import statements to look for in .swift source files
FRAMEWORK_IMPORTS: dict[str, list[str]] = {
    "SwiftUI": ["import SwiftUI"],
    "UIKit": ["import UIKit"],
    "AppKit": ["import AppKit"],
    "Combine": ["import Combine"],
}


def detect_swift_project(root: Path, files: list[Path]) -> DetectorFindings:
    """Detect Swift/Xcode project types, frameworks, linters, and CI usage."""
    detected: set[str] = set()
    evidence: dict[str, list[str]] = {}

    file_names = {path.name for path in files}
    file_paths_str = [str(path) for path in files]

    # --- Project file detection ---
    # .xcodeproj (directory, appears as a path component)
    for fp in file_paths_str:
        if ".xcodeproj" in fp:
            detected.add("xcodeproj")
            evidence.setdefault("xcodeproj", []).append(fp.split(".xcodeproj")[0] + ".xcodeproj")
            break

    if "Package.swift" in file_names:
        detected.add("spm")
        evidence.setdefault("spm", []).append("Package.swift")

    if "Podfile" in file_names:
        detected.add("cocoapods")
        evidence.setdefault("cocoapods", []).append("Podfile")

    # .xcworkspace (directory, appears as a path component)
    for fp in file_paths_str:
        if ".xcworkspace" in fp:
            detected.add("xcworkspace")
            evidence.setdefault("xcworkspace", []).append(
                fp.split(".xcworkspace")[0] + ".xcworkspace"
            )
            break

    # --- Framework detection (scan .swift source files) ---
    swift_files = [root / path for path in files if path.suffix == ".swift"]
    for swift_file in swift_files[:50]:  # cap to avoid huge scans
        content = read_text(swift_file, max_chars=10000)
        if not content:
            continue
        for framework, patterns in FRAMEWORK_IMPORTS.items():
            if framework not in detected:
                for pattern in patterns:
                    if pattern in content:
                        detected.add(framework)
                        evidence.setdefault(framework, []).append(str(swift_file.relative_to(root)))
                        break

    # Also check Package.swift for framework references
    package_swift = root / "Package.swift"
    if package_swift.exists():
        content = read_text(package_swift, max_chars=20000)
        for framework, patterns in FRAMEWORK_IMPORTS.items():
            for pattern in patterns:
                if pattern.replace("import ", "") in content:
                    detected.add(framework)
                    evidence.setdefault(framework, []).append("Package.swift")
                    break

    # --- Linter detection ---
    linter_configs = {"swiftlint.yml", ".swiftlint.yml"}
    for cfg in linter_configs:
        if cfg in file_names:
            detected.add("SwiftLint")
            evidence.setdefault("SwiftLint", []).append(cfg)
            break

    if ".swift-format" in file_names:
        detected.add("swift-format")
        evidence.setdefault("swift-format", []).append(".swift-format")

    # --- CI: xcodebuild in GitHub Actions workflows ---
    workflow_files = [
        root / path
        for path in files
        if str(path).startswith(".github/workflows/") and path.suffix in {".yml", ".yaml"}
    ]
    for wf in workflow_files:
        content = read_text(wf, max_chars=20000)
        if "xcodebuild" in content:
            detected.add("xcodebuild-ci")
            evidence.setdefault("xcodebuild-ci", []).append(str(wf.relative_to(root)))
            break

    # Build ordered values list
    order = PROJECT_TYPE_ORDER + FRAMEWORK_ORDER + LINTER_ORDER + ["xcodebuild-ci"]
    values = [item for item in order if item in detected]
    trimmed_evidence = {k: sorted(set(v))[:5] for k, v in evidence.items() if k in detected}
    return DetectorFindings(values=values, evidence=trimmed_evidence)
