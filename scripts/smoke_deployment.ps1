param(
    [string]$StreamlitUrl = "https://visa-synthetic-research-copilot.27cqtktlikeo.eu-de.codeengine.appdomain.cloud",
    [string]$ApiUrl = "https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud",
    [string]$PayloadPath = "demo/api_smoke_payload.json",
    [int]$TimeoutSec = 180
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Assert-HttpOk {
    param(
        [string]$Name,
        [string]$Uri
    )

    $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec $TimeoutSec
    if ($response.StatusCode -ne 200) {
        throw "$Name returned HTTP $($response.StatusCode)"
    }
    Write-Host "$Name OK: HTTP $($response.StatusCode)"
}

Assert-HttpOk -Name "Streamlit cockpit" -Uri $StreamlitUrl

$health = Invoke-RestMethod -Method Get -Uri "$ApiUrl/health" -TimeoutSec $TimeoutSec
if ($health.status -ne "ok") {
    throw "API health failed: $($health | ConvertTo-Json -Compress)"
}
Write-Host "API health OK: $($health.service)"

$payload = Get-Content -Path $PayloadPath -Raw
$run = Invoke-RestMethod -Method Post -Uri "$ApiUrl/run" -ContentType "application/json" -Body $payload -TimeoutSec ($TimeoutSec + 60)
if (-not $run.run_id -or $run.response_count -le 0) {
    throw "API run did not return a valid synthetic research result."
}
if (-not $run.validation.overall.score) {
    throw "API run did not return validation evidence."
}

Write-Host "API run OK: run_id=$($run.run_id), responses=$($run.response_count), validation=$($run.validation.overall.score)"
