$ErrorActionPreference = 'Stop'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$reportRoot = Join-Path $projectRoot 'reports'
$docker = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
& $docker build -f (Join-Path $projectRoot 'infra\reports.Dockerfile') -t creditsoft-report-renderer $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Report renderer build failed' }
& $docker run --rm --network none --mount "type=bind,source=$reportRoot,target=/reports" --mount 'type=bind,source=C:\Windows\Fonts,target=/usr/local/share/fonts/windows,readonly' creditsoft-report-renderer /reports/Lab_5.docx /reports/Lab_6.docx /reports/Lab_7.docx /reports/Lab_8.docx
if ($LASTEXITCODE -ne 0) { throw 'Report PDF rendering failed' }
