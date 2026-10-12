# BDFR VirtualCam — Windows 11 native track (work in progress)

**Status:** Registrar source and CMake build have been committed. The actual BDFR Media Source (COM DLL) and frame transport have **not** been implemented. Do not confuse camera registration with a functional image-delivering camera.

## Requirements
Windows 11 build 22000+, Visual Studio 2022 Desktop development with C++, Windows 11 SDK, CMake. A registered virtual-camera-compatible `IMFMediaSource` COM DLL is required.

## Native proof of concept
1. Run `powershell -ExecutionPolicy Bypass -File .\native\prepare_microsoft_sample.ps1` to clone Microsoft's sample separately. Review its license and build instructions.
2. Build/install Microsoft's synthetic Media Source using its prescribed project/MSI workflow.
3. Run `powershell -ExecutionPolicy Bypass -File .\native\build_native.ps1`.
4. Find the actual installed source CLSID in Microsoft's sample source/COM registration. From a command prompt, run:
   `native\build\Release\BDFRVCamRegistrar.exe install "{YOUR-REGISTERED-SOURCE-CLSID}"`
5. Open Windows Camera and select BDFR VirtualCam. The picture, **if functional**, is still Microsoft's synthetic test pattern; it is NOT connected to BDFR's image preview.
6. Remove the camera with `BDFRVCamRegistrar.exe remove "{SAME-CLSID}"`.

Never supply a random GUID or claim that registration alone creates a functional virtual-camera media source.

## Remaining implementation work
- Build a distinct BDFR source COM DLL (activate, stream, media types, samples, timestamps, lifecycle, registry installation).
- Connect that source to the Python app through securely scoped shared memory and synchronization.
- Package and sign installer; test in Windows Camera / browser / conferencing applications.
- Expose native output state in the GUI and remove UnityCapture dependency.

References:
- https://github.com/microsoft/Windows-Camera/tree/master/Samples/VirtualCamera
- https://learn.microsoft.com/windows/win32/api/mfvirtualcamera/nf-mfvirtualcamera-mfcreatevirtualcamera
