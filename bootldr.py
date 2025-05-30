from common import *
from config import server as srv
import core
from appHandlers import AppHandlers
from os import rename, remove

def run():
    global dev, handlers
    dev = core.getDevice()
    handlers = AppHandlers(dev)
    updateFiles()
    boot()

def updateFiles():
    autoUpdate = srv.autoUpdate; urls = getUpdateUrls()
    if autoUpdate is None:
        autoUpdate = (dev.autoUpdate if 'autoUpdate' in dev else None)
    if autoUpdate is None:
        autoUpdate = False
    if not (autoUpdate and urls):
        return False
    
    handlers.lcdClear(); handlers.lcdWrite('UPDATE CHECK', 0, 0)
    url = None; lastError = None
    for _url in urls:
        if not _url:
            continue
        try:
            resp = handlers.textReq(f'{_url}/files.txt')
            # Update List yok ise: oto-update iptal
            if 'Not found' in resp:
                continue
            url = _url; lastError = None
            break
        except Exception as ex:
            lastError = ex
            continue
    
    if lastError:
        print(lastError)
    if lastError or not url:
        return False
    
    for name in resp.split('\n'):
        name = name.strip()
        if not name:
            continue
        try:
            fileUrl = f'{url}/{name}'
            handlers.lcdClear(); handlers.lcdWrite('UPDATING:', 0, 0)
            handlers.lcdWrite(name, 1, 2)
            # Uzak Dosyayı indir
            fileContent = handlers.textReq(fileUrl)
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
            print(ex)
            continue
    handlers.lcdClear()
    return True

def boot():
    import app
    app.init()
    app.run()

