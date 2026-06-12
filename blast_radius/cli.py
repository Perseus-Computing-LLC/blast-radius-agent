"""Command-line entrypoint for local blast-radius analysis.

Usage:
    python -m blast_radius <path> [--function NAME] [--graph FIXTURE.json]
                           [--json] [--max-depth N] [--env PATH]

Without --graph it uses the Orbit CLI (`orbit sql`) in local mode, honoring the
keys in .env / .env.example. With --graph it runs fully offline against a graph
fixture (the same contract Orbit returns), which is what the test suite and the
offline demo use.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .config import Config
from .engine import BlastRadiusEngine, TargetResolutionError
from .orbit_client import InMemoryOrbitClient, OrbitCLIClient
from .report import format_report


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="blast-radius",
        description="Trace cross-file dependency blast radius via GitLab Orbit.",
    )
    p.add_argument("path", help="Target file path (exact or suffix match).")
    p.add_argument("--function", "-f", help="Function/definition name to disambiguate.")
    p.add_argument(
        "--graph",
        help="Path to a JSON graph fixture for offline mode (skips Orbit CLI).",
    )
    p.add_argument("--max-depth", type=int, help="Override max transitive depth.")
    p.add_argument("--env", help="Path to a .env file to load.")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return p


def _report_to_dict(report) -> dict:
    return {
        "target_path": report.target_path,
        "target_name": report.target_name,
        "risk": str(report.risk),
        "direct": [d.__dict__ for d in report.direct],
        "transitive": [d.__dict__ for d in report.transitive],
        "projects": report.projects,
        "total_dependents": report.total_dependents,
        "max_depth": report.max_depth,
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    config = Config.load(dotenv_path=args.env)
    if args.max_depth is not None:
        config = Config(
            orbit_mode=config.orbit_mode,
            orbit_cli_path=config.orbit_cli_path,
            gitlab_url=config.gitlab_url,
            gitlab_token=config.gitlab_token,
            max_depth=args.max_depth,
            exclude_patterns=config.exclude_patterns,
            thresholds=config.thresholds,
            cross_project_critical=config.cross_project_critical,
        )

    if args.graph:
        try:
            graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        except FileNotFoundError:
            sys.stderr.write(f"Error: graph fixture not found: {args.graph}\n")
            return 5
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"Error: invalid JSON in graph fixture {args.graph}: {exc}\n")
            return 5
        client = InMemoryOrbitClient(graph)
    else:
        cli_client = OrbitCLIClient(cli_path=config.orbit_cli_path)
        if not cli_client.available():
            sys.stderr.write(
                "Error: Orbit CLI not found on PATH "
                f"(ORBIT_CLI_PATH={config.orbit_cli_path!r}). "
                "Install Orbit CLI or pass --graph FIXTURE.json for offline mode.\n"
            )
            return 2
        client = cli_client

    engine = BlastRadiusEngine(client, config)
    try:
        report = engine.analyze(path=args.path, name=args.function)
    except TargetResolutionError as exc:
        sys.stderr.write(f"Target resolution failed: {exc}\n")
        for c in exc.candidates:
            sys.stderr.write(f"  candidate: {c.get('path')} ({c.get('name')})\n")
        return 3
    # B-3: catch Orbit subprocess errors and other runtime failures
    # so callers (including agent wrappers) get clean one-line errors
    # and distinct exit codes instead of raw tracebacks.
    except subprocess.TimeoutExpired:
        sys.stderr.write(
            "Error: Orbit CLI timed out. Check GITLAB_TOKEN and network, "
            "or use --graph FIXTURE.json for offline mode.\n"
        )
        return 4
    except RuntimeError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 4
    except Exception as exc:
        sys.stderr.write(f"Error: {type(exc).__name__}: {exc}\n")
        return 4

    if args.json:
        print(json.dumps(_report_to_dict(report), indent=2))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
