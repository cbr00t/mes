def run():
    updateFiles()
    boot()

def updateFiles():
    from config import server as srv
    import core
    import os
    
    autoUpdate = srv.autoUpdate; url = srv.updateUrl
    if not (autoUpdate and url):
        return False
    dev = core.getDevice(); req = dev.req
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
            if fileContent and os.path.splitext(name)[1] == '.py':
                fileContent = fileContent.rstrip() + '\n'
            print(f'<< [{fileUrl}]')
            localFile = name; localBackupFile = f'{name}.bak'
            # Eğer önceki yedek varsa sil
            if os.path.exists(localBackupFile):
                os.remove(localBackupFile)
            # Önceki dosya varsa yedeğini oluştur
            if os.path.exists(localFile):
                os.rename(localFile, localBackupFile)
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
