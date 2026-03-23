# proxy-toggle

`proxy-toggle` adds a `proxy` command to PowerShell by updating your PowerShell profile.

## What it does

After installation, you can run:

```powershell
proxy
```

The command toggles these environment variables in the current PowerShell session:

```powershell
$env:HTTP_PROXY = 'http://127.0.0.1:7890'
$env:HTTPS_PROXY = 'http://127.0.0.1:7890'
```

If you run `proxy` again, it removes both variables from the current session.

## Files

- `install-proxy-toggle.ps1`: installs the `proxy` command into your PowerShell profile
- `uninstall-proxy-toggle.ps1`: removes the `proxy` command from your PowerShell profile

## Install

From this folder, run:

```powershell
.\install-proxy-toggle.ps1
```

The script updates your PowerShell profile, reloads it, and makes `proxy` available immediately in that session.

## Use

Run:

```powershell
proxy
```

Behavior:

- first call: enables `HTTP_PROXY` and `HTTPS_PROXY`
- second call: removes `HTTP_PROXY` and `HTTPS_PROXY`

## Uninstall

Run:

```powershell
.\uninstall-proxy-toggle.ps1
```

This removes the injected profile block and unloads the `proxy` function from the current session.

