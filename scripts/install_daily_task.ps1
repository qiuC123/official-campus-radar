param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$taskName = 'OfficialCampusRadarDailyUpdate'
$projectRoot = Split-Path -Parent $PSScriptRoot
$managePy = Join-Path $projectRoot 'manage.py'
$pythonLauncher = (Get-Command 'py.exe' -ErrorAction Stop).Source
$arguments = '-3.13 "{0}" run_daily_update --trigger scheduled' -f $managePy
$action = New-ScheduledTaskAction -Execute $pythonLauncher -Argument $arguments -WorkingDirectory $projectRoot
$scheduleTimes = @('12:00', '20:00')
$triggers = @(
    foreach ($scheduleTime in $scheduleTimes) {
        New-ScheduledTaskTrigger -Daily -At $scheduleTime
    }
)
$settings = New-ScheduledTaskSettingsSet `
    -WakeToRun:$false `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

if (-not $Apply) {
    Write-Host "Dry run only. No task will be registered."
    Write-Host "Task name: $taskName"
    Write-Host "Action: $pythonLauncher $arguments"
    Write-Host "Triggers: every day at 12:00 and 20:00"
    Write-Host "Missed start: run when the computer is next available"
    Write-Host "Overlap policy: ignore a new trigger while the task is running"
    Write-Host "Working directory: $projectRoot"
    exit 0
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Description 'Refresh admitted official recruitment sources at 12:00 and 20:00.' `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Force | Out-Null
Write-Host "Registered or replaced task: $taskName"
