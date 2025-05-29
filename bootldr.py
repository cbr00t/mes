from common import *
from config import server as srv
import core
from os import rename, remove

def run():
    global dev
    dev = core.getDevice()
    updateFiles()
    boot()

def updateFiles():
    global dev
    autoUpdate = srv.autoUpdate; url = srv.updateUrl
    if not (autoUpdate and url):
        return False
    req = dev.req
    try:
        resp = req.sendText(f'{url}/files.txt')
        # Update List yok ise: oto-update iptal
        if 'Not found' in resp: return False
    except Exception as ex:
        print(ex)
        return False
    
    for name in resp.split('\n'):
        name = name.strip()
        if not name:
            continue
        try:
            fileUrl = f'{url}/{name}'
            # Uzak Dosyayı indir
            fileContent = req.sendText(fileUrl)
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
    return True

def boot():
    import app
    app.init()
    app.run()
