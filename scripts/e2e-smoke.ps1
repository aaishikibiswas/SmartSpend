param(
  [string]$ApiBase = "http://127.0.0.1:8000",
  [string]$SampleFile = "C:\Users\Aaishiki\Desktop\streamlit\sample.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SampleFile)) {
  throw "Sample file not found: $SampleFile"
}

$uploadUri = "$ApiBase/api/parse/upload"
$analyzeUri = "$ApiBase/api/dashboard/analyze"

Write-Host "Uploading sample file to $uploadUri"
$upload = Invoke-RestMethod -Method Post -Uri $uploadUri -Form @{
  file = Get-Item -LiteralPath $SampleFile
}

if (-not $upload.transactions -or $upload.transactions.Count -eq 0) {
  throw "Upload returned no transactions."
}

Write-Host "Parsed transactions:" $upload.transactions.Count
Write-Host "Detected categories:" (($upload.available_categories | Sort-Object) -join ", ")

$payload = @{
  transactions = $upload.transactions
  monthly_budget = 10000
  weekly_budget_amount = 2500
  financial_goals = @()
  bill_reminders = @()
  category_budgets = @{}
  filters = @{
    start_date = $null
    end_date = $null
    categories = @("All")
    projection_months = 6
  }
} | ConvertTo-Json -Depth 8

Write-Host "Posting dashboard analysis to $analyzeUri"
$analysis = Invoke-RestMethod -Method Post -Uri $analyzeUri -ContentType "application/json" -Body $payload

Write-Host "Dashboard has data:" $analysis.has_data
Write-Host "Total expense:" $analysis.metrics.total_expense
Write-Host "Top category:" $analysis.metrics.top_category
Write-Host "Alert count:" $analysis.alerts.Count
Write-Host "Daily chart points:" $analysis.charts.daily_expense.Count

if (-not $analysis.has_data) {
  throw "Dashboard response indicates no data."
}

if (-not $analysis.charts.daily_expense -or $analysis.charts.daily_expense.Count -eq 0) {
  throw "Daily expense chart is empty."
}

Write-Host "Smoke test passed."
