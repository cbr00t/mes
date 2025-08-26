# keypad_handler2.py - Kısa tuş basışları için optimize edilmiş
# Adafruit Matrix_Keypad kütüphanesini kullanarak
# 'interval' parametresi olmadan çalışacak versiyon

import time
from adafruit_matrixkeypad import Matrix_Keypad

class KeypadHandler:
    def __init__(self, row_pins, col_pins, keys, on_press, on_release):
        # Standart başlatma, ek parametreler yok
        self.keypad = Matrix_Keypad(row_pins, col_pins, keys)
        self.on_press = on_press
        self.on_release = on_release
        self._pressed = {}
        
        # Performans için ek değişkenler
        self._last_scan_time = time.monotonic()
        self._min_scan_interval = 0.0002  # 2ms - optimal tarama sıklığı
        
    def update(self):
        now = time.monotonic()
        
        # Daha sık tarama için, her çağrıda değil, minimum aralıktan sonra tara
        elapsed = now - self._last_scan_time
        if elapsed < self._min_scan_interval:
            # Çok fazla CPU kullanmamak için küçük bir bekleme
            # time.sleep(0.0001)  # 0.1ms bekleme - isteğe bağlı
            return
            
        # Zamanı güncelle
        self._last_scan_time = now
        
        try:
            # Ana tarama kodunu hata yakalama içine al
            current_keys = set(self.keypad.pressed_keys)
            
            # Basılan yeni tuşları algıla
            for key in current_keys:
                if key not in self._pressed:
                    self._pressed[key] = now
                    if self.on_press:
                        self.on_press(key)
            
            # Bırakılan tuşları kontrol et
            released_keys = [key for key in self._pressed if key not in current_keys]
            
            for key in released_keys:
                pressed_time = self._pressed.pop(key)
                duration = now - pressed_time
                
                # Tüm tuş bırakma olaylarını işle
                if self.on_release:
                    # 3 ondalık basamak hassasiyet (milisaniye)
                    self.on_release(key, duration)
                    
        except Exception as e:
            # Herhangi bir hata olursa sessizce devam et
            print(f"Keypad tarama hatası: {e}")