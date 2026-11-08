$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$csv = Import-Csv (Join-Path $root "SOURCES.csv")
$report = @()

foreach ($row in $csv) {
    $folderMap = @{
        "AUTOSAR_SRS_CAN.pdf" = "01_CAN_Network"
        "AUTOSAR_SRS_COM.pdf" = "02_Communication"
        "AUTOSAR_SRS_NetworkManagement.pdf" = "03_Network_Management"
        "AUTOSAR_SRS_FlexRay.pdf" = "04_FlexRay_Network"
        "AUTOSAR_SRS_Gateway.pdf" = "05_Network_Gateway"
        "AUTOSAR_SRS_Ethernet.pdf" = "06_Ethernet"
        "AUTOSAR_SRS_CryptoStack.pdf" = "07_Cryptography"
        "AUTOSAR_SRS_SecureOnboardCommunication.pdf" = "08_Secure_Communication"
        "AUTOSAR_SRS_V2XCommunication.pdf" = "09_V2X"
        "AUTOSAR_SRS_XCP.pdf" = "10_XCP_Network_Protocol"
    }
    $folder = Join-Path $root $folderMap[$row.Filename]
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    $target = Join-Path $folder ("{0}_{1}" -f $row.Release, $row.Filename)

    $status = "FAILED"
    $used = ""
    foreach ($url in @($row.Primary_URL, $row.Fallback_URL)) {
        if ([string]::IsNullOrWhiteSpace($url)) { continue }
        try {
            Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing -TimeoutSec 90
            if ((Test-Path $target) -and ((Get-Item $target).Length -gt 10000)) {
                $status = "DOWNLOADED"
                $used = $url
                break
            }
        } catch {}
    }
    $report += [pscustomobject]@{
        No=$row.No; Document=$row.Document; Release=$row.Release; Status=$status; URL=$used; Target=$target
    }
}
$report | Export-Csv (Join-Path $root "DOWNLOAD_REPORT.csv") -NoTypeInformation -Encoding UTF8
Write-Host ""
Write-Host "Finished. Check DOWNLOAD_REPORT.csv"
Read-Host "Press Enter to close"
