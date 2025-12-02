import tkinter as tk

class LongPressButton(tk.Button):
    def __init__(self, parent, long_press_time=1000, **kwargs):
        super().__init__(parent, **kwargs)
        self.long_press_time = long_press_time  # ms
        self.long_press_id = None
        self.is_held = False
        
        # Bind events
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    

    def cancel_long_press(self):
        self.is_held = False
        if self.long_press_id:
            self.after_cancel(self.long_press_id)
            self.long_press_id = None
    

    def config(self, cnf=None, **kw):
        if cnf and "command" in cnf:
            self._command = cnf["command"]
            cnf = dict(cnf)  # make a copy
            del cnf["command"]
        if "command" in kw:
            self._command = kw.pop("command")
        super().config(cnf, **kw)

    
    configure = config


    def on_leave(self, event):
        self.cancel_long_press()


    def on_enter(self, event):
        if self.is_held and self.long_press_id:
            # Restart timer if still holding on enter
            self.cancel_long_press()
            self.long_press_id = self.after(self.long_press_time, self.do_long_press)
    
    def on_press(self, event):
        if not self.is_held:
            self.is_held = True
            self.long_press_id = self.after(self.long_press_time, self.do_long_press)
    

    def on_release(self, event):
        self.cancel_long_press()
    
    
    def do_long_press(self):
        if self._command:
            self._command()
        self.long_press_id = None

