from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from app.backends import build_command, select_backend
from app.config import ensure_logs_dir
from app.context import InvocationContext


@dataclass(frozen=True)
class ActionSpec:
    name: str
    commands: list[str] = field(default_factory=list)
    display_lines: list[str] = field(default_factory=list)
    backend: str = 'auto-bash'
    working_directory: Path | None = None
    environment: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 600
    continue_on_error: bool = False


@dataclass(frozen=True)
class RunResult:
    backend_name: str
    command: list[str]
    exit_code: int
    log_path: Path


def run_action(context: InvocationContext, action: ActionSpec) -> RunResult:
    if not action.commands and not action.display_lines:
        raise ValueError('ActionSpec must provide commands or display_lines.')

    working_directory = (action.working_directory or context.working_directory).resolve(strict=False)
    custom_environment = context.to_environment()
    custom_environment.update(action.environment)

    environment = os.environ.copy()
    environment.update(custom_environment)
    backend_name = 'builtin'
    command: list[str] = []

    if action.commands:
        backend = select_backend(action.backend)
        backend_name = backend.name
        command = build_command(
            backend=backend,
            commands=action.commands,
            working_directory=working_directory,
            environment=custom_environment,
            continue_on_error=action.continue_on_error,
        )

    logs_dir = ensure_logs_dir()
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_path = logs_dir / f'{timestamp}-{sanitize_name(action.name)}.log'

    header_lines = [
        f'action={action.name}',
        f'backend={backend_name}',
        f'working_directory={working_directory}',
        f'command={command}',
        '',
    ]
    header_text = '\n'.join(header_lines)

    exit_code = 1
    combined_output = ''

    if action.display_lines:
        combined_output = '\n'.join(action.display_lines)
        if combined_output and not combined_output.endswith('\n'):
            combined_output += '\n'
        exit_code = 0
    else:
        try:
            completed = subprocess.run(
                command,
                cwd=str(working_directory),
                env=environment,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=action.timeout_seconds,
                shell=False,
            )
            stdout = completed.stdout or ''
            stderr = completed.stderr or ''
            combined_output = stdout + stderr
            exit_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ''
            stderr = exc.stderr or ''
            combined_output = f'timeout after {action.timeout_seconds} seconds\n{stdout}{stderr}'
            exit_code = 124

    if combined_output:
        print(combined_output, end='' if combined_output.endswith('\n') else '\n')

    summary_text = f'\nexit_code={exit_code}\nlog_path={log_path}\n'

    with log_path.open('w', encoding='utf-8') as log_file:
        log_file.write(header_text)
        log_file.write(combined_output)
        if combined_output and not combined_output.endswith('\n'):
            log_file.write('\n')
        log_file.write(summary_text)

    return RunResult(
        backend_name=backend_name,
        command=command,
        exit_code=exit_code,
        log_path=log_path,
    )


def sanitize_name(value: str) -> str:
    characters = []
    for character in value.lower():
        if character.isalnum() or character in ('-', '_'):
            characters.append(character)
        else:
            characters.append('-')
    return ''.join(characters).strip('-') or 'action'
