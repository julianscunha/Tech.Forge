"""
Install Job Registry — Fase 11 Slice 5b §11/§12
================================================
In-memory registry for tracking remote module installation progress.

Job lifecycle:
  1. create(module_id) → ACQUIRING phase, generated job_id
  2. set_phase(job_id, phase, error=None) → advance phase
  3. get(job_id) → query current state

Finished phases (DONE/FAILED) have finished_at timestamp.
Intermediate phases (ACQUIRING/VALIDATING/INSTALLING) do not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class InstallJobPhase(str, Enum):
    """Installation job phase progression."""
    ACQUIRING    = "ACQUIRING"     # Downloading/fetching from remote source
    VALIDATING   = "VALIDATING"    # Validating .mod file integrity
    INSTALLING   = "INSTALLING"    # Installing to modules/installed/
    DONE         = "DONE"          # Success
    FAILED       = "FAILED"        # Error; see error message


@dataclass
class InstallJob:
    """Single installation job state."""
    job_id:       str
    module_id:    str
    phase:        InstallJobPhase
    error:        Optional[str] = None
    started_at:   datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at:  Optional[datetime] = None


class InstallJobRegistry:
    """
    In-memory, singleton, non-persistent registry of installation jobs.

    Same pattern as ModuleRuntimeRegistry (module_runtime/state.py):
    - Reconstruible (ephemeral state, cleared on shutdown)
    - Indexed by job_id
    - Thread-safe operations (Python GIL protects dict operations)
    """

    def __init__(self) -> None:
        self._jobs: dict[str, InstallJob] = {}

    def create(self, module_id: str) -> InstallJob:
        """
        Create a new installation job in ACQUIRING phase.

        Returns the InstallJob with a generated 12-character job_id.
        """
        job_id = uuid4().hex[:12]
        job = InstallJob(
            job_id=job_id,
            module_id=module_id,
            phase=InstallJobPhase.ACQUIRING,
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[InstallJob]:
        """Retrieve a job by ID, or None if not found."""
        return self._jobs.get(job_id)

    def set_phase(
        self,
        job_id: str,
        phase: InstallJobPhase,
        error: Optional[str] = None,
    ) -> None:
        """
        Advance a job to a new phase.

        Sets finished_at only when phase is DONE or FAILED.
        Sets error message if provided (usually for FAILED).
        Does nothing if job_id does not exist (idempotent).
        """
        job = self._jobs.get(job_id)
        if job is None:
            return

        job.phase = phase
        if error is not None:
            job.error = error

        # Set finished_at only for terminal phases
        if phase in (InstallJobPhase.DONE, InstallJobPhase.FAILED):
            job.finished_at = datetime.now(timezone.utc)


# ── Singleton instance ─────────────────────────────────────────────────────────

install_job_registry = InstallJobRegistry()
