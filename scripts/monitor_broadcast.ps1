# General Broadcast Monitor
# Monitors any broadcast checkpoint directory and displays progress
param(
    [string]$CheckpointDir = ".",
    [int]$RefreshSeconds = 30,
    [switch]$Continuous
)

function Show-BroadcastProgress {
    Clear-Host
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "     BROADCAST SESSION MONITOR" -ForegroundColor Cyan
    Write-Host "================================================================`n" -ForegroundColor Cyan
    
    $checkpoints = Get-ChildItem "$CheckpointDir/checkpoint_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if (-not $checkpoints) {
        Write-Host "Waiting for checkpoint files in: $CheckpointDir" -ForegroundColor Yellow
        Write-Host ""
        
        $pythonProc = Get-Process python -ErrorAction SilentlyContinue
        if ($pythonProc) {
            Write-Host "[OK] Broadcast process running (PID: $($pythonProc[0].Id))" -ForegroundColor Green
            $runtime = (Get-Date) - $pythonProc[0].StartTime
            $hours = [math]::Floor($runtime.TotalHours)
            $mins = $runtime.Minutes
            Write-Host "   Runtime: ${hours}h ${mins}m`n" -ForegroundColor Green
        } else {
            Write-Host "[WARN] No Python process found`n" -ForegroundColor Yellow
        }
        return
    }
    
    $latest = $checkpoints[0]
    $cp = Get-Content $latest.FullName | ConvertFrom-Json
    
    # Detect checkpoint structure and extract key info
    $djName = if ($cp.metadata.dj_name) { $cp.metadata.dj_name } elseif ($cp.dj_name) { $cp.dj_name } else { "Unknown DJ" }
    $segmentsGenerated = if ($cp.metadata.segments_generated) { $cp.metadata.segments_generated } elseif ($cp.segments_completed) { $cp.segments_completed } else { 0 }
    $currentHour = if ($cp.metadata.current_hour) { $cp.metadata.current_hour } else { "?" }
    $totalHours = if ($cp.metadata.total_hours) { $cp.metadata.total_hours } else { "?" }
    
    # Calculate test runtime if available
    try {
        if ($cp.session_context.session_memory.session_start -and $cp.metadata.created_at) {
            $testStart = [datetime]::Parse($cp.session_context.session_memory.session_start)
            $checkpointTime = [datetime]::Parse($cp.metadata.created_at)
            $testRuntime = $checkpointTime - $testStart
            $runtimeHours = [math]::Floor($testRuntime.TotalHours)
            $runtimeMins = $testRuntime.Minutes
            $runtimeDisplay = "${runtimeHours}h ${runtimeMins}m"
        } elseif ($cp.broadcast_start -and $cp.timestamp) {
            $testStart = [datetime]::Parse($cp.broadcast_start)
            $checkpointTime = [datetime]::Parse($cp.timestamp)
            $testRuntime = $checkpointTime - $testStart
            $runtimeHours = [math]::Floor($testRuntime.TotalHours)
            $runtimeMins = $testRuntime.Minutes
            $runtimeDisplay = "${runtimeHours}h ${runtimeMins}m"
        } else {
            $runtimeDisplay = "N/A"
        }
    } catch {
        $runtimeDisplay = "N/A"
    }
    
    # Calculate progress if total hours known
    if ($totalHours -ne "?" -and $totalHours -gt 0) {
        $targetSegments = $totalHours * 2  # Assuming 2 segments/hour
        $progress = [math]::Round(($segmentsGenerated / $targetSegments) * 100, 1)
    } else {
        $targetSegments = "?"
        $progress = 0
    }
    
    Write-Host "SESSION INFO" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor DarkGray
    Write-Host "  DJ:           $djName" -ForegroundColor Yellow
    
    if ($targetSegments -ne "?") {
        Write-Host "  Segments:     $segmentsGenerated/$targetSegments ($progress%)" -ForegroundColor Yellow
    } else {
        Write-Host "  Segments:     $segmentsGenerated" -ForegroundColor Yellow
    }
    
    if ($totalHours -ne "?") {
        Write-Host "  Hour:         $currentHour/$totalHours" -ForegroundColor Yellow
    } else {
        Write-Host "  Hour:         $currentHour" -ForegroundColor Yellow
    }
    
    Write-Host "  Runtime:      $runtimeDisplay" -ForegroundColor Green
    Write-Host "  Checkpoint:   $($latest.Name)" -ForegroundColor Gray
    Write-Host "  Last Update:  $($latest.LastWriteTime.ToString('HH:mm:ss'))" -ForegroundColor Gray
    Write-Host ""
    
    # Story State (if available)
    if ($cp.story_state) {
        Write-Host "STORY SYSTEM" -ForegroundColor Cyan
        Write-Host "================================================================" -ForegroundColor DarkGray
        
        if ($cp.story_state.story_pools) {
            $dailyPool = if ($cp.story_state.story_pools.daily) { $cp.story_state.story_pools.daily.Length } else { 0 }
            $weeklyPool = if ($cp.story_state.story_pools.weekly) { $cp.story_state.story_pools.weekly.Length } else { 0 }
            $monthlyPool = if ($cp.story_state.story_pools.monthly) { $cp.story_state.story_pools.monthly.Length } else { 0 }
            
            Write-Host "  Story Pools:" -ForegroundColor Gray
            Write-Host "    Daily:   $dailyPool" -ForegroundColor $(if ($dailyPool -eq 0) { "DarkGray" } else { "Green" })
            Write-Host "    Weekly:  $weeklyPool" -ForegroundColor $(if ($weeklyPool -eq 0) { "Yellow" } else { "Green" })
            Write-Host "    Monthly: $monthlyPool" -ForegroundColor $(if ($monthlyPool -eq 0) { "DarkGray" } else { "Green" })
        }
        
        if ($cp.story_state.beat_history) {
            $beatCount = ($cp.story_state.beat_history.PSObject.Properties | Measure-Object).Count
            Write-Host "  Beat Tracking: $beatCount stories" -ForegroundColor Yellow
        }
        
        Write-Host ""
    }
    
    # Session Memory (if available)
    if ($cp.session_context.session_memory) {
        Write-Host "SESSION MEMORY" -ForegroundColor Cyan
        Write-Host "================================================================" -ForegroundColor DarkGray
        
        $mem = $cp.session_context.session_memory
        if ($mem.segment_count) {
            Write-Host "  Segments in Session: $($mem.segment_count)" -ForegroundColor Yellow
        }
        
        if ($mem.mentioned_topics) {
            $topicCount = ($mem.mentioned_topics.PSObject.Properties | Measure-Object).Count
            Write-Host "  Topic Diversity:     $topicCount categories" -ForegroundColor Yellow
        }
        
        Write-Host ""
    }
    
    # Progress Bar
    if ($progress -gt 0 -and $progress -le 100) {
        Write-Host "PROGRESS" -ForegroundColor Cyan
        Write-Host "================================================================" -ForegroundColor DarkGray
        $barWidth = 50
        $filled = [math]::Floor($barWidth * ($progress / 100))
        $empty = [math]::Max(0, $barWidth - $filled)
        Write-Host "  [" -NoNewline
        Write-Host ("#" * $filled) -NoNewline -ForegroundColor Green
        Write-Host ("-" * $empty) -NoNewline -ForegroundColor DarkGray
        Write-Host "] $progress%" -ForegroundColor Yellow
        Write-Host ""
    }
    
    if ($Continuous) {
        Write-Host "Next refresh in $RefreshSeconds seconds... (Ctrl+C to stop)" -ForegroundColor DarkGray
    }
}

if ($Continuous) {
    while ($true) {
        Show-BroadcastProgress
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-BroadcastProgress
}
