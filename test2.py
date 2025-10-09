from time import sleep
import _thread
buf = ['', '', '']

# core1
def thread_proc():
    while True:
        sleep(.5)
        buf[0] = 'c'
        buf[1] = 'b'
        buf[2] = 'r'

# core0
def main():
    _thread.start_new_thread(thread_proc, ())
    while True:
        buf[0] = 'a'
        buf[1] = 'b'
        buf[2] = 'c'
        sleep(.4)
        buf[0] = 'a'
        buf[1] = 'b'
        buf[2] = 'c'
        sleep(.05)
        if not(buf[0] == 'a' and buf[1] == 'b' and buf[2] == 'c'):
            print('cbr00t from heap corrupption')
            break
    
main()
