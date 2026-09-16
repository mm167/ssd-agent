"""Git CLI adapter for `GitRepository` (TASKS T004; PLAN Sections 3.1, 21-24).

`GitCliRepository` shells out to the `git` executable rather than using a
Git library, matching PLAN Section 3.1 ("subprocesses; Git;") and Section 21
("A Git CLI adapter shall provide the V1 implementation").

Candidate computation deliberately avoids the Git index as its source of
truth. `git diff <baseline_sha>` (no `--cached`) compares the baseline tree
directly against the on-disk worktree content, so a file that is staged and
then further edited unstaged is still reported with its final on-disk
content -- exactly the "worktree, not index" guarantee PLAN Section 23
requires. Content identity is computed by hashing the actual file bytes
ourselves (not a Git blob SHA), so tracked and untracked entries share one
uniform, binary-safe content identity.

All Git invocations use NUL-separated (`-z`) machine-readable output and
`--no-renames`, so filenames containing spaces or other unusual valid
characters parse unambiguously and a rename is always reported as a
canonical delete + add pair rather than a single rename record (PLAN
Section 23).
"""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
from pathlib import Path

from sdd_agent.diagnostics.errors import GitOperationError
from sdd_agent.domain.models.candidate import CandidateEntry, CandidateEntryKind, CandidateSnapshot
from sdd_agent.domain.models.git_status import WorktreeStatus
from sdd_agent.ports.git import GitRepository

_IS_WINDOWS = platform.system() == "Windows"

_STATUS_ARGS = (
    "status",
    "--porcelain=v2",
    "-z",
    "--untracked-files=all",
    "--ignored=matching",
    "--no-renames",
)


class GitCliRepository(GitRepository):
    """Concrete V1 `GitRepository` implementation invoking the `git` CLI.

    Every instance is bound to one explicit repository workspace path (PLAN
    Section 79: agent/adapter behavior must not depend on an implicit shell
    current directory).
    """

    def __init__(self, repo_path: Path | str) -> None:
        self._repo_path = Path(repo_path)

    def head_sha(self) -> str:
        return self._run_git(["rev-parse", "HEAD"]).decode("ascii").strip()

    def current_branch(self) -> str | None:
        name = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]).decode(
            "utf-8", errors="replace"
        ).strip()
        return None if name == "HEAD" else name

    def worktree_status(self) -> WorktreeStatus:
        raw = self._run_git(list(_STATUS_ARGS))
        records = raw.decode("utf-8", errors="surrogateescape").split("\x00")

        staged: list[str] = []
        unstaged: list[str] = []
        untracked: list[str] = []
        ignored: list[str] = []

        for record in records:
            if not record:
                continue
            marker = record[0]
            if marker == "1":
                # "1 XY sub mH mI mW hH hI path" (9 space-separated fields;
                # maxsplit keeps a path containing spaces intact).
                parts = record.split(" ", 8)
                xy, path = parts[1], parts[8]
                if xy[0] != ".":
                    staged.append(path)
                if xy[1] != ".":
                    unstaged.append(path)
            elif marker == "u":
                # Unmerged (conflict) entry; conservatively treat as both
                # staged and unstaged. Not a normal V1 workflow state.
                path = record.rsplit(" ", 1)[-1]
                staged.append(path)
                unstaged.append(path)
            elif marker == "?":
                untracked.append(record.split(" ", 1)[1])
            elif marker == "!":
                ignored.append(record.split(" ", 1)[1])
            # marker == "2" (rename/copy) cannot occur: --no-renames.

        return WorktreeStatus(
            staged_paths=tuple(staged),
            unstaged_paths=tuple(unstaged),
            untracked_paths=tuple(untracked),
            ignored_paths=tuple(ignored),
        )

    def candidate_snapshot(self, baseline_sha: str) -> CandidateSnapshot:
        status = self.worktree_status()

        entries: dict[str, CandidateEntry] = {}
        for path in status.untracked_paths:
            entries[path] = self._untracked_entry(path)
        # Tracked changes take precedence on any path collision.
        entries.update(self._tracked_entries(baseline_sha))

        ordered = tuple(entries[path] for path in sorted(entries))
        return CandidateSnapshot(baseline_sha=baseline_sha, entries=ordered)

    def _tracked_entries(self, baseline_sha: str) -> dict[str, CandidateEntry]:
        raw = self._run_git(["diff", "--raw", "-z", "--no-renames", baseline_sha])
        tokens = raw.decode("utf-8", errors="surrogateescape").split("\x00")

        entries: dict[str, CandidateEntry] = {}
        index = 0
        while index < len(tokens):
            meta = tokens[index]
            index += 1
            if not meta:
                continue
            # ":<oldmode> <newmode> <oldsha> <newsha> <status>"
            fields = meta.split(" ")
            new_mode, status_letter = fields[1], fields[4][0]
            path = tokens[index]
            index += 1

            if status_letter == "D":
                entries[path] = CandidateEntry(path=path, kind=CandidateEntryKind.DELETED)
            else:
                kind = (
                    CandidateEntryKind.ADDED
                    if status_letter == "A"
                    else CandidateEntryKind.MODIFIED
                )
                entries[path] = CandidateEntry(
                    path=path,
                    kind=kind,
                    file_mode=new_mode,
                    content_sha256=self._hash_file(self._repo_path / path),
                )
        return entries

    def _untracked_entry(self, path: str) -> CandidateEntry:
        absolute = self._repo_path / path
        return CandidateEntry(
            path=path,
            kind=CandidateEntryKind.ADDED,
            file_mode=self._infer_new_file_mode(absolute),
            content_sha256=self._hash_file(absolute),
        )

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _infer_new_file_mode(path: Path) -> str:
        if _IS_WINDOWS:
            return "100644"
        return "100755" if os.access(path, os.X_OK) else "100644"

    def _run_git(self, args: list[str]) -> bytes:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(self._repo_path),
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitOperationError(
                "git executable not found on PATH", details={"args": args}
            ) from exc

        if result.returncode != 0:
            raise GitOperationError(
                f"git {' '.join(args)} failed with exit code {result.returncode}",
                details={
                    "args": args,
                    "returncode": result.returncode,
                    "stderr": result.stderr.decode("utf-8", errors="replace"),
                },
            )
        return result.stdout
