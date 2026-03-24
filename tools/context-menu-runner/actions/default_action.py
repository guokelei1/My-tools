from __future__ import annotations

from app.context import InvocationContext
from app.executor import ActionSpec


def build_action(context: InvocationContext) -> ActionSpec:
    return ActionSpec(
        name='default-action',
        commands=[
            'git add .',
            'git commit -m "new commit"',
            'git push',
        ],
        backend='powershell',
        working_directory=context.working_directory,
        timeout_seconds=1800,
    )
