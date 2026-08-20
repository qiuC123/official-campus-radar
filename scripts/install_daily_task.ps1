param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$taskName = 'OfficialCampusRadarDailyUpdate'
$projectRoot = Split-Path -Parent $PSScriptRoot
$managePy = Join-Path $projectRoot 'manage.py'
$arguments = '-3.13 "{0}" run_daily_update --trigger scheduled' -f $managePy
$action = New-ScheduledTaskAction -Execute 'py.exe' -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Daily -At 22:00
$settings = New-ScheduledTaskSettingsSet -WakeToRun:$false

if (-not $Apply) {
    Write-Host "Dry run only. No task will be registered."
    Write-Host "Task name: $taskName"
    Write-Host "Action: py $arguments"
    Write-Host "Trigger: every day at 22:00"
    Write-Host "Working directory: $projectRoot"
    exit 0
}

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Registered or replaced task: $taskName"
