"""Performance Testing Script for Phase 8"""
# Run comprehensive API performance tests

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PHASE 8: PERFORMANCE & STRESS TESTING                   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$results = @{}

# Test 1: Full List Performance (100 scripts)
Write-Host "📊 Test 1: Full List Query (page_size=100)" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?page_size=100"
$stopwatch.Stop()
$results['full_list'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Scripts Returned: $($response.scripts.Count)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 2: Category Filtering
Write-Host "📊 Test 2: Category Filtering (category=weather)" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?category=weather&amp;page_size=100"
$stopwatch.Stop()
$results['filter_category'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Scripts Returned: $($response.scripts.Count)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 3: DJ Filtering
Write-Host "📊 Test 3: DJ Filtering (dj=Julie)" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?dj=Julie&amp;page_size=100"
$stopwatch.Stop()
$results['filter_dj'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Scripts Returned: $($response.scripts.Count)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 4: Status Filtering
Write-Host "📊 Test 4: Status Filtering (status=pending)" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?status=pending&amp;page_size=100"
$stopwatch.Stop()
$results['filter_status'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Scripts Returned: $($response.scripts.Count)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 5: Combined Filters
Write-Host "📊 Test 5: Combined Filters (dj=Julie, category=weather, status=pending)" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?dj=Julie&amp;category=weather&amp;status=pending&amp;page_size=100"
$stopwatch.Stop()
$results['filter_combined'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Scripts Returned: $($response.scripts.Count)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 6: Statistics Endpoint
Write-Host "📊 Test 6: Statistics Endpoint" -ForegroundColor Yellow
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/statistics"
$stopwatch.Stop()
$results['statistics'] = $stopwatch.ElapsedMilliseconds
Write-Host "   Response Time: $($stopwatch.ElapsedMilliseconds)ms"
Write-Host "   Total Scripts: $($response.overview.total)"
if ($stopwatch.ElapsedMilliseconds -lt 500) {
    Write-Host "   ✅ PASS (< 500ms target)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (>= 500ms)`n" -ForegroundColor Yellow
}

# Test 7: Repeated Queries (Cache Test)
Write-Host "📊 Test 7: Repeated Queries (10x full list - cache test)" -ForegroundColor Yellow
$times = @()
for ($i = 1; $i -le 10; $i++) {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/scripts?page_size=100"
    $stopwatch.Stop()
    $times += $stopwatch.ElapsedMilliseconds
}
$avg = ($times | Measure-Object -Average).Average
$min = ($times | Measure-Object -Minimum).Minimum
$max = ($times | Measure-Object -Maximum).Maximum
$results['repeated_avg'] = [math]::Round($avg, 2)
$results['repeated_min'] = $min
$results['repeated_max'] = $max
Write-Host "   Avg Response Time: $([math]::Round($avg, 2))ms"
Write-Host "   Min: $($min)ms, Max: $($max)ms"
if ($avg -lt 500) {
    Write-Host "   ✅ PASS (avg < 500ms)`n" -ForegroundColor Green
} else {
    Write-Host "   ⚠️ SLOW (avg >= 500ms)`n" -ForegroundColor Yellow
}

# Summary
Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PERFORMANCE TEST SUMMARY                                ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$results.GetEnumerator() | Sort-Object Value | ForEach-Object {
    $status = if ($_.Value -lt 500) { "✅ PASS" } else { "⚠️ SLOW" }
    Write-Host "   $($_.Key.PadRight(20)) $($_.Value.ToString().PadLeft(6))ms  $status"
}

$allPass = ($results.Values | Where-Object { $_ -ge 500 }).Count -eq 0
if ($allPass) {
    Write-Host "`n   🎉 ALL TESTS PASSED! All responses under 500ms target`n" -ForegroundColor Green
} else {
    $failCount = ($results.Values | Where-Object { $_ -ge 500 }).Count
    Write-Host "`n   ⚠️ $failCount tests exceeded 500ms target`n" -ForegroundColor Yellow
}

# Export results
$results | ConvertTo-Json | Out-File "output/phase8_api_performance_results.json"
Write-Host "📝 Results saved to output/phase8_api_performance_results.json`n" -ForegroundColor Gray
