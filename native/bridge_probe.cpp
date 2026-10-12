// Diagnostic client for the frame transport. NOT a virtual-camera Media Source.
#include <windows.h>
#include <cstdint>
#include <cstring>
#include <iostream>
#pragma pack(push,1)
struct Header {
  char magic[4];
  uint32_t width,height,stride,size;
  uint64_t sequence;
  uint32_t pixelFormat;
};
#pragma pack(pop)
static_assert(sizeof(Header)==32,"bridge header size must match Python");
int wmain() {
  HANDLE mutex=OpenMutexW(SYNCHRONIZE | MUTEX_MODIFY_STATE,FALSE,L"Local\\BDFRVirtualCamFramesMutexV1");
  HANDLE mapping=OpenFileMappingW(FILE_MAP_READ,FALSE,L"Local\\BDFRVirtualCamFramesV1");
  if (!mutex||!mapping) {
    std::wcerr << L"Bridge not present. Run BDFR VirtualCam with an image or video.\n";
    if (mutex) CloseHandle(mutex);
    if (mapping) CloseHandle(mapping);
    return 2;
  }
  auto* view=static_cast<const unsigned char*>(MapViewOfFile(mapping,FILE_MAP_READ,0,0,0));
  if (!view) { std::cerr << "MapViewOfFile failed\n";CloseHandle(mapping);CloseHandle(mutex);return 3; }
  int result=0;
  for (int i=0;i<10;++i) {
    DWORD status=WaitForSingleObject(mutex,1500);
    if (status!=WAIT_OBJECT_0&&status!=WAIT_ABANDONED) {std::cerr<<"Mutex timeout\n";result=4;break;}
    Header h{};
    std::memcpy(&h,view,sizeof(h));
    bool valid=std::memcmp(h.magic,"BDFR",4)==0 && h.width>=1 && h.width<=3840 &&
      h.height>=1 && h.height<=2160 && h.stride==h.width*3 &&
      h.size==static_cast<uint64_t>(h.stride)*h.height && h.pixelFormat==1;
    if (valid) {
      volatile uint8_t sample=view[sizeof(h)]; (void)sample;
      std::cout<<"RGB24 "<<h.width<<"x"<<h.height<<" frame #"<<h.sequence<<" bytes "<<h.size<<"\n";
    } else {std::cerr<<"Invalid frame header\n";result=5;}
    ReleaseMutex(mutex);
    if (result)break;
    Sleep(200);
  }
  UnmapViewOfFile(view);CloseHandle(mapping);CloseHandle(mutex);
  return result;
}
