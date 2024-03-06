# Script: main.ps1

# Variables
$global:isAdmin = $false
$global:shutdownEnabled = $false


# Imports
. .\scripts\display.ps1

# Check Admin
function Check-AdminRights {
    Write-Host "Checking Admin.."
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
    $global:isAdmin = $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if ($global:isAdmin) {
        Write-Host "..Shutdown Optional.`n"
		Write-Host "Re-Setting Dir.."
        Set-Location -Path $PSScriptRoot
	    Write-Host "..Using Script Dir.`n"
    } else {
        Write-Host "..Regular Timer.`n"
    }
}

# Start Timer
function Start-Timer {
    param([TimeSpan]$Duration)
    
    $endTime = (Get-Date).Add($Duration)
    while ($endTime -gt (Get-Date)) {
        Show-Header
        $elapsed = (Get-Date) - $endTime.Add(-$Duration)
        $remaining = $endTime - (Get-Date)
        $percentComplete = (($elapsed.TotalSeconds) / $Duration.TotalSeconds) * 100

        $status = "`n                Timer Running.."
        $currentOperation = "Elapsed: $($elapsed.ToString('hh\:mm\:ss')) - Remaining: $($remaining.ToString('hh\:mm\:ss'))"
        $progressBar = '[' + '█' * [Math]::Round($percentComplete / 2.5) + ' ' * (40 - [Math]::Round($percentComplete / 2.5)) + ']'
        Write-Host "$status`n"
        Write-Host "`n   $currentOperation`n"
        Write-Host "  $progressBar`n`n"
		Show-Divider
        Start-Sleep -Seconds 5
    }
    
    Show-TimerOverScreen -Duration $Duration
}

# Initialize program
function script-InitializationCode {
	Clear-Host
	Show-Header
	Start-Sleep -Seconds 1
	Set-ConfigureDisplay
	Start-Sleep -Seconds 1
	Check-AdminRights
	Start-Sleep -Seconds 1
	Write-Host "Powershell Script Initialized...`n"
    Start-Sleep -Seconds 2
}

# Exit Program
function script-FinalizationCode {
    Clear-Host
	Show-Header
    Write-Host "....Powershell Script Exiting.`n"
    Start-Sleep -Seconds 2
	exit
}

# Entry point
script-InitializationCode
Show-DynamicMenu
script-FinalizationCode

