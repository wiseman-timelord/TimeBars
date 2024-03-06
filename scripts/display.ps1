# Script: display.ps1

# Show Devider
function Show-Divider {
    Write-Host "`n----------------------------------------------"
}

# Page Title
function Show-Header {
    Clear-Host
    Write-Host "`n=================( TimeBars )=================`n"
}

# display configuration
function Set-ConfigureDisplay {
    Write-Host "Display Configuration.."
    [Console]::ForegroundColor = [ConsoleColor]::White
    [Console]::BackgroundColor = [ConsoleColor]::DarkGray
	[Console]::Clear()
    Show-Header
	Write-Host "Re-Setting Dir.."
	Write-Host "..Using Script Dir.`n"
    Write-Host "Display Configuration.."
	Write-Host "..Display Configured.`n"
}


# Timer Over
function Show-TimerOverScreen {
    param([TimeSpan]$Duration)
    Show-Header
    Write-Host "`n`n`n`n                 Timer Over!`n`n`n`n"
    Show-Divider
    $player = New-Object System.Media.SoundPlayer ".\sounds\alarm-bleep.wav"
    $player.PlaySync()
    if ($global:shutdownEnabled -and $isAdmin) {
        Write-Host " Shutdown Initiated..."
        Start-Sleep -Seconds 5
        Stop-Computer -Force
    } else {
        $action = Read-Host "Select, Repeat = R, Menu = M, Exit = X"
        switch ($action) {
            "R" { Start-Timer -Duration $Duration }
            "M" { Show-DynamicMenu }
            "X" { return }
            default { 
                Write-Host "Invalid option, please try again."; 
                Start-Sleep -Seconds 2; 
                Show-TimerOverScreen -Duration $Duration 
            }
        }
    }
}

# Shutdown Toggle
function Toggle-ShutdownOption {
    $global:shutdownEnabled = -not $global:shutdownEnabled
}

# Main Menu
# Main Menu
function Show-DynamicMenu {
    do {
        $shutdownStatus = if ($global:shutdownEnabled) {"Activated"} else {"Optional"}
        Show-Header
        Write-Host "             1. 2 Hours Timer"
        Write-Host "             2. 1 Hour Timer"
        Write-Host "             3. 30 Minutes Timer"
        Write-Host "             4. 15 Minutes Timer"
        Write-Host "             5. 10 Minutes Timer"
        Write-Host "             6. 5 Minutes Timer"
        Write-Host "             7. 1 Minute Timer`n"
        if ($isAdmin) {
            Write-Host "            Shutdown: $shutdownStatus"
        } else {
            Write-Host "            Shutdown: Unavailable"
        }
        Show-Divider
        $promptText = if ($isAdmin) {"Select, Options=1-7, Shutdown=S, Exit=X"} else {"Select, Options=1-7, Exit=X"}
        $choice = Read-Host $promptText
        switch ($choice) {
            "1" {"Starting 2H Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromHours(2)}
            "2" {"Starting 1H Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromHours(1)}
            "3" {"Starting 30M Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromMinutes(30)}
            "4" {"Starting 15M Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromMinutes(15)}
            "5" {"Starting 10M Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromMinutes(10)}
            "6" {"Starting 5M Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromMinutes(5)}
            "7" {"Starting 1M Timer..."; Start-Sleep -Seconds 2; $duration = [TimeSpan]::FromMinutes(1)}
            "S" {
                if ($isAdmin) {
                    Toggle-ShutdownOption
                    $currentStatus = if ($global:shutdownEnabled) {"activated"} else {"de-activated"}
                    Write-Host "Shutdown has been $currentStatus."
                    Start-Sleep -Seconds 2
                }
            }
            "X" {"Exiting Program..."; Start-Sleep -Seconds 2; break}
            default {"Invalid option, please try again."; Start-Sleep -Seconds 2; continue}
        }
        if ($choice -ne "X") {
            Start-Timer -Duration $duration
        }
    } while ($choice -ne "X")
}

