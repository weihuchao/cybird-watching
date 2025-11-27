# HoloCubic PowerShell CLI - Clean Architecture Version
param(
    [string]$ComPort = "COM3",
    [int]$BaudRate = 115200
)

# ==================== CONFIGURATION ====================
class HoloCubicConfig {
    [int]$ConnectTimeoutMs = 3000
    [int]$CommandTimeoutMs = 6000
    [int]$ResponseWaitMs = 300
    [int]$DataReadIntervalMs = 50
    [int]$NoDataTimeoutMs = 800
    [int]$PatientWaitTimeoutMs = 300

    [string]$ResponseStartMarker = "<<<RESPONSE_START>>>"
    [string]$ResponseEndMarker = "<<<RESPONSE_END>>>"
}

# ==================== CONNECTION MANAGER ====================
class SerialConnectionManager {
    [System.IO.Ports.SerialPort]$Port
    [bool]$IsConnected

    SerialConnectionManager([string]$comPort, [int]$baudRate) {
        $this.Port = $null
        $this.IsConnected = $false
        $this.ComPort = $comPort
        $this.BaudRate = $baudRate
    }

    [string]$ComPort
    [int]$BaudRate

    [bool]Connect() {
        try {
            $this.Port = New-Object System.IO.Ports.SerialPort $this.ComPort, $this.BaudRate
            $this.Port.Open()
            $this.IsConnected = $true
            Write-Host "Connected to HoloCubic device ($($this.ComPort))" -ForegroundColor Green
            return $true
        }
        catch {
            Write-Host "Connection failed: $($_.Exception.Message)" -ForegroundColor Red
            $this.IsConnected = $false
            return $false
        }
    }

    [void]Disconnect() {
        if ($this.Port -and $this.Port.IsOpen) {
            $this.Port.Close()
        }
        $this.IsConnected = $false
    }

    [void]ClearBuffers() {
        if ($this.Port -and $this.Port.IsOpen) {
            $this.Port.DiscardInBuffer()
            $this.Port.DiscardOutBuffer()
        }
    }
}

# ==================== RESPONSE HANDLER ====================
class CommandResponseHandler {
    [HoloCubicConfig]$Config

    CommandResponseHandler([HoloCubicConfig]$config) {
        $this.Config = $config
    }

    [string]ReadResponse([SerialConnectionManager]$connection) {
        $rawResponse = ""
        $startTime = Get-Date
        $foundStart = $false
        $foundEnd = $false

        while ($true) {
            $currentTime = Get-Date
            $elapsed = ($currentTime - $startTime).TotalMilliseconds

            # Exit if total time exceeds timeout
            if ($elapsed -gt $this.Config.CommandTimeoutMs) {
                break
            }

            # If data is available to read
            if ($connection.Port.BytesToRead -gt 0) {
                $newData = $connection.Port.ReadExisting()
                $rawResponse += $newData

                # Check for response markers
                if ($newData -match [regex]::Escape($this.Config.ResponseStartMarker)) {
                    $foundStart = $true
                }

                if ($newData -match [regex]::Escape($this.Config.ResponseEndMarker)) {
                    $foundEnd = $true
                }

                # If we found both markers, extract content
                if ($foundStart -and $foundEnd) {
                    $startPos = $rawResponse.IndexOf($this.Config.ResponseStartMarker)
                    $endPos = $rawResponse.IndexOf($this.Config.ResponseEndMarker)

                    if ($startPos -ne -1 -and $endPos -ne -1) {
                        $contentStart = $startPos + $this.Config.ResponseStartMarker.Length
                        $response = $rawResponse.Substring($contentStart, $endPos - $contentStart)
                        return $response.Trim()
                    }
                }

                continue
            }

            # Brief sleep to avoid high CPU usage
            Start-Sleep -Milliseconds $this.Config.DataReadIntervalMs
        }

        # Fallback: no clear response markers found
        if ($rawResponse.Trim()) {
            return "Warning: Could not find response markers.`nRaw data received: $([regex]::Replace($rawResponse, "`r`n", '\n'))"
        } else {
            return "No response from device"
        }
    }
}

# ==================== COMMAND EXECUTOR ====================
class CommandExecutor {
    [HoloCubicConfig]$Config
    [SerialConnectionManager]$Connection
    [CommandResponseHandler]$ResponseHandler

    CommandExecutor(
        [HoloCubicConfig]$config,
        [SerialConnectionManager]$connection,
        [CommandResponseHandler]$responseHandler
    ) {
        $this.Config = $config
        $this.Connection = $connection
        $this.ResponseHandler = $responseHandler
    }

