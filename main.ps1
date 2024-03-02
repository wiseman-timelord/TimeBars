function Show-Divider {
    Write-Host "`n----------------------------------------------"
}

function Show-Header {
    Clear-Host
    Write-Host "`n=================( TimeLoop )=================`n"
}

function Start-Timer {
    param([TimeSpan]$Duration)
    
    $endTime = (Get-Date).Add($Duration)
    while ($endTime -gt (Get-Date)) {
        Show-Header
        $elapsed = (Get-Date) - $endTime.Add(-$Duration)
        $remaining = $endTime - (Get-Date)
        $percentComplete = (($elapsed.TotalSeconds) / $Duration.TotalSeconds) * 100

        # Updated display method
        $status = "Timer Running..."
        $currentOperation = "Elapsed: $($elapsed.ToString('hh\:mm\:ss')) - Remaining: $($remaining.ToString('hh\:mm\:ss'))"
        $progressBar = '[' + '█' * [Math]::Round($percentComplete / 2.5) + ' ' * (40 - [Math]::Round($percentComplete / 2.5)) + ']'
        Write-Host "$status`n"
		Write-Host "`n`n`n`n`n   $currentOperation`n"
        Write-Host "  $progressBar"

        Start-Sleep -Seconds 5
    }
    
    Show-Header
    Write-Host "`n`n`n                                             Timer Over!"
    Show-Divider
    $action = Read-Host "Select, Menu = M, Exit = X: "
    if ($action -eq 'M') {
        Show-Menu
    }
}

function Show-Menu {
    do {
        Show-Header
        Write-Host "`n`n             1. 2 Hours Timer`n"
        Write-Host "             2. 1 Hour Timer`n"
        Write-Host "             3. 30 Minutes Timer`n"
        Write-Host "             4. 15 Minutes Timer`n"
        Write-Host "             5. 10 Minutes Timer`n"
        Write-Host "             6. 5 Minutes Timer`n`n"
        Show-Divider
        $choice = Read-Host "Select, Options = 1-6, Exit = X"
        switch ($choice) {
            "1" {
                Write-Host "Starting 2H Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromHours(2)
            }
            "2" {
                Write-Host "Starting 1H Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromHours(1)
            }
            "3" {
                Write-Host "Starting 30M Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromMinutes(30)
            }
            "4" {
                Write-Host "Starting 15M Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromMinutes(15)
            }
            "5" {
                Write-Host "Starting 10M Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromMinutes(10)
            }
            "6" {
                Write-Host "Starting 5M Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromMinutes(5)
            }
            "X" {
                Write-Host "Exiting Program..."
                Start-Sleep -Seconds 2
                break
            }
            default {
                Write-Host "Invalid option, please try again."
                Start-Sleep -Seconds 2
                continue
            }
        }
        if ($choice -ne "X") {
            Start-Timer -Duration $duration
        }
    } while ($choice -ne "X")
}

Show-Menu
