import storage
try:
    storage.remount("/", readonly=False)
except Exception as ex:
    print(f'[BOOT]  {ex}')
