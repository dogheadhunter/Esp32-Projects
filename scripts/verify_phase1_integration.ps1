# Phase 1 Integration Test Verification Script
# Analyzes checkpoints, segments, and validates all Phase 1 features

param(
    [string]$CheckpointDir = "./phase1_integration_test",
    [string]$ExpectedDJ = "Julie (2102, Appalachia)",
    [int]$ExpectedSegments = 32,
    [int]$ExpectedCheckpoints = 16
)

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "PHASE 1 INTEGRATION TEST - VERIFICATION REPORT" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan
Write-Host "Test Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "DJ: $ExpectedDJ" -ForegroundColor Gray
Write-Host "`n"

$results = @{
    CheckpointsPassed = $false
    SegmentsPassed = $false
    IntegrityPassed = $false
    FiltersPassed = $false
    OverallPassed = $false
}

# ============================================================================
# 1. CHECKPOINT SYSTEM VERIFICATION
# ============================================================================
Write-Host "┌────────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│ 1. CHECKPOINT SYSTEM VERIFICATION                                  │" -ForegroundColor Cyan
Write-Host "└────────────────────────────────────────────────────────────────────┘`n" -ForegroundColor Cyan

if (Test-Path $CheckpointDir) {
    $checkpoints = Get-ChildItem "$CheckpointDir/*.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime
    
    Write-Host "  Checkpoints Created: $($checkpoints.Count) / $ExpectedCheckpoints" -ForegroundColor Yellow
    
    # Check if we have enough checkpoints
    if ($checkpoints.Count -ge ($ExpectedCheckpoints * 0.95)) {
        Write-Host "  ✅ Checkpoint count: PASS ($($checkpoints.Count) >= 95% of $ExpectedCheckpoints)" -ForegroundColor Green
        $results.CheckpointsPassed = $true
    } else {
        Write-Host "  ❌ Checkpoint count: FAIL ($($checkpoints.Count) < 95% of $ExpectedCheckpoints)" -ForegroundColor Red
    }
    
    # Verify checkpoint integrity (all valid JSON)
    $validCheckpoints = 0
    $corruptCheckpoints = 0
    
    foreach ($cp in $checkpoints) {
        try {
            $data = Get-Content $cp.FullName -Raw | ConvertFrom-Json
            $validCheckpoints++
            
            # Verify schema
            if (-not $data.metadata -or -not $data.broadcast_state) {
                Write-Host "  ⚠️  Warning: $($cp.Name) missing expected schema sections" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ CORRUPT: $($cp.Name) - $($_.Exception.Message)" -ForegroundColor Red
            $corruptCheckpoints++
        }
    }
    
    Write-Host "`n  Checkpoint Integrity:" -ForegroundColor Yellow
    Write-Host "    Valid: $validCheckpoints" -ForegroundColor Green
    Write-Host "    Corrupt: $corruptCheckpoints" -ForegroundColor $(if ($corruptCheckpoints -eq 0) { "Green" } else { "Red" })
    
    if ($corruptCheckpoints -eq 0) {
        Write-Host "  ✅ Checkpoint integrity: PASS (0 corrupted files)" -ForegroundColor Green
        $results.IntegrityPassed = $true
    } else {
        Write-Host "  ❌ Checkpoint integrity: FAIL ($corruptCheckpoints corrupted files)" -ForegroundColor Red
    }
    
    # Show latest checkpoint details
    if ($checkpoints.Count -gt 0) {
        $latest = $checkpoints[-1]
        $latestData = Get-Content $latest.FullName -Raw | ConvertFrom-Json
        
        Write-Host "`n  Latest Checkpoint Details:" -ForegroundColor Yellow
        Write-Host "    File: $($latest.Name)" -ForegroundColor Gray
        Write-Host "    DJ: $($latestData.metadata.dj_name)" -ForegroundColor Gray
        Write-Host "    Current Hour: $($latestData.metadata.current_hour)" -ForegroundColor Gray
        Write-Host "    Segments Generated: $($latestData.metadata.segments_generated)" -ForegroundColor Gray
        Write-Host "    Timestamp: $($latestData.metadata.created_at)" -ForegroundColor Gray
    }
    
} else {
    Write-Host "  ❌ Checkpoint directory not found: $CheckpointDir" -ForegroundColor Red
}

# ============================================================================
# 2. SEGMENT GENERATION VERIFICATION
# ============================================================================
Write-Host "`n┌────────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│ 2. SEGMENT GENERATION VERIFICATION                                 │" -ForegroundColor Cyan
Write-Host "└────────────────────────────────────────────────────────────────────┘`n" -ForegroundColor Cyan

# Find output directory
$outputDirs = Get-ChildItem -Directory | Where-Object { $_.Name -match "Julie.*output" }

if ($outputDirs) {
    $outputDir = $outputDirs[0]
    Write-Host "  Output Directory: $($outputDir.Name)" -ForegroundColor Yellow
    
    $segments = Get-ChildItem "$($outputDir.FullName)/*.txt" -ErrorAction SilentlyContinue
    $segmentCount = $segments.Count
    $completionRate = [math]::Round($segmentCount / $ExpectedSegments * 100, 1)
    
    Write-Host "  Segments Generated: $segmentCount / $ExpectedSegments ($completionRate%)" -ForegroundColor Yellow
    
    if ($completionRate -ge 95) {
        Write-Host "  ✅ Segment generation: PASS (≥95% completion)" -ForegroundColor Green
        $results.SegmentsPassed = $true
    } elseif ($completionRate -ge 90) {
        Write-Host "  ⚠️  Segment generation: ACCEPTABLE (≥90% completion)" -ForegroundColor Yellow
        $results.SegmentsPassed = $true
    } else {
        Write-Host "  ❌ Segment generation: FAIL (<90% completion)" -ForegroundColor Red
    }
    
    # Show segment distribution by type
    Write-Host "`n  Segment Distribution:" -ForegroundColor Yellow
    $timeChecks = ($segments | Where-Object { $_.Name -match "time" }).Count
    $gossips = ($segments | Where-Object { $_.Name -match "gossip" }).Count
    
    Write-Host "    Time checks: $timeChecks" -ForegroundColor Gray
    Write-Host "    Gossip segments: $gossips" -ForegroundColor Gray
    
} else {
    Write-Host "  ⚠️  No output directory found matching 'Julie.*output'" -ForegroundColor Yellow
}

# ============================================================================
# 3. CHROMADB FILTER VERIFICATION (Temporal/Regional)
# ============================================================================
Write-Host "`n┌────────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│ 3. CHROMADB FILTER VERIFICATION                                    │" -ForegroundColor Cyan
Write-Host "└────────────────────────────────────────────────────────────────────┘`n" -ForegroundColor Cyan

if ($outputDir) {
    Write-Host "  Scanning for temporal/regional violations..." -ForegroundColor Yellow
    Write-Host "  (Julie 2102 Appalachia should not mention: NCR, Legion, Mojave)`n" -ForegroundColor Gray
    
    # Temporal violations (content that doesn't exist until after 2102)
    $ncrMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "\bNCR\b" -CaseSensitive -ErrorAction SilentlyContinue
    $legionMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "\bLegion\b|\bCaesar's Legion\b" -CaseSensitive -ErrorAction SilentlyContinue
    $instituteMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "\bInstitute\b" -CaseSensitive -ErrorAction SilentlyContinue
    
    # Regional violations (locations outside Appalachia)
    $mojaveMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "Mojave" -CaseSensitive -ErrorAction SilentlyContinue
    $vegasMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "New Vegas|Vegas Strip" -CaseSensitive -ErrorAction SilentlyContinue
    $commonwealthMatches = Select-String -Path "$($outputDir.FullName)/*.txt" -Pattern "Commonwealth\b" -CaseSensitive -ErrorAction SilentlyContinue
    
    $temporalViolations = $ncrMatches.Count + $legionMatches.Count + $instituteMatches.Count
    $regionalViolations = $mojaveMatches.Count + $vegasMatches.Count + $commonwealthMatches.Count
    $totalViolations = $temporalViolations + $regionalViolations
    
    Write-Host "  Temporal Violations:" -ForegroundColor Yellow
    Write-Host "    NCR mentions: $($ncrMatches.Count)" -ForegroundColor $(if ($ncrMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    Legion mentions: $($legionMatches.Count)" -ForegroundColor $(if ($legionMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    Institute mentions: $($instituteMatches.Count)" -ForegroundColor $(if ($instituteMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    Total temporal: $temporalViolations" -ForegroundColor $(if ($temporalViolations -eq 0) { "Green" } else { "Red" })
    
    Write-Host "`n  Regional Violations:" -ForegroundColor Yellow
    Write-Host "    Mojave mentions: $($mojaveMatches.Count)" -ForegroundColor $(if ($mojaveMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    New Vegas mentions: $($vegasMatches.Count)" -ForegroundColor $(if ($vegasMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    Commonwealth mentions: $($commonwealthMatches.Count)" -ForegroundColor $(if ($commonwealthMatches.Count -eq 0) { "Green" } else { "Red" })
    Write-Host "    Total regional: $regionalViolations" -ForegroundColor $(if ($regionalViolations -eq 0) { "Green" } else { "Red" })
    
    Write-Host "`n  Overall Violations: $totalViolations" -ForegroundColor $(if ($totalViolations -eq 0) { "Green" } else { "Red" })
    
    if ($totalViolations -eq 0) {
        Write-Host "  ✅ ChromaDB filters: PASS (0 violations detected)" -ForegroundColor Green
        $results.FiltersPassed = $true
    } elseif ($totalViolations -le 2) {
        Write-Host "  ⚠️  ChromaDB filters: ACCEPTABLE (≤2 violations)" -ForegroundColor Yellow
        $results.FiltersPassed = $true
    } else {
        Write-Host "  ❌ ChromaDB filters: FAIL ($totalViolations violations)" -ForegroundColor Red
    }
    
    # Show violation details if any
    if ($totalViolations -gt 0) {
        Write-Host "`n  Violation Details:" -ForegroundColor Yellow
        $allViolations = @($ncrMatches; $legionMatches; $instituteMatches; $mojaveMatches; $vegasMatches; $commonwealthMatches)
        foreach ($match in $allViolations | Select-Object -First 5) {
            if ($match) {
                Write-Host "    $($match.Filename): Line $($match.LineNumber)" -ForegroundColor Gray
                Write-Host "      $($match.Line.Trim())" -ForegroundColor Gray
            }
        }
        if ($totalViolations -gt 5) {
            Write-Host "    ... and $($totalViolations - 5) more" -ForegroundColor Gray
        }
    }
}

# ============================================================================
# 4. RETRY SYSTEM VERIFICATION
# ============================================================================
Write-Host "`n┌────────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│ 4. RETRY SYSTEM VERIFICATION                                       │" -ForegroundColor Cyan
Write-Host "└────────────────────────────────────────────────────────────────────┘`n" -ForegroundColor Cyan

# Check log files for retry activity
$logFiles = Get-ChildItem logs/session_*_broadcast.log -ErrorAction SilentlyContinue | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -First 1

if ($logFiles) {
    Write-Host "  Latest log file: $($logFiles.Name)" -ForegroundColor Yellow
    
    # Search for retry-related log entries
    $retryLines = Select-String -Path $logFiles.FullName -Pattern "retry|RETRY" -CaseSensitive -ErrorAction SilentlyContinue
    $validationFails = Select-String -Path $logFiles.FullName -Pattern "validation.*failed|VALIDATION FAILED" -CaseSensitive -ErrorAction SilentlyContinue
    
    Write-Host "  Retry mentions in log: $($retryLines.Count)" -ForegroundColor Yellow
    Write-Host "  Validation failures: $($validationFails.Count)" -ForegroundColor Yellow
    
    if ($retryLines.Count -gt 0) {
        Write-Host "  ✅ Retry system: ACTIVE (retries detected in logs)" -ForegroundColor Green
    } else {
        Write-Host "  ℹ️  Retry system: NO RETRIES NEEDED (all segments passed first attempt)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠️  No log files found" -ForegroundColor Yellow
}

# ============================================================================
# FINAL SUMMARY
# ============================================================================
Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "FINAL RESULTS" -ForegroundColor Cyan
Write-Host "======================================================================`n" -ForegroundColor Cyan

Write-Host "  Checkpoint System:      " -NoNewline
Write-Host $(if ($results.CheckpointsPassed) { "✅ PASS" } else { "❌ FAIL" }) -ForegroundColor $(if ($results.CheckpointsPassed) { "Green" } else { "Red" })

Write-Host "  Checkpoint Integrity:   " -NoNewline
Write-Host $(if ($results.IntegrityPassed) { "✅ PASS" } else { "❌ FAIL" }) -ForegroundColor $(if ($results.IntegrityPassed) { "Green" } else { "Red" })

Write-Host "  Segment Generation:     " -NoNewline
Write-Host $(if ($results.SegmentsPassed) { "✅ PASS" } else { "❌ FAIL" }) -ForegroundColor $(if ($results.SegmentsPassed) { "Green" } else { "Red" })

Write-Host "  ChromaDB Filters:       " -NoNewline
Write-Host $(if ($results.FiltersPassed) { "✅ PASS" } else { "❌ FAIL" }) -ForegroundColor $(if ($results.FiltersPassed) { "Green" } else { "Red" })

$results.OverallPassed = $results.CheckpointsPassed -and $results.IntegrityPassed -and $results.SegmentsPassed -and $results.FiltersPassed

Write-Host "`n  OVERALL:                " -NoNewline
if ($results.OverallPassed) {
    Write-Host "✅ PHASE 1 INTEGRATION TEST PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ PHASE 1 INTEGRATION TEST FAILED" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor Cyan

# Return exit code
if ($results.OverallPassed) {
    exit 0
} else {
    exit 1
}
