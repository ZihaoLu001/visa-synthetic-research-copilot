param(
    [string]$ApiUrl = "https://visa-synthetic-research-api.27cqtktlikeo.eu-de.codeengine.appdomain.cloud",
    [string]$SurveyDir = "demo/external_survey_tests",
    [int]$MicroPopulation = 24,
    [int]$ConsistencyRuns = 2,
    [int]$TimeoutSec = 240
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$surveyFiles = Get-ChildItem -Path $SurveyDir -Filter "*.txt" | Sort-Object Name
if (-not $surveyFiles) {
    throw "No external survey test files found in $SurveyDir"
}

$results = @()
foreach ($file in $surveyFiles) {
    $surveyText = [System.IO.File]::ReadAllText($file.FullName)
    $payload = @{
        survey_text = $surveyText
        micro_population_n = $MicroPopulation
        consistency_runs = $ConsistencyRuns
        response_mode = "summary"
    } | ConvertTo-Json -Depth 6

    Write-Host "Running external survey test: $($file.Name)"
    $run = Invoke-RestMethod -Method Post -Uri "$ApiUrl/run" -ContentType "application/json" -Body $payload -TimeoutSec $TimeoutSec

    if (-not $run.run_id -or $run.response_count -le 0) {
        throw "$($file.Name) did not return a valid run."
    }
    if ($run.questions.Count -lt 4) {
        throw "$($file.Name) parsed too few questions: $($run.questions.Count)"
    }
    if (-not $run.validation.overall.score) {
        throw "$($file.Name) did not return validation evidence."
    }

    $results += [pscustomobject]@{
        file = $file.Name
        run_id = $run.run_id
        questions = $run.questions.Count
        responses = $run.response_count
        validation_score = $run.validation.overall.score
        coverage_score = $run.validation.question_coverage.score
        json_parse_success_rate = $run.aggregate.runtime.json_parse_success_rate
    }
}

$results | Format-Table -AutoSize
