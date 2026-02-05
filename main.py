import sqlite3, binascii, ctypes
from ctypes import wintypes

DB = r"C:\Users\James\xwechat_files\all_users\login\wxid_lvoshukxr2ya32\key_info.db"

# --- DPAPI via CryptUnprotectData ---
crypt32 = ctypes.windll.crypt32
kernel32 = ctypes.windll.kernel32

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_byte))]

def unprotect(data: bytes) -> bytes:
    in_blob = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_byte)))
    out_blob = DATA_BLOB()
    if not crypt32.CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
        raise ctypes.WinError()
    try:
        buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
        return buf
    finally:
        kernel32.LocalFree(out_blob.pbData)

con = sqlite3.connect(DB)
cur = con.cursor()
rows = cur.execute("select rowid, user_name_md5, key_info_md5, key_info_data from LoginKeyInfoTable").fetchall()
con.close()

print("rows", len(rows))
ok = 0
for rowid, user_md5, info_md5, blob in rows:
    try:
        plain = unprotect(blob)
        ok += 1
        print(f"\nrowid={rowid} user_md5={user_md5} info_md5={info_md5}")
        print("plain_len", len(plain))
        print("plain_hex", binascii.hexlify(plain).decode())
    except Exception as e:
        pass

print("\nDPAPI_unprotect_ok", ok)



