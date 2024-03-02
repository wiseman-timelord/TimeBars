function Show-Divider {
    Write-Host "`n----------------------------------------------"
}

function Show-Header {
    Clear-Host
    Write-Host "`n=================( TimeLoop )=================`n"
}

function Show-TimerOverScreen {
    param([TimeSpan]$Duration)

    Show-Header
    Write-Host "`n`n`n`n`n`n`n                 Timer Over!`n`n`n`n`n`n`n"
    Show-Divider
    # Play sound
    $player = New-Object System.Media.SoundPlayer ".\sounds\alarm-bleep.wav"
    $player.PlaySync()

    $action = Read-Host "Select, Repeat = R, Menu = M, Exit = X"
    switch ($action) {
        "R" { Start-Timer -Duration $Duration }
        "M" { Show-Menu }
        "X" { return }
        default { Write-Host "Invalid option, please try again."; Start-Sleep -Seconds 2; Show-TimerOverScreen -Duration $Duration }
    }
}


function Start-Timer {
    param([TimeSpan]$Duration)
    
    $endTime = (Get-Date).Add($Duration)
    while ($endTime -gt (Get-Date)) {
        Show-Header
        $elapsed = (Get-Date) - $endTime.Add(-$Duration)
        $remaining = $endTime - (Get-Date)
        $percentComplete = (($elapsed.TotalSeconds) / $Duration.TotalSeconds) * 100

        $status = "Timer Running..."
        $currentOperation = "Elapsed: $($elapsed.ToString('hh\:mm\:ss')) - Remaining: $($remaining.ToString('hh\:mm\:ss'))"
        $progressBar = '[' + '█' * [Math]::Round($percentComplete / 2.5) + ' ' * (40 - [Math]::Round($percentComplete / 2.5)) + ']'
        Write-Host "$status`n"
        Write-Host "`n`n`n`n   $currentOperation`n"
        Write-Host "  $progressBar`n`n`n`n`n`n"
		Show-Divider
        Start-Sleep -Seconds 5
    }
    
    Show-TimerOverScreen -Duration $Duration
}


function Show-Menu {
    do {
        Show-Header
        Write-Host "`n             1. 2 Hours Timer`n"
        Write-Host "             2. 1 Hour Timer`n"
        Write-Host "             3. 30 Minutes Timer`n"
        Write-Host "             4. 15 Minutes Timer`n"
        Write-Host "             5. 10 Minutes Timer`n"
        Write-Host "             6. 5 Minutes Timer`n"
		Write-Host "             7. 1 Minute Timer`n"
        Show-Divider
        $choice = Read-Host "Select, Options = 1-7, Exit = X"
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
            "7" {
                Write-Host "Starting 1M Timer..."
                Start-Sleep -Seconds 2
                $duration = [TimeSpan]::FromMinutes(1)
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

# Sets the window title, size, and console properties for display configuration
function Set-ConfigureDisplay {
    Write-Host "Display Configuration.."
    [Console]::ForegroundColor = [ConsoleColor]::White
    [Console]::BackgroundColor = [ConsoleColor]::DarkGray
	[Console]::Clear()
    Show-Header
    Write-Host "Display Configuration.."
	Write-Host "..Display Configured.`n"
}


# Initialize program
function script-InitializationCode {
	Clear-Host
	Show-Header
	Start-Sleep -Seconds 1
	Set-ConfigureDisplay
	Start-Sleep -Seconds 1
	Write-Host "Powershell Script Initialized...`n"
    Start-Sleep -Seconds 2
}

# Exit Program
function script-FinalizationCode {
    Clear-Host
	Show-Header
    Write-Host "`n....Powershell Script Exiting.`n"
    Start-Sleep -Seconds 2
	exit
}


# Entry point
script-InitializationCode
Show-Menu
script-FinalizationCode

