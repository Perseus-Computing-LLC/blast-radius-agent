"""Render a BlastRadiusReport in the documented text format."""

from __future__ import annotations

from .engine import BlastRadiusReport


def format_report(report: BlastRadiusReport) -> str:
    lines = []
    target = report.target_path
    if report.target_name:
        target = f"{target} -- {report.target_name}"
    lines.append(f"BLAST RADIUS: {target}")
    lines.append("")

    lines.append(f"DIRECT IMPACT ({len(report.direct)} files):")
    if report.direct:
        for d in report.direct:
            lines.append(f"  - {d.path} — {d.name or d.language}")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"TRANSITIVE IMPACT ({len(report.transitive)} files):")
    if report.transitive:
        for d in report.transitive:
            lines.append(f"  - {d.path} (depth {d.depth})")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"PROJECT IMPACT ({len(report.projects)}):")
    if report.projects:
        for p in report.projects:
            lines.append(f"  - {p}")
    else:
        lines.append("  (none)")
    lines.append("")

    lines.append(f"RISK SCORE: {report.risk}")
    return "\n".join(lines)
