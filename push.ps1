# CHRS - Quick Git Push Script
# Usage:  .\push.ps1                  → auto-generates commit message
#         .\push.ps1 "your message"   → uses your custom message

param([string]$msg)

Set-Location $PSScriptRoot

if (-not $msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $msg = "update: $timestamp"
}

Write-Host "`n🔄  Staging all changes..." -ForegroundColor Cyan
git add -A

Write-Host "📝  Committing: $msg" -ForegroundColor Yellow
git commit -m $msg

Write-Host "🚀  Pushing to GitHub..." -ForegroundColor Green
git push origin master

Write-Host "`n✅  Done! Changes pushed to GitHub.`n" -ForegroundColor Green
