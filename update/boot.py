import storage
try:
    storage.remount("/", readonly=False, disable_concurrent_write_protection=True)
    print('boot success')
except Exception as ex:
    print(f'[BOOT]  {ex}')
