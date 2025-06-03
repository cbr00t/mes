from common import *
from config import local, server as srv, hw
from time import sleep, monotonic
from os import rename, remove
import json
import gc

def updateFiles():
    global dev, lcd, sock
    dev = shared.dev
    lcd = dev.lcd; sock = dev.sock
    shared._updateCheckPerformed = True
    autoUpdate = srv.autoUpdate; urls = getUpdateUrls()
    if autoUpdate is None: autoUpdate = shared.updateCheck != False
    if autoUpdate is None: autoUpdate = False
    if not (autoUpdate and urls):
        return False
    
    if not lcdIsBusy():
        lcd.clearLine(range(1, 3)); lcd.write('UPDATE CHECK', 1, 1)
    url = None; lastError = None
    for _url in urls:
        if not _url: continue
        try:
            resp = sock.wsTalk('webRequest', None, { 'url': f'{_url}/files.txt', 'output': 'str', 'stream': False }, timeout=3)
            print(f'<< resp', resp)
            resp = resp['data']['string'] if isinstance(resp, dict) else None
            # if resp:
            #     try: resp = from64(resp.encode(encoding))
            #     except Exception as ex: print(ex); continue
            # Update List yok ise: oto-update iptal
            if not resp or 'not found' in resp.lower():
                print('[INFO]', "'files.txt' not found, skipping...")
                continue
            url = _url; lastError = None
            break
        except Exception as ex:
            lastError = ex; print(f'[ERROR]', ex)
            continue
    if lastError:
        print('[ERROR]', lastError); print_exception(lastError)
    if lastError or not url:
        return False
    for name in resp.splitlines():
        name = name.strip()
        if not name: continue
        try:
            busy(); fileUrl = f'{url}/{name}'
            if not lcdIsBusy():
                lcd.clearLine(range(1, 3)); lcd.write('UPDATING:', 1, 1)
                lcd.write(name, 2, 5)
            # Uzak Dosyayı indir
            fileContent = sock.wsTalk('webRequest', None, { 'url': fileUrl, 'output': 'str', 'stream': False }, timeout=5)
            fileContent = fileContent['data']['string'] if isinstance(fileContent, dict) else None
            gc.collect()
            if fileContent:
                if fileContent: fileContent = fileContent.replace('\r', '')
                # try:
                #     fileContent = from64(fileContent.encode(encoding))
                #     if fileContent: fileContent = fileContent.replace('\r', '')
                #     gc.collect()
                # except Exception as ex2:
                #     print(ex2); continue
            # Yanıt boş veya yok ise sonrakine geç
            if not fileContent or 'Not found' in fileContent:
                print('  ... NOT FOUND')
                continue
            if fileContent and splitext(name)[1] == '.py':
                fileContent = fileContent.rstrip() + '\n'
            print(f'<< [{fileUrl}]')
            localFile = name; localBackupFile = f'{name}.bak'
            # Eğer önceki yedek varsa sil
            if exists(localBackupFile):
                remove(localBackupFile)
            # Önceki dosya varsa yedeğini oluştur
            if exists(localFile):
                rename(localFile, localBackupFile)
            # Yeni içerikle dosyayı yaz
            success = False
            print(f'    file: {localFile}')
            with open(localFile, 'w', encoding=encoding) as f:
                try:
                    f.write(fileContent); success = True
                    lcd.write('OK', 1, 0)
                    print('        ...  UPDATED')
                except Exception as ex2:
                    lcd.write('ERR', 1, 0)
                    print('        ...', ex2)
            if not success and exists(localBackupFile):
                remove(localFile)
                rename(localBackupFile, localFile)
            gc.collect()
        except Exception as ex:
            print('[ERROR]', ex); print_exception(ex)
            continue
    return True
