from gui.xeprplus_gui import XeprPlusGui
from logic.xeprplus_logic import XeprPlusLogic

logic = XeprPlusLogic()
gui = XeprPlusGui(logic=logic)
gui._mw.win.mainloop()
