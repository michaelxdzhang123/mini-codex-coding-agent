"""Safe command runner with output capture and timeout handling."""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from core.commands.audit import ExecutionLog
from core.commands.config import AllowedCommand
from core.commands.guard import CommandGuard


@dataclass
class ExecutionResult:
    """Result of a command execution attempt."""

    command: str
    status: str  # success, failure, denied, timeout
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int
    log_id: str = ""


class SafeCommandRunner:
    """
    Executes approved commands safely.

    Responsibilities:
    1. Validate every command through CommandGuard
    2. Run with timeout
    3. Capture stdout/stderr/exit code
    4. Produce audit logs
    """

    def __init__(self, guard: CommandGuard) -> None:
        self.guard = guard
        self._logs: list[ExecutionLog] = []

    def validate(self, command: str) -> AllowedCommand:
        """Validate a command without running it."""
        return self.guard.validate(command)

    def run(
        self,
        command: str,
        working_dir: str | None = None,
        approved_by: str | None = None,
    ) -> ExecutionResult:
        """
        Validate and run a command.

        Args:
            command: The exact command string to run.
            working_dir: Optional working directory.
            approved_by: User who approved this execution (if applicable).

        Returns:
            ExecutionResult with output and status.
        """
        log = ExecutionLog(
            command=command,
            working_directory=working_dir or "",
            approved_by=approved_by,
        )

        # Validation
        try:
            matched = self.guard.validate(command)
        except ValueError as e:
            log.status = "denied"
            log.details["reason"] = str(e)
            self._logs.append(log)
            return ExecutionResult(
                command=command,
                status="denied",
                stdout="",
                stderr=str(e),
                exit_code=None,
                duration_ms=0,
                log_id=log.id,
            )

        # Determine timeout
        timeout = matched.timeout_seconds
        effective_wd = Path(working_dir) if working_dir else Path.cwd()

        # Execute
        log.status = "running"
        start = time.monotonic()
        try:
            result = subprocess.run(
                shlex.split(command),
                shell=False,
                cwd=effective_wd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = int((time.monotonic() - start) * 1000)

            log.status = "success" if result.returncode == 0 else "failure"
            log.exit_code = result.returncode
            log.stdout = result.stdout
            log.stderr = result.stderr
            log.duration_ms = duration

            self._logs.append(log)
            return ExecutionResult(
                command=command,
                status=log.status,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration,
                log_id=log.id,
            )

        except subprocess.TimeoutExpired as e:
            duration = int((time.monotonic() - start) * 1000)
            log.status = "timeout"
            log.duration_ms = duration
            log.stdout = e.stdout or ""
            log.stderr = e.stderr or ""
            self._logs.append(log)
            return ExecutionResult(
                command=command,
                status="timeout",
                stdout=e.stdout or "",
                stderr=e.stderr or "",
                exit_code=None,
                duration_ms=duration,
                log_id=log.id,
            )

        except Exception as e:
            duration = int((time.monotonic() - start) * 1000)
            log.status = "failure"
            log.duration_ms = duration
            log.details["error"] = str(e)
            self._logs.append(log)
            return ExecutionResult(
                command=command,
                status="failure",
                stdout="",
                stderr=str(e),
                exit_code=None,
                duration_ms=duration,
                log_id=log.id,
            )

    def get_logs(self) -> list[ExecutionLog]:
        return list(self._logs)
