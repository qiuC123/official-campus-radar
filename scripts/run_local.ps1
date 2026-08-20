$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    & py -3.13 manage.py migrate --check
    if ($LASTEXITCODE -ne 0) {
        Write-Error '数据库迁移尚未应用。请先运行: py -3.13 manage.py migrate'
        exit 1
    }
    & py -3.13 manage.py runserver 127.0.0.1:8000 --noreload
} finally {
    Pop-Location
}
