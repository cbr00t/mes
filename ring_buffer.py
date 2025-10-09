# ==========================================================
# RingBuffer — sabit boyutlu, thread-safe, GC-siz FIFO buffer
# (c) cbr00t-MES common.utils
# ==========================================================

import _thread

class RingBuffer:
    """Sabit boyutlu, lock destekli, thread-safe FIFO buffer."""
    def __init__(self, size=64):
        self.size = size
        self.buf = [None] * size
        self.head = 0    # write pointer
        self.tail = 0    # read pointer
        self.lock = _thread.allocate_lock()
    # ------------------------------------------------------
    def push(self, item):
        """Yeni öğe ekle (True=eklendi, False=overflow)."""
        with self.lock:
            nxt = (self.head + 1) % self.size
            if nxt == self.tail:
                # Overflow -> eskiyi ezmek istersen self.tail = (self.tail + 1) % self.size
                return False
            self.buf[self.head] = item
            self.head = nxt
            return True
    # ------------------------------------------------------
    def pop(self):
        """İlk öğeyi al (None=boş)."""
        with self.lock:
            if self.tail == self.head:
                return None
            item = self.buf[self.tail]
            self.buf[self.tail] = None
            self.tail = (self.tail + 1) % self.size
            return item
    # ------------------------------------------------------
    def peek(self):
        """İlk öğeyi silmeden oku."""
        with self.lock:
            if self.tail == self.head:
                return None
            return self.buf[self.tail]
    # ------------------------------------------------------
    def clear(self):
        """Buffer'ı temizle."""
        with self.lock:
            self.head = self.tail = 0
            for i in range(self.size):
                self.buf[i] = None

    # ------------------------------------------------------
    @property
    def count(self):
        """Buffer'daki öğe sayısı."""
        with self.lock:
            if self.head >= self.tail:
                return self.head - self.tail
            return self.size - (self.tail - self.head)
    # ------------------------------------------------------
    @property
    def full(self):
        """Buffer dolu mu?"""
        with self.lock:
            return (self.head + 1) % self.size == self.tail
    # ------------------------------------------------------
    @property
    def empty(self):
        """Buffer boş mu?"""
        with self.lock:
            return self.head == self.tail
    # ------------------------------------------------------
    def __len__(self):
        return self.count
    def __bool__(self):
        """Falsy operator: boşsa False, doluysa True."""
        with self.lock:
            return self.head != self.tail
    def __iter__(self):
        """Thread-safe, heap-free iterator (FIFO sırası)."""
        # Mevcut head/tail snapshot alınır, böylece push/pop sırasında çakışma olmaz
        with self.lock:
            head = self.head
            tail = self.tail
            size = self.size
            buf = self.buf
        # snapshot sonrası sadece okunur erişim
        while tail != head:
            yield buf[tail]
            tail = (tail + 1) % size
    def __repr__(self):
        return f"<RingBuffer len={self.count()} size={self.size}>"
