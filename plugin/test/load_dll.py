import ctypes
from ctypes import wintypes


def print_dll_version(dll_name="GameInput.dll"):
    """Load a DLL by name and print its resolved path and file version."""

    # Load the DLL (resolved via standard Windows DLL search order).
    dll = ctypes.WinDLL(dll_name)

    # Resolve the actual on-disk path behind the loaded handle.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel32.GetModuleFileNameW.restype = wintypes.DWORD

    path_buf = ctypes.create_unicode_buffer(260)
    n = kernel32.GetModuleFileNameW(wintypes.HMODULE(dll._handle), path_buf, len(path_buf))
    if n == 0:
        raise ctypes.WinError(ctypes.get_last_error())
    path = path_buf.value

    # Pull the file version resource (this is what Explorer shows under
    # Properties -> Details -> File version).
    version_dll = ctypes.WinDLL("version", use_last_error=True)

    size = version_dll.GetFileVersionInfoSizeW(path, None)
    if size == 0:
        raise ctypes.WinError(ctypes.get_last_error())

    buf = ctypes.create_string_buffer(size)
    if not version_dll.GetFileVersionInfoW(path, 0, size, buf):
        raise ctypes.WinError(ctypes.get_last_error())

    value_ptr = ctypes.c_void_p()
    value_size = wintypes.UINT()
    if not version_dll.VerQueryValueW(buf, "\\", ctypes.byref(value_ptr), ctypes.byref(value_size)):
        raise ctypes.WinError(ctypes.get_last_error())

    # VS_FIXEDFILEINFO layout: dwFileVersionMS/LS hold the four version
    # numbers packed as two 16-bit halves each.
    ffi = ctypes.cast(value_ptr, ctypes.POINTER(ctypes.c_uint32 * 13)).contents
    ms, ls = ffi[2], ffi[3]  # dwFileVersionMS, dwFileVersionLS
    version = (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)

    print(f"DLL:     {dll_name}")
    print(f"Path:    {path}")
    print(f"Version: {'.'.join(str(part) for part in version)}")

    return path, version


print_dll_version(r"C:\Program Files\Microsoft GameInput\x64\GameInputRedist.dll")
