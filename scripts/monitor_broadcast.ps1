# General Broadcast Monitor
# Monitors any broadcast checkpoint directory and displays progress
param(
    [string]$CheckpointDir = "",
    [int]$RefreshSeconds = 10,
    [switch]$Continuous
)

function Find-ActiveCheckpointDir {
    # Find the most recently active checkpoint directory by scanning ALL directories with checkpoints
    $activeDir = $null
    $newestTime = [datetime]::MinValue
    
    # Scan current directory for any folder containing checkpoint files
    $allDirs = Get-ChildItem -Directory -ErrorAction SilentlyContinue
    
    foreach ($dir in $allDirs) {
        $checkpoints = Get-ChildItem "$($dir.FullName)/checkpoint_*.json" -ErrorAction SilentlyContinue
        if ($checkpoints) {
            $latest = $checkpoints | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($latest.LastWriteTime -gt $newestTime) {
                $newestTime = $latest.LastWriteTime
                $activeDir = "./$($dir.Name)"
            }
        }
    }
    
    return $activeDir
}

function Show-BroadcastProgress {
    param([string]$TargetDir)
    
    Clear-Host
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "     BROADCAST SESSION MONITOR" -ForegroundColor Cyan
    Write-Host "================================================================`n" -ForegroundColor Cyan
    
    $checkpoints = Get-ChildItem "$TargetDir/checkpoint_*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
    
    if (-not $checkpoints) {
        Write-Host "Waiting for checkpoint files in: $TargetDir" -ForegroundColor Yellow
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
    
    Write-Host "Monitoring: $TargetDir" -ForegroundColor DarkGray
    
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
    $updateTime = $latest.LastWriteTime.ToString("HH:mm:ss")
    Write-Host "  Last Update:  $updateTime" -ForegroundColor Gray
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
            # Count total beats across all stories
            $totalBeats = 0
            $storyCount = 0
            foreach ($story in $cp.story_state.beat_history.PSObject.Properties) {
                $storyCount++
                if ($story.Value) {
                    $totalBeats += $story.Value.Length
                }
            }
            Write-Host "  Beat Tracking: $totalBeats beats from $storyCount stories" -ForegroundColor Yellow
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

# Main execution
if (-not $CheckpointDir) {
    # Auto-detect active checkpoint directory
    $CheckpointDir = Find-ActiveCheckpointDir
    
    if (-not $CheckpointDir) {
        Write-Host "`n❌ No checkpoint directories found with recent activity" -ForegroundColor Red
        Write-Host ""
        Write-Host "Searched locations:" -ForegroundColor Gray
        Write-Host "  - ./phase2_validation_rerun" -ForegroundColor Gray
        Write-Host "  - ./phase2_validation" -ForegroundColor Gray
        Write-Host "  - ./phase1_integration_test" -ForegroundColor Gray
        Write-Host "  - ./checkpoints" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Tip: Start a broadcast or specify directory:" -ForegroundColor Yellow
        Write-Host "     .\scripts\monitor_broadcast.ps1 -CheckpointDir `"./your_dir`"" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
    
    Write-Host "`n✅ Auto-detected checkpoint directory: $CheckpointDir" -ForegroundColor Green
    Start-Sleep -Seconds 1
}

if ($Continuous) {
    while ($true) {
        # Re-scan for active directory on each refresh (detects new broadcasts)
        if (-not $CheckpointDir) {
            $CheckpointDir = Find-ActiveCheckpointDir
            if (-not $CheckpointDir) {
                Clear-Host
                Write-Host "`n⏳ Waiting for broadcast to start..." -ForegroundColor Yellow
                Write-Host "   No checkpoint files found yet.`n" -ForegroundColor Gray
                Start-Sleep -Seconds $RefreshSeconds
                continue
            }
        }
        
        Show-BroadcastProgress -TargetDir $CheckpointDir
        
        # Check if there's a newer checkpoint directory
        $newestDir = Find-ActiveCheckpointDir
        if ($newestDir -ne $CheckpointDir) {
            Write-Host "`n🔄 Switched to newer broadcast: $newestDir" -ForegroundColor Cyan
            $CheckpointDir = $newestDir
            Start-Sleep -Seconds 2
        }
        
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-BroadcastProgress -TargetDir $CheckpointDir
}
