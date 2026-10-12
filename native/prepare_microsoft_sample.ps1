# Fetch the official Microsoft sample, WITHOUT silently registering third-party code.
# The sample is reference / synthetic camera until a BDFR Media Source is developed.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$destination = Join-Path $PSScriptRoot "upstream-Windows-Camera"
if (!(Test-Path $destination)) {
    git clone --depth 1 https://github.com/microsoft/Windows-Camera.git $destination
    if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }
}
$sample = Join-Path $destination "Samples\VirtualCamera"
Write-Host "Official Microsoft reference sample: $sample"
Write-Host "Open its Visual Studio solution. Build VirtualCameraMediaSource and VirtualCamera_Installer, then install the registered media-source DLL as documented by Microsoft."
Write-Host "The BDFR registrar requires the CLSID of the INSTALLED custom media source."
