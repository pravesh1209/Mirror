# MIRROR pre-pitch smoke test.
# Verifies the entire backend loop without touching a browser.

$ErrorActionPreference = "Stop"
$base = "http://localhost:8000"

function Check($name, $script) {
    try {
        & $script | Out-Null
        Write-Host "  [OK]   $name" -ForegroundColor Green
    } catch {
        Write-Host "  [FAIL] $name -- $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "MIRROR smoke test" -ForegroundColor Cyan
Write-Host "-----------------"

# 1. Backend up
Check "GET /api/health" {
    $r = Invoke-RestMethod "$base/api/health" -TimeoutSec 3
    if ($r.status -ne "ok") { throw "status != ok" }
}

# 2. Status
Check "GET /api/status" {
    $r = Invoke-RestMethod "$base/api/status" -TimeoutSec 3
    if ($r.db -ne "ok") { throw "db != ok" }
}

# 3. Session
$sess = Invoke-RestMethod -Method Post -Uri "$base/api/sessions" `
    -ContentType "application/json" -Body '{"mode":"live"}'
Check "POST /api/sessions" {
    if (-not $sess.session_id) { throw "no session_id" }
}

# 4. Scenario
$sc = (Invoke-RestMethod -Method Post -Uri "$base/api/scenarios/generate" `
    -ContentType "application/json" `
    -Body (@{ session_id = $sess.session_id; use_bank_only = $true } | ConvertTo-Json)).scenario
Check "POST /api/scenarios/generate" {
    if (-not $sc.id) { throw "no scenario id" }
    if ($sc.options.Count -lt 2) { throw "fewer than 2 options" }
}

# 5. Events
$opt = $sc.options[0]
$events = @{
    session_id = $sess.session_id
    events = @(
        @{ event_id = [guid]::NewGuid().ToString("N"); event_type = "scenario_started";    option_id = $null;   payload = @{}; relative_time_ms = 0 },
        @{ event_id = [guid]::NewGuid().ToString("N"); event_type = "option_viewed";      option_id = $opt.id; payload = @{}; relative_time_ms = 500 },
        @{ event_id = [guid]::NewGuid().ToString("N"); event_type = "decision_submitted"; option_id = $opt.id; payload = @{}; relative_time_ms = 2000 },
        @{ event_id = [guid]::NewGuid().ToString("N"); event_type = "scenario_completed"; option_id = $null;   payload = @{}; relative_time_ms = 2000 }
    )
} | ConvertTo-Json -Depth 6

Check "POST /events" {
    $r = Invoke-RestMethod -Method Post -Uri "$base/api/scenarios/$($sc.id)/events" `
        -ContentType "application/json" -Body $events
    if ($r.accepted -ne 4) { throw "accepted=$($r.accepted), expected 4" }
}

# 6. Decision
Check "POST /decision" {
    $r = Invoke-RestMethod -Method Post -Uri "$base/api/scenarios/$($sc.id)/decision" `
        -ContentType "application/json" `
        -Body (@{ session_id = $sess.session_id; final_option_id = $opt.id } | ConvertTo-Json)
    if ($r.profile_version -lt 1) { throw "no profile version" }
}

# 7. Fingerprint
Check "GET /fingerprint" {
    $r = Invoke-RestMethod "$base/api/profile/$($sess.user_id)/fingerprint"
    if ($r.sample_count -lt 1) { throw "sample_count < 1" }
}

# 8. Stats
Check "GET /stats" {
    Invoke-RestMethod "$base/api/profile/$($sess.user_id)/stats" | Out-Null
}

# 9. Demo seed
Check "POST /demo/seed" {
    $r = Invoke-RestMethod -Method Post -Uri "$base/api/demo/seed"
    if ($r.decisions -lt 5) { throw "demo produced only $($r.decisions) decisions" }
}

# 10. Timeline
$demoUid = (Invoke-RestMethod -Method Post -Uri "$base/api/demo/seed").user_id
Check "GET /timeline" {
    $r = Invoke-RestMethod "$base/api/model/timeline?user_id=$demoUid"
    if ($r.entries.Count -lt 3) { throw "expected >=3 timeline entries, got $($r.entries.Count)" }
}

# 11. Blind spots
Check "POST /blind-spots/analyze" {
    $r = Invoke-RestMethod -Method Post -Uri "$base/api/blind-spots/analyze" `
        -ContentType "application/json" `
        -Body (@{ user_id = $demoUid } | ConvertTo-Json)
    if (-not $r.known -or -not $r.unknown) { throw "missing known/unknown" }
}

# 12. Cleanup
Check "POST /demo/reset" {
    Invoke-RestMethod -Method Post -Uri "$base/api/demo/reset" | Out-Null
}

Write-Host ""
Write-Host "All checks passed." -ForegroundColor Green
Write-Host ""