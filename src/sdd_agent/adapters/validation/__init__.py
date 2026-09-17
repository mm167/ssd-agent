"""Concrete `ValidationRunner` implementations (TASKS T006; PLAN Section 30).

`SubprocessValidationRunner` is the concrete V1 execution adapter.
`FakeValidationRunner` is the deterministic test double mandated by PLAN
Section 97 for Core tests that must not depend on real command execution.
"""

from sdd_agent.adapters.validation.fake import FakeValidationRunner
from sdd_agent.adapters.validation.subprocess_runner import SubprocessValidationRunner

__all__ = [
    "FakeValidationRunner",
    "SubprocessValidationRunner",
]
