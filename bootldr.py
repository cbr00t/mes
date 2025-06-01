from common import *
from config import server as srv
import json
from time import sleep
from os import rename, remove
from traceback import print_exception

def run():
    globalInit(); dev = shared.dev; lcd = dev.lcd
    lcd.off(); lcd.on()
    ethWait(); updateFiles()
    boot()

def ethWait():
    dev = shared.dev; eth = dev.eth; lcd = dev.lcd
    if not lcdIsBusy():
        lcd.clearLine(1); lcd.write('Ethernet bekleniyor...', 1, 1)
    while not eth.isConnected():
        print('waiting for ethernet conn')
    sleep(0.2)
def updateFiles():
    autoUpdate = srv.autoUpdate; urls = getUpdateUrls()
    if autoUpdate is None: autoUpdate = shared.updateCheck != False
    if autoUpdate is None: autoUpdate = False
    if not (autoUpdate and urls):
        return False
    
    dev = shared.dev; eth = dev.eth; sock = dev.sock; lcd = dev.lcd
    busy()
    if not sock.isConnected():
        sock.open()
    # if sock.isConnected(): wsHeartbeat()
    if not sock.isConnected():
        return False
    
    if not lcdIsBusy():
        lcd.clearLine(1)
        lcd.write('UPDATE CHECK', 1, 1)
    url = None; lastError = None
    for _url in urls:
        if not _url: continue
        try:
            # resp = req.sendText(f'{_url}/files.txt')
            resp = sock.wsTalk('webRequest', None, { 'url': f'{_url}/files.txt' })
            print(f'<< resp', resp)
            resp = resp['data']['string'] if isinstance(resp, dict) else None
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
    for name in resp.split('\n'):
        name = name.strip()
        if not name: continue
        try:
            busy(); fileUrl = f'{url}/{name}'
            if not lcdIsBusy():
                lcd.clear(); lcd.write('UPDATING:', 0, 0)
                lcd.write(name, 1, 2)
            # Uzak Dosyayı indir
            fileContent = sock.wsTalk('webRequest', None, { 'url': fileUrl })
            fileContent = fileContent['data']['string'] if isinstance(fileContent, dict) else None
            # fileContent = textReq(fileUrl)
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
            with open(localFile, 'w') as f:
                f.write(fileContent)
            print('  ... UPDATED')
        except Exception as ex:
            print('[ERROR]', ex); print_exception(ex)
            continue
    if not lcdIsBusy():
        lcd.clear()
    sock.close()
    return True

def boot():
    import app
    app.init()
    app.run()

