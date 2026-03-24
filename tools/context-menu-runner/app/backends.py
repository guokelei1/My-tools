from __future__ import annotations

import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ShellBackend:
    name: str
    family: str
    executable: str


def select_backend(preference: str) -> ShellBackend:
    available = discover_backends()

    if preference == 'auto-bash':
        for name in ('bash', 'wsl'):
            backend = available.get(name)
            if backend:
                return backend
        raise RuntimeError('No Bash backend found. Install Git Bash or WSL.')

    if preference == 'auto':
        for name in ('bash', 'wsl', 'powershell'):
            backend = available.get(name)
            if backend:
                return backend
        raise RuntimeError('No supported shell backend found.')

    backend = available.get(preference)
    if backend:
        return backend

    raise RuntimeError(f'Requested backend is not available: {preference}')


def discover_backends() -> dict[str, ShellBackend]:
    backends: dict[str, ShellBackend] = {}

    bash_path = find_bash_executable()
    if bash_path:
        backends['bash'] = ShellBackend(name='bash', family='bash', executable=str(bash_path))

    wsl_path = shutil.which('wsl.exe') or shutil.which('wsl')
    if wsl_path:
        backends['wsl'] = ShellBackend(name='wsl', family='bash', executable=wsl_path)

    powershell_path = shutil.which('powershell.exe') or shutil.which('pwsh')
    if powershell_path:
        backends['powershell'] = ShellBackend(
            name='powershell',
            family='powershell',
            executable=powershell_path,
        )

    return backends


def build_command(
    backend: ShellBackend,
    commands: list[str],
    working_directory: Path,
    environment: dict[str, str],
    continue_on_error: bool,
) -> list[str]:
    if backend.family == 'bash':
        script = build_bash_script(
            backend=backend,
            commands=commands,
            working_directory=working_directory,
            environment=environment,
            continue_on_error=continue_on_error,
        )

        if backend.name == 'wsl':
            return [backend.executable, 'bash', '-lc', script]

        return [backend.executable, '-lc', script]

    if backend.family == 'powershell':
        script = build_powershell_script(
            commands=commands,
            working_directory=working_directory,
            environment=environment,
            continue_on_error=continue_on_error,
        )
        return [backend.executable, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script]

    raise RuntimeError(f'Unsupported backend family: {backend.family}')


def build_bash_script(
    backend: ShellBackend,
    commands: list[str],
    working_directory: Path,
    environment: dict[str, str],
    continue_on_error: bool,
) -> str:
    lines: list[str] = []

    if not continue_on_error:
        lines.append('set -e')

    if backend.name == 'wsl':
        shell_path = to_wsl_path(working_directory)
    else:
        shell_path = to_git_bash_path(working_directory)

    lines.append(f'cd {shlex.quote(shell_path)}')
    lines.extend(commands)
    return '\n'.join(lines)


def build_powershell_script(
    commands: list[str],
    working_directory: Path,
    environment: dict[str, str],
    continue_on_error: bool,
) -> str:
    lines: list[str] = []
    lines.append("$ErrorActionPreference = 'Continue'" if continue_on_error else "$ErrorActionPreference = 'Stop'")

    escaped_working_directory = str(working_directory).replace("'", "''")
    lines.append(f"Set-Location -LiteralPath '{escaped_working_directory}'")
    lines.extend(commands)
    return '; '.join(lines)


def find_bash_executable() -> Path | None:
    candidates: list[str] = []

    for env_name in ('ProgramW6432', 'ProgramFiles', 'ProgramFiles(x86)', 'LocalAppData'):
        base_path = os.environ.get(env_name)
        if not base_path:
            continue

        candidates.extend(
            [
                str(Path(base_path) / 'Git' / 'bin' / 'bash.exe'),
                str(Path(base_path) / 'Git' / 'usr' / 'bin' / 'bash.exe'),
                str(Path(base_path) / 'Programs' / 'Git' / 'bin' / 'bash.exe'),
            ]
        )

    which_bash = shutil.which('bash.exe') or shutil.which('bash')
    if which_bash and not is_windows_legacy_bash(which_bash):
        candidates.append(which_bash)

    seen: set[str] = set()
    for candidate in candidates:
        normalized_candidate = os.path.normcase(candidate)
        if normalized_candidate in seen:
            continue
        seen.add(normalized_candidate)

        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path

    return None


def is_windows_legacy_bash(executable: str) -> bool:
    normalized = os.path.normcase(str(Path(executable)))
    return normalized == os.path.normcase(r'C:\Windows\System32\bash.exe')


def to_git_bash_path(path: Path) -> str:
    resolved_path = path.resolve(strict=False)
    posix_path = resolved_path.as_posix()

    if resolved_path.drive:
        drive = resolved_path.drive.rstrip(':').lower()
        return f'/{drive}{posix_path[2:]}'

    return posix_path


def to_wsl_path(path: Path) -> str:
    resolved_path = path.resolve(strict=False)
    posix_path = resolved_path.as_posix()

    if resolved_path.drive:
        drive = resolved_path.drive.rstrip(':').lower()
        return f'/mnt/{drive}{posix_path[2:]}'

    return posix_path
