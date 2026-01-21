# Phase 2 Validation Test Monitor
param(
    [string]$CheckpointDir = "./phase2_validation",
    [int]$RefreshSeconds = 30,
    [switch]$Continuous
)

function Show-Progress {
    Clear-Host
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "     PHASE 2 VALIDATION TEST MONITOR" -ForegroundColor Cyan
    Write-Host "================================================================`n" -ForegroundColor Cyan
    
    $checkpoints = Get-ChildItem "$CheckpointDir/*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if (-not $checkpoints) {
        Write-Host "Waiting for first checkpoint..." -ForegroundColor Yellow
        Write-Host "Expected in ~2 hours (checkpoint interval = 2 hours)`n" -ForegroundColor Gray
        
        $pythonProc = Get-Process python -ErrorAction SilentlyContinue
        if ($pythonProc) {
            Write-Host "[OK] Test process running (PID: $($pythonProc[0].Id))" -ForegroundColor Green
            $runtime = (Get-Date) - $pythonProc[0].StartTime
            $hours = [math]::Floor($runtime.TotalHours)
            $mins = $runtime.Minutes
            Write-Host "   Runtime: ${hours}h ${mins}m`n" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] No Python process found!`n" -ForegroundColor Red
        }
        return
    }
    
    $latest = $checkpoints[0]
    $cp = Get-Content $latest.FullName | ConvertFrom-Json
    
    $targetSegments = 64
    $segmentsGenerated = if ($cp.metadata.segments_generated) { $cp.metadata.segments_generated } else { 0 }
    $progress = [math]::Round(($segmentsGenerated / $targetSegments) * 100, 1)
    
    # Calculate actual test runtime
    try {
        $testStart = [datetime]::Parse($cp.session_context.session_memory.session_start)
        $checkpointTime = [datetime]::Parse($cp.metadata.created_at)
        $testRuntime = $checkpointTime - $testStart
        $runtimeHours = [math]::Floor($testRuntime.TotalHours)
        $runtimeMins = $testRuntime.Minutes
        $runtimeDisplay = "${runtimeHours}h ${runtimeMins}m"
    } catch {
        $runtimeDisplay = "N/A"
    }
    
    Write-Host "OVERALL PROGRESS" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "  Segments:     $segmentsGenerated/$targetSegments ($progress%)" -ForegroundColor Yellow
    Write-Host "  Current Hour: $($cp.metadata.current_hour)/$($cp.metadata.total_hours)" -ForegroundColor Yellow
    Write-Host "  Test Runtime: $runtimeDisplay" -ForegroundColor Green
    Write-Host "  Checkpoint:   $($latest.Name)" -ForegroundColor Gray
    Write-Host "  Last Update:  $($latest.LastWriteTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "PHASE 2A: Quality Gates" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    if ($cp.broadcast_state) {
        Write-Host "  Historical Broadcasts: $($cp.broadcast_state.broadcast_count)" -ForegroundColor Gray
        Write-Host "  (Historical runtime: $([math]::Round($cp.broadcast_state.total_runtime_hours, 2))h - from previous sessions)" -ForegroundColor DarkGray
    } else {
        Write-Host "  No broadcast state in checkpoint" -ForegroundColor Gray
    }
    Write-Host ""
    
    Write-Host "PHASE 2B: Variety Tracking" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    if ($cp.session_context.session_memory) {
        $mem = $cp.session_context.session_memory
        $segCount = if ($mem.segment_count) { $mem.segment_count } else { 0 }
        Write-Host "  Session Segments: $segCount" -ForegroundColor Yellow
        
        if ($mem.mentioned_topics) {
            $topicCount = ($mem.mentioned_topics.PSObject.Properties | Measure-Object).Count
            Write-Host "  Topic Diversity:  $topicCount categories" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  No session memory in checkpoint" -ForegroundColor Gray
    }
    Write-Host ""
    
    Write-Host "PHASE 2C: Story Beat Tracking" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    if ($cp.story_state) {
        $dailyPool = if ($cp.story_state.story_pools.daily) { $cp.story_state.story_pools.daily.Length } else { 0 }
        $weeklyPool = if ($cp.story_state.story_pools.weekly) { $cp.story_state.story_pools.weekly.Length } else { 0 }
        $monthlyPool = if ($cp.story_state.story_pools.monthly) { $cp.story_state.story_pools.monthly.Length } else { 0 }
        $beatHistory = if ($cp.story_state.beat_history) { ($cp.story_state.beat_history.PSObject.Properties | Measure-Object).Count } else { 0 }
        
        Write-Host "  Story Pools:" -ForegroundColor Gray
        Write-Host "    Daily:   $dailyPool stories" -ForegroundColor $(if ($dailyPool -eq 0) { "DarkGray" } else { "Green" })
        Write-Host "    Weekly:  $weeklyPool stories" -ForegroundColor $(if ($weeklyPool -eq 0) { "Yellow" } else { "Green" })
        Write-Host "    Monthly: $monthlyPool stories" -ForegroundColor $(if ($monthlyPool -eq 0) { "DarkGray" } else { "Green" })
        Write-Host "  Beat Tracking: $beatHistory stories tracked" -ForegroundColor Yellow
    } else {
        Write-Host "  No story state in checkpoint" -ForegroundColor Gray
    }
    Write-Host ""
    
    Write-Host "PROGRESS BAR" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    $barWidth = 50
    $filled = [math]::Floor($barWidth * ($progress / 100))
    $empty = $barWidth - $filled
    Write-Host "  [" -NoNewline
    Write-Host ("#" * $filled) -NoNewline -ForegroundColor Green
    Write-Host ("-" * $empty) -NoNewline -ForegroundColor DarkGray
    Write-Host "] $progress%" -ForegroundColor Yellow
    Write-Host ""
    
    if ($Continuous) {
        Write-Host "Next refresh in $RefreshSeconds seconds... (Ctrl+C to stop)" -ForegroundColor DarkGray
    }
}

if ($Continuous) {
    while ($true) {
        Show-Progress
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-Progress
}
