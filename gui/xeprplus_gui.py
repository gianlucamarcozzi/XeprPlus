# %%
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import sys

class XeprPlusMainWindow():
    
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Xepr Plus")
        self.win.geometry("500x260")
        self.win.minsize(510, 260)

        # Menubar
        self.menubar = tk.Menu(self.win)

        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Open")
        file_menu.add_command(label="Save")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.win.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # Options menu
        self.options_menu = tk.Menu(self.menubar, tearoff=0)
        self.options_menu.add_command(label="Connect to Xepr API")
        self.options_menu.add_command(label="Close Xepr API")
        self.menubar.add_cascade(label="Options", menu=self.options_menu)

        self.win.config(menu=self.menubar)

        # Text
        self.logs_area = tk.Text(self.win, height=10, width=50)
        self.logs_area.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Buttons
        self.bottom_frame = tk.Frame(self.win, height=5, width=200)
        self.bottom_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
        self.new_exp_button = tk.Button(self.bottom_frame, text="New exp")
        self.new_exp_button.grid(row=0, column=0)
        self.run_meas_button = tk.Button(self.bottom_frame, text="Run meas")
        self.run_meas_button.grid(row=0, column=1)
        self.data_analysis_button = tk.Button(self.bottom_frame,
                                              text="Data analysis")
        self.data_analysis_button.grid(row=0, column=2)
        self.rm_tm_button = tk.Button(self.bottom_frame, text="RM TM")
        self.rm_tm_button.grid(row=0, column=3)
        self.resonator_dip_button = tk.Button(self.bottom_frame,
                                              text="Resonator dip")
        self.resonator_dip_button.grid(row=0, column=4)
        self.pulsespel_button = tk.Button(self.bottom_frame, text="PulseSPEL")
        self.pulsespel_button.grid(row=0, column=5)

        self.win.rowconfigure(0, weight=0)
        self.win.rowconfigure(1, weight=1)
        self.win.rowconfigure(2, weight=0)
        self.win.columnconfigure(0, weight=1)

class XeprPlusNewExpWindow():

    def __init__(self, top_level):
        self.win = tk.Toplevel(top_level)
        self.win.title("New Experiment")
        self.win.geometry("300x100")
        # Non resizable width nor height
        self.win.resizable(False, False)

        # Upper frame (radio buttons)
        self.up_frame = tk.Frame(self.win, width=300, height=100)
        self.up_frame.pack(side=tk.TOP, expand=True, anchor='center')

        self.exp_type = tk.IntVar()
        self.cw_radiobutton = tk.Radiobutton(
            self.up_frame, text="C.W.", variable=self.exp_type, value=0)
        self.cw_radiobutton.grid(row=0, column=0)
        self.cw_radiobutton = tk.Radiobutton(
            self.up_frame, text="Transient", variable=self.exp_type, value=1)
        self.cw_radiobutton.grid(row=0, column=1)
        self.cw_radiobutton = tk.Radiobutton(
            self.up_frame, text="Pulse", variable=self.exp_type, value=2)
        self.cw_radiobutton.grid(row=0, column=2)
        self.exp_type.initialize(0)
        
        # Bottom frame (buttons)
        self.down_frame = tk.Frame(self.win, width=300, height=100)
        self.down_frame.pack(side=tk.TOP, expand=True, anchor='center')

        self.create_button = tk.Button(self.down_frame, text="Create")
        self.create_button.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        self.cancel_button = tk.Button(self.down_frame, text="Cancel")
        self.cancel_button.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
    
        self.win.rowconfigure(0, weight=1)
        self.win.columnconfigure(0, weight=1)


class XeprPlusGui():
    
    def __init__(self, logic):
        self._logic = logic
        
        self._mw = XeprPlusMainWindow()
        self.print_log("Start XeprPlus.")
        self._newexpw = XeprPlusNewExpWindow(self._mw.win)

        # Do not open as soon as called
        self._newexpw.win.withdraw()
        # When clicking "X" button, change default behavior
        self._mw.win.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._newexpw.win.protocol("WM_DELETE_WINDOW",
                                   self._newexpw.win.withdraw)
        
        self._mw.options_menu.entryconfig(0,
                                          command=self.mw_connect_to_xepr_api)
        self._mw.new_exp_button.config(
            command=self.mw_new_exp_button_clicked)
        
        
        self._newexpw.cancel_button.config(
            command=self.newexpw_cancel_button_clicked)
        self._newexpw.create_button.config(
            command=self.newexpw_create_button_clicked)

        # TODO add some if statement
        # Auto connect to XeprAPI at startup
        #self.mw_connect_to_xepr_api()


    def _on_closing(self):
        self._mw.win.destroy()
        self._logic._on_closing()
        
        
    def mw_connect_to_xepr_api(self):
        status = self._logic.connect_to_xepr_api()
        if status == 0:
            self.print_log("Connected to XeprAPI.")
        
        
    def mw_new_exp_button_clicked(self):
        self._newexpw.win.deiconify()
        self._newexpw.win.lift()
        self._newexpw.win.focus_force()
    
    
    def newexpw_cancel_button_clicked(self):
        self._newexpw.win.withdraw()
        
        
    def newexpw_create_button_clicked(self):
        self._logic.create_new_experiment(self._newexpw.exp_type.get())
        self._newexpw.win.withdraw()


    def print_log(self, msg):
        now = datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S >> ')
        self._mw.logs_area.insert(tk.END, now + msg + '\n')

