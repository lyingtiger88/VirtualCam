"""BDFR VirtualCam v0.3 — preview independent of virtual-camera backend."""
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import cv2
import mss
import numpy as np
import pyvirtualcam
from PIL import Image, ImageTk

SIZES = {"640x480": (640,480), "1280x720": (1280,720), "1920x1080": (1920,1080)}

class VirtualCamApp:
    def __init__(self, root):
        self.root=root
        root.title("BDFR VirtualCam • v0.3")
        root.geometry("980x680")
        self.stop_event=None
        self.worker=None
        self.running=False
        self.lock=threading.Lock()
        self.latest=None
        self.messages=[]
        self.source=tk.StringVar(value="Webcam")
        self.index=tk.StringVar(value="0")
        self.path=tk.StringVar()
        self.size=tk.StringVar(value="1280x720")
        self.fps=tk.StringVar(value="30")
        self.loop=tk.BooleanVar(value=True)
        self.mirror=tk.BooleanVar(value=False)
        self.gray=tk.BooleanVar(value=False)
        self.brightness=tk.DoubleVar(value=0)
        self.overlay=tk.StringVar()
        self.status=tk.StringVar(value="Ready — preview needs no virtual camera driver")
        self.build_ui()
        root.after(60,self.tick)
        root.protocol("WM_DELETE_WINDOW",self.close)

    def build_ui(self):
        style=ttk.Style()
        if "clam" in style.theme_names():style.theme_use("clam")
        area=ttk.Frame(self.root,padding=15)
        area.pack(fill="both",expand=True)
        ttk.Label(area,text="BDFR VirtualCam v0.3",font=("Segoe UI",20,"bold")).pack(anchor="w")
        content=ttk.Frame(area)
        content.pack(fill="both",expand=True,pady=10)
        left=ttk.Frame(content,width=310)
        left.pack(side="left",fill="y",padx=(0,15))
        left.pack_propagate(False)
        right=ttk.Frame(content)
        right.pack(side="left",fill="both",expand=True)
        ttk.Label(left,text="Input source").pack(anchor="w")
        for kind in ("Webcam","Video","Image","Desktop"):
            ttk.Radiobutton(left,text=kind,variable=self.source,value=kind).pack(anchor="w")
        ttk.Label(left,text="Webcam index").pack(anchor="w",pady=(8,0))
        ttk.Entry(left,textvariable=self.index).pack(fill="x")
        ttk.Button(left,text="Choose image / video",command=self.choose).pack(fill="x",pady=8)
        ttk.Label(left,textvariable=self.path,wraplength=300).pack(anchor="w")
        ttk.Label(left,text="Output resolution").pack(anchor="w",pady=(8,0))
        ttk.Combobox(left,textvariable=self.size,values=list(SIZES),state="readonly").pack(fill="x")
        ttk.Label(left,text="FPS").pack(anchor="w")
        ttk.Combobox(left,textvariable=self.fps,values=("15","24","30","60"),state="readonly").pack(fill="x")
        for label,var in (("Loop video",self.loop),("Mirror",self.mirror),("Grayscale",self.gray)):
            ttk.Checkbutton(left,text=label,variable=var).pack(anchor="w")
        ttk.Label(left,text="Brightness").pack(anchor="w")
        ttk.Scale(left,variable=self.brightness,from_=-90,to=90).pack(fill="x")
        ttk.Label(left,text="Text overlay").pack(anchor="w")
        ttk.Entry(left,textvariable=self.overlay).pack(fill="x")
        self.preview_button=ttk.Button(left,text="Preview (no driver needed)",command=lambda:self.start(False))
        self.preview_button.pack(fill="x",pady=(14,3))
        self.virtual_button=ttk.Button(left,text="Start Virtual Camera",command=lambda:self.start(True))
        self.virtual_button.pack(fill="x",pady=3)
        self.stop_button=ttk.Button(left,text="Stop",command=self.stop,state="disabled")
        self.stop_button.pack(fill="x",pady=3)
        ttk.Label(right,text="Live preview").pack(anchor="w")
        self.preview=tk.Label(right,text="Choose an image / video or click Preview",bg="#101720",fg="white")
        self.preview.pack(fill="both",expand=True,pady=6)
        ttk.Label(area,textvariable=self.status,wraplength=930).pack(anchor="w")

    def choose(self):
        path=filedialog.askopenfilename(filetypes=[("Media","*.png *.jpg *.jpeg *.bmp *.mp4 *.mkv *.avi *.mov *.webm"),("All files","*.*")])
        if path:
            self.path.set(path)
            ext=os.path.splitext(path)[1].lower()
            self.source.set("Image" if ext in (".png",".jpg",".jpeg",".bmp") else "Video")
            self.start(False)

    def notify(self,msg):
        with self.lock:self.messages.append(msg)

    def start(self,virtual):
        mode=self.source.get()
        path=self.path.get()
        if mode in ("Video","Image") and not os.path.isfile(path):
            messagebox.showerror("Missing file","Choose a valid image or video first")
            return
        try:
            options=dict(size=SIZES[self.size.get()],fps=int(self.fps.get()),
                         index=int(self.index.get()),mirror=self.mirror.get(),
                         gray=self.gray.get(),loop=self.loop.get(),
                         brightness=int(self.brightness.get()),overlay=self.overlay.get().strip())
            if options["fps"]<=0 or options["index"]<0:raise ValueError("Invalid FPS or webcam index")
        except (KeyError,ValueError) as exc:
            messagebox.showerror("Settings",str(exc))
            return
        previous=self.worker
        if self.stop_event:self.stop_event.set()
        event=threading.Event()
        self.stop_event=event
        self.running=True
        self.preview_button.configure(state="disabled")
        self.virtual_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.notify("Opening camera output…" if virtual else "Opening preview…")
        def run():
            if previous and previous.is_alive():previous.join(timeout=2)
            if not event.is_set():self.stream(mode,path,options,virtual,event)
        self.worker=threading.Thread(target=run,daemon=True)
        self.worker.start()

    def stop(self):
        if self.stop_event:self.stop_event.set()
        self.notify("Stopping…")

    @staticmethod
    def fit(frame,w,h):
        fh,fw=frame.shape[:2]
        if not fh or not fw:raise ValueError("Empty frame")
        scale=max(w/fw,h/fh)
        sw,sh=max(w,round(fw*scale)),max(h,round(fh*scale))
        resized=cv2.resize(frame,(sw,sh),interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_LINEAR)
        x,y=(sw-w)//2,(sh-h)//2
        return resized[y:y+h,x:x+w]

    def stream(self,mode,path,opt,virtual,event):
        capture=screen=camera=None
        try:
            w,h=opt["size"]
            fps=opt["fps"]
            still=None
            if mode=="Webcam":
                capture=cv2.VideoCapture(opt["index"],cv2.CAP_DSHOW if os.name=="nt" else cv2.CAP_ANY)
                if not capture.isOpened():raise RuntimeError("Cannot open webcam "+str(opt["index"]))
                capture.set(cv2.CAP_PROP_FRAME_WIDTH,w)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT,h)
            elif mode=="Video":
                capture=cv2.VideoCapture(path)
                if not capture.isOpened():raise RuntimeError("Cannot read video; try H.264 MP4")
            elif mode=="Image":
                still=cv2.imdecode(np.fromfile(path,dtype=np.uint8),cv2.IMREAD_COLOR)
                if still is None:raise RuntimeError("Cannot decode image; try JPEG/PNG")
            elif mode=="Desktop":
                screen=mss.mss()
            if virtual:
                try:
                    camera=pyvirtualcam.Camera(width=w,height=h,fps=fps,fmt=pyvirtualcam.PixelFormat.RGB,backend="unitycapture")
                    self.notify("Virtual camera active: "+camera.device)
                except Exception as exc:
                    self.notify("Preview ONLY — Unity Capture unavailable: "+str(exc))
            else:self.notify("Preview running — no driver required")
            next_time=time.monotonic()
            while not event.is_set():
                if mode=="Image":frame=still.copy()
                elif mode=="Desktop":
                    frame=cv2.cvtColor(np.asarray(screen.grab(screen.monitors[1])),cv2.COLOR_BGRA2BGR)
                else:
                    ok,frame=capture.read()
                    if not ok and mode=="Video" and opt["loop"]:
                        capture.set(cv2.CAP_PROP_POS_FRAMES,0)
                        ok,frame=capture.read()
                    if not ok:
                        self.notify("End of video / source disconnected")
                        break
                frame=self.fit(frame,w,h)
                if opt["mirror"]:frame=cv2.flip(frame,1)
                if opt["gray"]:frame=cv2.cvtColor(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),cv2.COLOR_GRAY2BGR)
                if opt["brightness"]:
                    frame=np.clip(frame.astype(np.int16)+opt["brightness"],0,255).astype(np.uint8)
                if opt["overlay"]:
                    cv2.putText(frame,opt["overlay"],(30,h-40),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),5,cv2.LINE_AA)
                    cv2.putText(frame,opt["overlay"],(30,h-40),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2,cv2.LINE_AA)
                rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                if camera:
                    try:camera.send(np.ascontiguousarray(rgb))
                    except Exception as exc:
                        self.notify("Virtual output stopped; preview continues: "+str(exc))
                        camera.close()
                        camera=None
                with self.lock:
                    self.latest=cv2.resize(rgb,(640,360),interpolation=cv2.INTER_AREA)
                next_time+=1/fps
                delay=next_time-time.monotonic()
                if delay>0:event.wait(delay)
                else:next_time=time.monotonic()
        except Exception as exc:self.notify("ERROR: "+str(exc))
        finally:
            if camera:camera.close()
            if capture:capture.release()
            if screen:screen.close()
            if self.stop_event is event:self.running=False

    def tick(self):
        with self.lock:
            frame=self.latest
            self.latest=None
            messages=self.messages[:]
            self.messages.clear()
        if frame is not None:
            photo=ImageTk.PhotoImage(Image.fromarray(frame))
            self.preview.configure(image=photo,text="")
            self.preview.image=photo
        if messages:self.status.set(messages[-1])
        if not self.running:
            self.preview_button.configure(state="normal")
            self.virtual_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
        self.root.after(60,self.tick)

    def close(self):
        if self.stop_event:self.stop_event.set()
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk()
    VirtualCamApp(root)
    root.mainloop()
