from __future__ import annotations

import argparse
import os
import re
import subprocess
import tarfile
from pathlib import Path

_SAFE_ENVIRONMENT_KEYS = (
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONPATH",
    "PYTHONUTF8",
    "TZ",
)


def extract_repository(archive: Path, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, mode="r:gz") as bundle:
        bundle.extractall(workspace, filter="data")
    roots = [item for item in workspace.iterdir() if item.is_dir()]
    if len(roots) != 1:
        raise ValueError("repository archive must contain exactly one root directory")
    return roots[0]


def execute_verification(
    archive: Path,
    workspace: Path,
    command: list[str],
    *,
    timeout_seconds: int,
) -> int:
    if not command:
        raise ValueError("verification command is required")
    repository = extract_repository(archive, workspace)
    environment = {
        key: value
        for key in _SAFE_ENVIRONMENT_KEYS
        if (value := os.environ.get(key)) is not None
    }
    environment.update(
        {
            "CI": "true",
            "HOME": "/tmp/swarmcore-home",
            "NO_PROXY": "*",
            "PIP_NO_INDEX": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    completed = subprocess.run(
        command,
        cwd=repository,
        env=environment,
        check=False,
        timeout=timeout_seconds,
        shell=False,
    )
    return completed.returncode


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--workspace", type=Path, default=Path("/workspace"))
    parser.add_argument("--timeout-seconds", type=int, default=540)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def run() -> None:
    arguments = _parser().parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", arguments.commit_sha) is None:
        raise ValueError("commit SHA must be a full lowercase Git SHA")
    command = list(arguments.command)
    if command and command[0] == "--":
        command = command[1:]
    raise SystemExit(
        execute_verification(
            arguments.archive,
            arguments.workspace,
            command,
            timeout_seconds=arguments.timeout_seconds,
        )
    )


if __name__ == "__main__":
    run()
