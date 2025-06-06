from config import mod, initMenus
from common import *
from part_input import InputPart
# mod.device = 'rasppico'

part = InputPart(_title = 'Input Test')
part.run()
shared.dev.lcd.on()
part.onKeyReleased('c')
part.onKeyReleased('i')
part.onKeyReleased('k')
print('input val:', part.val())
part.onKeyReleased('enter')

# menus = initMenus();
# part = menus.main.run()
# part.onKeyReleased('down')
# part.onKeyReleased('enter')
# part.onKeyReleased('esc')
# part.onKeyReleased('esc')
