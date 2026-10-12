$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if ([Environment]::OSVersion.Version.Build -lt 22000) {
    throw "Windows 11 build 22000+ required."
}
cmake -S . -B build -A x64
if ($LASTEXITCODE -ne 0) { throw "CMake configure failed. Install Visual Studio 2022 C++ Desktop workload and Windows 11 SDK." }
cmake --build build --config Release
if ($LASTEXITCODE -ne 0) { throw "CMake build failed." }
Write-Host "Registrar: $PSScriptRoot\build\Release\BDFRVCamRegistrar.exe"
