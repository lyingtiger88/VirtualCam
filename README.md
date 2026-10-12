# BDFR VirtualCam v0.3

Windows graphical app with **live preview** from image, video, physical webcam, or desktop. Preview is independent of the virtual-camera backend.

## Run
Install Python 3.11/3.12 (64-bit), then run `install_and_run.bat`. Select a JPG/PNG or MP4 file; preview starts automatically. Use Preview for webcam/desktop.

## Virtual camera output
**Current limitation:** Virtual-camera output still requires the external Unity Capture driver. This repository is **not yet a fully native, standalone Windows virtual camera**. Image/video preview does not require it. When installed, click Start Virtual Camera and select Unity Video Capture in the target app.

## Build
Run `build_exe.bat`; executable is created at `dist\BDFR_VirtualCam.exe`. Windows build and driver behavior have not been tested in this environment.

## Windows 11 native development
A C++ Media Foundation virtual-camera registrar, CMake build scripts, Microsoft sample preparation, and a Windows build workflow have been added under [`native/`](native/README.md). **This is not yet a complete native BDFR virtual camera:** the custom media-source COM DLL and image-frame delivery still need implementation. The existing Python preview continues to run, and virtual-camera output remains Unity Capture-based until those parts are complete.

See [`native/README.md`](native/README.md) for the test procedure and exact limitations.

## Source
`app.py` — GUI and streaming loop; `requirements.txt` — Python dependencies.
