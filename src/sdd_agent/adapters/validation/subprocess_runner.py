"""Subprocess `ValidationRunner` adapter (TASKS T006; PLAN Sections 3.1, 30,
33, 37, 80, 87).

`SubprocessValidationRunner` executes `ValidationObligation.execution_reference`
as an argv command (split via `_split_command`, never a shell string) and
translates the outcome into exactly the three SPEC Section 19 statuses:

- exit code 0                                -> PASSED
- the process ran and returned non-zero      -> FAILED
- the command could not even run/complete    -> NOT_RUN, with a diagnostic

The last case deliberately covers two named PLAN Section 33 diagnostics --
"missing executable" (`FileNotFoundError`) and "timeout" (a bounded, PLAN
Section 80/81 configurable wait) -- and represents them as a structured
`ValidationResult` rather than raising, because SPEC Sections 20/22 require
these to flow through problem classification and waiver eligibility as
workflow data, not as an unhandled technical exception. This is the opposite
choice from `sdd_agent.adapters.git.cli.GitCliRepository`, which raises
`GitOperationError` for a missing `git` executable: a missing Git binary
means the tool itself cannot function at all, whereas a missing *validation*
command is exactly the ENVIRONMENT-caused NOT_RUN case SPEC Section 22.2
exists to let a human waive. Any other, genuinely unexpected `OSError` is not
one of those two named cases and is raised as
`sdd_agent.diagnostics.errors.ValidationExecutionError` (PLAN Section 87)
instead of being silently absorbed into a soft result.

Raw stdout/stderr are never embedded in the returned `ValidationResult`
(PLAN Section 37: "Large command logs shall not be embedded directly into
the primary workflow state"). When `evidence_dir` is configured, they are
written to a separate JSON file and `ValidationResult.evidence_reference` is
set to its path; that sidecar dict is screened with this repository's
existing secret detectors (`sdd_agent.configuration.secrets`, already applied
to `.sdd/` writes by T003) before being written. This is a best-effort,
structural check reusing the detectors this codebase already has -- it is
not a general-purpose secret scrubber for arbitrary command output, which is
out of a generic runner's scope.

T006-IR-003 correction: that sidecar-file screening alone was insufficient,
because it only ran when `evidence_dir` was configured -- a credential
embedded in `obligation.execution_reference` (e.g. a URL with an embedded
password) could still reach the *returned* `ValidationResult` itself
regardless of `evidence_dir`. The same detectors are therefore also applied
to every field of the `ValidationResult` about to be returned,
unconditionally, via the shared `_reject_secrets` helper -- one rule, applied
at both boundaries (the optional sidecar file and the always-returned
result), never two inconsistent rulesets. Detection reports only the
offending field *path*, never the secret value itself, and nothing is
written or returned once a secret is detected.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from sdd_agent.configuration.secrets import find_secret_like_keys, find_secret_like_values
from sdd_agent.diagnostics.errors import ValidationExecutionError
from sdd_agent.domain.models.enums import ValidationStatus
from sdd_agent.domain.models.identity import EvidenceContext
from sdd_agent.domain.models.validation import ValidationObligation, ValidationResult
from sdd_agent.ports.validation import ValidationRunner

_DEFAULT_TIMEOUT_SECONDS = 600.0


def _split_command(command: str) -> list[str]:
    """Split `command` into argv, preserving Windows path backslashes.

    `shlex.split(..., posix=True)` (the default) treats `\\` as a POSIX
    escape character, silently corrupting a Windows path such as
    `C:\\...\\python.exe` into `C:...python.exe`. `posix=False` preserves
    backslashes but leaves each token's surrounding quote characters intact
    (e.g. `'"raise SystemExit(0)"'`), so those are stripped explicitly here.
    This intentionally does not attempt full shell-grammar support (pipes,
    `&&`, embedded/partial quoting) -- TASKS Section "Explicit Exclusions"
    scopes this to a generic runner, not a shell interpreter.
    """
    return [_strip_matching_quotes(token) for token in shlex.split(command, posix=False)]


def _strip_matching_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    return token


class SubprocessValidationRunner(ValidationRunner):
    """Concrete V1 `ValidationRunner`, executing obligations as subprocesses.

    Every instance is bound to an explicit working directory (PLAN Section
    79: behavior must not depend on an implicit shell current directory).
    """

    def __init__(
        self,
        cwd: Path | str,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        evidence_dir: Path | str | None = None,
    ) -> None:
        self._cwd = Path(cwd)
        self._timeout_seconds = timeout_seconds
        self._evidence_dir = Path(evidence_dir) if evidence_dir is not None else None

    def run(
        self,
        obligation: ValidationObligation,
        context: EvidenceContext,
        *,
        result_id: str,
    ) -> ValidationResult:
        args = _split_command(obligation.execution_reference)
        started_at = datetime.now(timezone.utc)
        start = time.monotonic()

        status: ValidationStatus
        exit_code: int | None = None
        stdout = ""
        stderr = ""
        diagnostic: str | None = None

        try:
            completed = subprocess.run(
                args,
                cwd=str(self._cwd),
                capture_output=True,
                timeout=self._timeout_seconds,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            status = ValidationStatus.NOT_RUN
            diagnostic = f"missing executable: {exc}"
        except subprocess.TimeoutExpired as exc:
            status = ValidationStatus.NOT_RUN
            diagnostic = f"timeout after {self._timeout_seconds}s"
            stdout = _decode(exc.stdout)
            stderr = _decode(exc.stderr)
        except OSError as exc:
            # execution_reference is deliberately not included in this
            # exception's details: it may be credential-bearing (T006-IR-003)
            # and this path is a genuinely unexpected technical failure, not
            # one of the two named NOT_RUN diagnostics that are otherwise
            # safe to retain as evidence.
            raise ValidationExecutionError(
                f"unexpected error executing obligation {obligation.obligation_id!r}: {exc}",
                details={"obligation_id": obligation.obligation_id},
            ) from exc
        else:
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            status = ValidationStatus.PASSED if exit_code == 0 else ValidationStatus.FAILED

        duration_seconds = time.monotonic() - start
        completed_at = datetime.now(timezone.utc)

        evidence_reference = self._write_evidence(
            result_id=result_id,
            obligation=obligation,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration_seconds,
            diagnostic=diagnostic,
        )

        result = ValidationResult(
            result_id=result_id,
            obligation_id=obligation.obligation_id,
            context=context,
            status=status,
            execution_reference=obligation.execution_reference,
            exit_code=exit_code,
            started_at=started_at,
            completed_at=completed_at,
            evidence_reference=evidence_reference,
        )
        _reject_secrets(result.model_dump(mode="json"), action="return validation evidence for")
        return result

    def _write_evidence(
        self,
        *,
        result_id: str,
        obligation: ValidationObligation,
        exit_code: int | None,
        stdout: str,
        stderr: str,
        duration_seconds: float,
        diagnostic: str | None,
    ) -> str | None:
        if self._evidence_dir is None:
            return None

        data = {
            "obligation_id": obligation.obligation_id,
            "execution_reference": obligation.execution_reference,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": duration_seconds,
            "diagnostic": diagnostic,
        }
        _reject_secrets(data, action="persist validation evidence for")

        self._evidence_dir.mkdir(parents=True, exist_ok=True)
        path = self._evidence_dir / f"{result_id}.json"
        tmp_path = path.with_name(f".{path.name}.tmp")
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
        return str(path)


def _decode(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _reject_secrets(data: dict[str, object], *, action: str) -> None:
    """Raise if `data` contains a secret-shaped key or credential-bearing
    value, reusing this repository's one existing detector set (T001) so the
    sidecar-evidence-file check and the always-applied returned-result check
    (T006-IR-003) share a single rule rather than two inconsistent ones.

    The raised message and `details` carry only the offending field *paths*,
    never the secret value itself.
    """
    offending_keys = sorted(find_secret_like_keys(data))
    offending_values = sorted(find_secret_like_values(data))
    if not offending_keys and not offending_values:
        return

    messages = []
    if offending_keys:
        messages.append("secret-like key(s): " + ", ".join(offending_keys))
    if offending_values:
        messages.append("credential-bearing value(s) at: " + ", ".join(offending_values))

    raise ValidationExecutionError(
        f"Refusing to {action} data that appears to contain secrets: " + "; ".join(messages),
        details={"offending_keys": offending_keys, "offending_values": offending_values},
    )
