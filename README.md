# My-tools

Personal utility repository for small tools and automation scripts.

This repo is meant to grow over time. Each tool lives in its own folder with its own README so it can be installed, used, and removed independently.

## Structure

- `tools/shortcut-cd/`: PowerShell enhancement that lets `cd` jump into Windows folder shortcuts like `codex.lnk` without manually typing `.lnk`
- `tools/proxy-toggle/`: PowerShell enhancement that adds a `proxy` command to toggle local proxy environment variables

## Current tools

### `shortcut-cd`

Adds shortcut-aware navigation to PowerShell:

- `cd codex`
- `cd .\codex`

If a real folder is not found, it automatically tries:

- `codex.lnk`
- `codex.link`

See `tools/shortcut-cd/README.md` for installation and removal.

### `proxy-toggle`

Adds a `proxy` command to PowerShell:

- first call sets `HTTP_PROXY` to `http://127.0.0.1:7890`
- first call sets `HTTPS_PROXY` to `http://127.0.0.1:7890`
- second call removes both variables from the current session

See `tools/proxy-toggle/README.md` for installation and removal.

## Notes

- Tools are designed to stay loosely coupled
- Each tool should provide its own install and uninstall path
- Future tools can be added under `tools/<tool-name>/`
