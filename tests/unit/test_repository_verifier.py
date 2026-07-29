from __future__ import annotations

import io
import tarfile
from pathlib import Path

from swarmcore_repository_verifier.main import execute_verification, extract_repository


def _archive(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, mode="w:gz") as bundle:
        for name, content in files.items():
            info = tarfile.TarInfo(name=f"owner-repository/{name}")
            info.size = len(content)
            bundle.addfile(info, io.BytesIO(content))


def test_extract_repository_accepts_single_safe_root(tmp_path: Path) -> None:
    archive = tmp_path / "repository.tar.gz"
    _archive(archive, {"README.md": b"real repository snapshot"})

    root = extract_repository(archive, tmp_path / "workspace")

    assert root.name == "owner-repository"
    assert (root / "README.md").read_bytes() == b"real repository snapshot"


def test_execute_verification_returns_real_command_exit_code(tmp_path: Path) -> None:
    archive = tmp_path / "repository.tar.gz"
    _archive(archive, {"module.py": b"answer = 42\n"})

    exit_code = execute_verification(
        archive,
        tmp_path / "workspace",
        ["python", "-m", "compileall", "-q", "."],
        timeout_seconds=30,
    )

    assert exit_code == 0
