param(
    [string]$KeyPath = "$env:USERPROFILE\.radar-preview\ecs-20260905\id_ed25519",
    [string]$KnownHostsPath = "$env:USERPROFILE\.radar-preview\ecs-20260905\known_hosts"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $KeyPath) -or -not (Test-Path -LiteralPath $KnownHostsPath)) {
    throw "Missing dedicated preview key or verified server host key."
}
Write-Host "Open http://127.0.0.1:18765 while this encrypted tunnel is running. Ctrl+C closes it."
& ssh.exe -N -T -i $KeyPath -o "UserKnownHostsFile=$KnownHostsPath" -o StrictHostKeyChecking=yes -o IdentitiesOnly=yes -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:18765:127.0.0.1:8765 radar-tunnel@112.125.89.240
exit $LASTEXITCODE
