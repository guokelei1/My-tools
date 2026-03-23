# shortcut-cd

`shortcut-cd` is a small PowerShell utility that makes `cd` understand Windows folder shortcuts.

## What it does

After installation, PowerShell will:

1. Try normal `cd` behavior first
2. If no real directory is found, automatically try `<name>.lnk`
3. Also try `<name>.link`
4. If the shortcut points to a folder, jump into that target folder

This means you can type:

```powershell
cd codex
```

instead of:

```powershell
cd .\codex.lnk
```

## Files

- `install-shortcut-cd.ps1`: installs the PowerShell profile hook
- `uninstall-shortcut-cd.ps1`: removes the hook and restores default behavior

## Install

From this folder, run:

```powershell
.\install-shortcut-cd.ps1
```

The script updates your PowerShell profile and adds shortcut-aware behavior for:

- `cd`
- `sl`
- `chdir`

## Use

Examples:

```powershell
cd codex
cd .\codex
sl my-folder-shortcut
```

If `codex` is not a real folder, PowerShell will automatically check for:

- `codex.lnk`
- `codex.link`

## Uninstall

Run:

```powershell
.\uninstall-shortcut-cd.ps1
```

This removes the injected block from your PowerShell profile and restores the aliases to `Set-Location`.

## Scope

- Works in `PowerShell`
- Intended for folder shortcuts
- Does not change Windows Explorer behavior
