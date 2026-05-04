param(
    [string]$AppName = "visa-synthetic-research-copilot",
    [string]$ProjectName = "",
    [string]$ResourceGroup = "watsonx_Challenge_2026_Students",
    [string]$Region = "eu-de",
    [ValidateSet("streamlit", "api")]
    [string]$Mode = "streamlit"
)

$ErrorActionPreference = "Stop"

function Require-Command($Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Missing required command '$Name'. Install it first, then rerun this script."
    }
}

Require-Command "ibmcloud"

if (-not $ProjectName) {
    throw "Pass -ProjectName with the Code Engine project name assigned to Group 28 / Visa."
}

ibmcloud target -r $Region
ibmcloud target -g $ResourceGroup
ibmcloud ce project select --name $ProjectName

ibmcloud ce application create `
    --name $AppName `
    --build-source . `
    --port 8080 `
    --env MODEL_PROVIDER=mock `
    --env APP_MODE=$Mode

ibmcloud ce application get --name $AppName
