param(
    [switch]$VerboseOutput
)

$ErrorActionPreference = "Stop"

$pytestCmd = "pytest -q --disable-warnings --maxfail=1 --cov=src/lucy --cov-report=term-missing"

Write-Host "Running: $pytestCmd" -ForegroundColor Cyan

try {
    $proc = Start-Process -FilePath "powershell" -ArgumentList "-NoProfile -Command $pytestCmd" -Wait -PassThru -WindowStyle Hidden
    if ($proc.ExitCode -ne 0) {
        Write-Host "Tests failed with exit code $($proc.ExitCode)" -ForegroundColor Red
        exit $proc.ExitCode
    }
    Write-Host "Tests passed. Coverage summary above." -ForegroundColor Green
}
catch {
    Write-Host "Error running tests: $_" -ForegroundColor Red
    exit 1
}