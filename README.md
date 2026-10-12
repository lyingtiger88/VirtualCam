# BDFR VirtualCam v0.3

Windows graphical app with **live preview** from image, video, physical webcam, or desktop. Preview is independent of the virtual-camera backend.

## Run
Install Python 3.11/3.12 (64-bit), then run `install_and_run.bat`. Select a JPG/PNG or MP4 file; preview starts automatically. Use Preview for webcam/desktop.

## Virtual camera output
**Current limitation:** Virtual-camera output still requires the external Unity Capture driver. This repository is **not yet a fully native, standalone Windows virtual camera**. Image/video preview does not require it. When installed, click Start Virtual Camera and select Unity Video Capture in the target app.

## Build
Run `build_exe.bat`; executable is created at `dist\BDFR_VirtualCam.exe`. Windows build and driver behavior have not been tested in this environment.

## Planned native release
Replace Unity Capture with a Windows Media Foundation virtual-camera media source + registration layer, providing a dedicated BDFR VirtualCam device name.

## Source
`app.py` — GUI and streaming loop; `requirements.txt` — Python dependencies.
