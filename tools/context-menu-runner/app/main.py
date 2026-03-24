from __future__ import annotations

import argparse
import importlib.util
import sys
import traceback
from pathlib import Path

INSTALL_ROOT = Path(__file__).resolve().parent.parent

if str(INSTALL_ROOT) not in sys.path:
    sys.path.insert(0, str(INSTALL_ROOT))

from app.config import APP_NAME, get_default_action_path
from app.context import InvocationContext
from app.executor import ActionSpec, run_action


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument('--mode', required=True, choices=['directory', 'background', 'file', 'multi'])
    parser.add_argument('--target', required=True)
    return parser.parse_args(argv)


def load_action_builder(action_path: Path):
    spec = importlib.util.spec_from_file_location('context_menu_runner_action', action_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load action module: {action_path}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build_action = getattr(module, 'build_action', None)

    if build_action is None:
        raise RuntimeError(f'Action module must define build_action(context): {action_path}')

    return build_action


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    context = InvocationContext.create(
        invocation_type=args.mode,
        target_path=args.target,
        install_root=INSTALL_ROOT,
        raw_args=list(argv or sys.argv[1:]),
    )

    action_path = get_default_action_path()
    build_action = load_action_builder(action_path)
    action = build_action(context)

    if not isinstance(action, ActionSpec):
        raise TypeError(f'build_action() must return ActionSpec, got: {type(action)!r}')

    result = run_action(context, action)
    return result.exit_code


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
