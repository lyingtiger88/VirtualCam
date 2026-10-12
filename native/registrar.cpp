// Windows 11 Media Foundation virtual-camera registration utility.
// This does NOT provide frames; a registered COM IMFMediaSource DLL is required.
#include <windows.h>
#include <mfapi.h>
#include <mfvirtualcamera.h>
#include <iostream>
#include <string>
#include <cwchar>

static void Fail(const wchar_t* step, HRESULT hr) {
    std::wcerr << step << L" failed: HRESULT 0x" << std::hex
               << static_cast<unsigned long>(hr) << std::endl;
}
static bool IsClsid(const wchar_t* str) {
    GUID id{};
    return str && SUCCEEDED(CLSIDFromString(str, &id));
}
int wmain(int argc, wchar_t** argv) {
    if (argc != 3 || (wcscmp(argv[1], L"install") && wcscmp(argv[1], L"remove"))) {
        std::wcerr << L"Usage: BDFRVCamRegistrar install|remove {REGISTERED-MEDIA-SOURCE-CLSID}\n"
                   << L"Media source must already be installed and registered (HKLM COM).\n";
        return 2;
    }
    if (!IsClsid(argv[2])) {
        std::wcerr << L"Invalid source CLSID. Use {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}\n";
        return 2;
    }
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(hr)) { Fail(L"CoInitializeEx", hr); return 1; }
    hr = MFStartup(MF_VERSION);
    if (FAILED(hr)) { Fail(L"MFStartup", hr); CoUninitialize(); return 1; }

    IMFVirtualCamera* cam = nullptr;
    hr = MFCreateVirtualCamera(
        MFVirtualCameraType_SoftwareCameraSource,
        MFVirtualCameraLifetime_System,
        MFVirtualCameraAccess_CurrentUser,
        L"BDFR VirtualCam",
        argv[2],
        nullptr, 0, &cam);
    if (SUCCEEDED(hr)) {
        if (wcscmp(argv[1], L"install") == 0) {
            hr = cam->Start(nullptr);
            if (SUCCEEDED(hr)) {
                std::wcout << L"BDFR VirtualCam registration started. Check Windows Camera.\n";
            } else Fail(L"IMFVirtualCamera::Start", hr);
        } else {
            hr = cam->Remove();
            if (SUCCEEDED(hr)) std::wcout << L"BDFR VirtualCam removed.\n";
            else Fail(L"IMFVirtualCamera::Remove", hr);
        }
        cam->Shutdown();
        cam->Release();
    } else {
        Fail(L"MFCreateVirtualCamera", hr);
    }
    MFShutdown();
    CoUninitialize();
    return FAILED(hr) ? 1 : 0;
}
