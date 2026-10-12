"""Windows shared-memory RGB24 producer for the future BDFR Media Source.
Does not register a webcam device. Reader and writer synchronize with a named mutex.
"""
import ctypes
import mmap
import struct

MAGIC=b"BDFR"
MAP_NAME="Local\\BDFRVirtualCamFramesV1"
MUTEX_NAME="Local\\BDFRVirtualCamFramesMutexV1"
HEADER=struct.Struct("<4sIIIIQI")  # magic, width, height, stride, byte count, sequence, pixel format
FORMAT_RGB24=1
WAIT_OBJECT_0=0
WAIT_ABANDONED=0x80
INFINITE=0xFFFFFFFF

class FrameBridge:
    def __init__(self,width,height):
        if ctypes.sizeof(ctypes.c_void_p)<8:
            raise RuntimeError("64-bit Python required")
        if not (1<=width<=3840 and 1<=height<=2160):
            raise ValueError("Unsupported bridge resolution")
        self.width=width
        self.height=height
        self.stride=width*3
        self.byte_count=self.stride*height
        self.sequence=0
        self.mapping=mmap.mmap(-1,HEADER.size+self.byte_count,tagname=MAP_NAME,access=mmap.ACCESS_WRITE)
        k=ctypes.WinDLL("kernel32",use_last_error=True)
        self.k=k
        k.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p]
        k.CreateMutexW.restype=ctypes.c_void_p
        k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
        k.WaitForSingleObject.restype=ctypes.c_uint32
        k.ReleaseMutex.argtypes=[ctypes.c_void_p]
        k.ReleaseMutex.restype=ctypes.c_int
        k.CloseHandle.argtypes=[ctypes.c_void_p]
        k.CloseHandle.restype=ctypes.c_int
        self.mutex=k.CreateMutexW(None,False,MUTEX_NAME)
        if not self.mutex:
            self.mapping.close()
            raise OSError(ctypes.get_last_error(),"CreateMutexW failed")
        self.publish_bytes(bytes(self.byte_count))

    def publish_bytes(self,raw):
        if len(raw)!=self.byte_count:
            raise ValueError("Expected exact RGB24 buffer")
        state=self.k.WaitForSingleObject(self.mutex,1000)
        if state not in (WAIT_OBJECT_0,WAIT_ABANDONED):
            raise TimeoutError("Frame bridge mutex unavailable")
        try:
            self.sequence+=1
            self.mapping.seek(0)
            self.mapping.write(HEADER.pack(MAGIC,self.width,self.height,self.stride,self.byte_count,self.sequence,FORMAT_RGB24))
            self.mapping.write(raw)
        finally:
            self.k.ReleaseMutex(self.mutex)

    def publish(self,rgb):
        if rgb.shape!=(self.height,self.width,3) or rgb.dtype.name!="uint8":
            raise ValueError("Frame must be RGB uint8 in configured resolution")
        self.publish_bytes(rgb.tobytes(order="C"))

    def close(self):
        if self.mapping:
            self.mapping.close()
            self.mapping=None
        if self.mutex:
            self.k.CloseHandle(self.mutex)
            self.mutex=None