    [void]ExecuteCommand([string]$command) {
        if (-not $this.Connection.IsConnected) {
            Write-Host "Device not connected" -ForegroundColor Red
            return
        }

        try {
            Write-Host "Sending: $command" -ForegroundColor Yellow

            # Clear input buffer to avoid reading old data
            $this.Connection.ClearBuffers()

            # Special test mode - simple ping without response markers
            if ($command -eq "test") {
                Write-Host "TEST MODE: Sending simple ping without response markers..." -ForegroundColor Cyan
                $this.Connection.Port.WriteLine("help`r`n")
                Start-Sleep -Milliseconds 1000

                # Read whatever comes back without marker processing
                $rawData = ""
                $readAttempts = 0
                while ($this.Connection.Port.BytesToRead -gt 0 -and $readAttempts -lt 20) {
                    $rawData += $this.Connection.Port.ReadExisting()
                    Start-Sleep -Milliseconds 50
                    $readAttempts++
                }

                if ($rawData.Trim()) {
                    Write-Host "RAW RESPONSE RECEIVED:" -ForegroundColor Green
                    Write-Host $rawData -ForegroundColor White
                } else {
                    Write-Host "No raw data received - firmware may not be processing commands" -ForegroundColor Red
                }
                return
            }

            # Send command with proper line ending
            $this.Connection.Port.WriteLine($command + "`r`n")

            # Wait for device to start processing (short wait)
            Start-Sleep -Milliseconds $this.Config.ResponseWaitMs

            # Read response directly without discarding buffer
            $response = $this.ResponseHandler.ReadResponse($this.Connection)

            if ($response.Trim()) {
                Write-Host "Response:"
                Write-Host $response -ForegroundColor Cyan
            } else {
                Write-Host "No response from device" -ForegroundColor Gray
            }
        }
        catch {
            Write-Host "Communication error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# ==================== HELP SYSTEM ====================
function Show-Help {
    Write-Host ""
    Write-Host "=== HoloCubic CLI Help ===" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "HoloCubic Device Commands (sent to device):" -ForegroundColor Yellow
    Write-Host "  log           - Show last 20 log lines" -ForegroundColor White
    Write-Host "  log clear     - Clear log file" -ForegroundColor White
    Write-Host "  log size      - Show log file size" -ForegroundColor White
    Write-Host "  log lines N   - Show last N log lines (1-500)" -ForegroundColor White
    Write-Host "  log cat/export- Show full log file content" -ForegroundColor White
    Write-Host "  status        - Show system status" -ForegroundColor White
    Write-Host "  clear         - Clear device terminal screen" -ForegroundColor White
    Write-Host "  tree [path] [levels] - Show SD card directory tree" -ForegroundColor White
    Write-Host "  dh, device-help - Show device help (from HoloCubic)" -ForegroundColor White
    Write-Host ""
    Write-Host "CLI Local Commands:" -ForegroundColor Yellow
    Write-Host "  help          - Show this CLI help" -ForegroundColor White
    Write-Host "  test          - Test basic communication without response markers" -ForegroundColor White
    Write-Host "  quit, exit    - Exit program" -ForegroundColor White
    Write-Host "  reconnect     - Reconnect to device" -ForegroundColor White
    Write-Host "  cls           - Clear this terminal screen" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  HoloCubic> log          # Show device logs" -ForegroundColor Gray
    Write-Host "  HoloCubic> log cat      # Show full log file content" -ForegroundColor Gray
    Write-Host "  HoloCubic> status       # Show device status" -ForegroundColor Gray
    Write-Host "  HoloCubic> log lines 20 # Show last 20 log lines" -ForegroundColor Gray
    Write-Host "  HoloCubic> tree         # Show SD card directory tree" -ForegroundColor Gray
    Write-Host "  HoloCubic> tree /config 2 # Show config directory with 2 levels" -ForegroundColor Gray
    Write-Host "  HoloCubic> tree 5       # Show root directory with 5 levels" -ForegroundColor Gray
    Write-Host "  HoloCubic> dh           # Show device help" -ForegroundColor Gray
    Write-Host ""
}

# ==================== MAIN PROGRAM ====================
function Main() {
    Write-Host "HoloCubic CLI - Interactive Command Line Tool v2.0" -ForegroundColor Green
    Write-Host "Connecting to device..." -ForegroundColor Gray

    # Initialize components
    $config = [HoloCubicConfig]::new()
    $connection = [SerialConnectionManager]::new($ComPort, $BaudRate)
    $responseHandler = [CommandResponseHandler]::new($config)
    $executor = [CommandExecutor]::new($config, $connection, $responseHandler)

    # Connect to device
    if ($connection.Connect()) {
        Write-Host "Connected! You can now send commands." -ForegroundColor Green
    } else {
        Write-Host "Connection failed. Type 'reconnect' to try again." -ForegroundColor Red
    }

    Write-Host ""
    Show-Help

    # Main command loop
    $running = $true
    while ($running) {
        try {
            $status = if ($connection.IsConnected) { "[ON]" } else { "[OFF]" }
            $prompt = "$status HoloCubic> "
            $input = Read-Host -Prompt $prompt
            $input = $input.Trim().ToLower()

            if ([string]::IsNullOrWhiteSpace($input)) {
                continue
            }

            switch ($input) {
                "quit" { $running = $false; break }
                "exit" { $running = $false; break }
                "help" { Show-Help; continue }
                "test" { $executor.ExecuteCommand("test"); continue }
                "reconnect" {
                    $connection.Disconnect()
                    if ($connection.Connect()) {
                        Write-Host "Reconnected successfully!" -ForegroundColor Green
                    }
                    continue
                }
                "cls" { Clear-Host; continue }
            }

            # Device commands (sent to HoloCubic)
            $deviceCommands = @("log", "status", "clear", "tree", "dh", "device-help")
            $commandWord = $input.Split(' ')[0]

            if ($deviceCommands -contains $commandWord) {
                $deviceCommand = if ($input -eq "dh" -or $input -eq "device-help") { "help" } else { $input }
                $executor.ExecuteCommand($deviceCommand)
                continue
            }

            Write-Host "Unknown command: $input" -ForegroundColor Red
            Write-Host "Type 'help' for available commands" -ForegroundColor Gray
        }
        catch {
            Write-Host "Input error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    # Cleanup
    $connection.Disconnect()
    Write-Host ""
    Write-Host "Goodbye!" -ForegroundColor Green
}

# Run the main program
Main