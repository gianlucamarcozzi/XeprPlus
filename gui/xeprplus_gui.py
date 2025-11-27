# %%
from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

class XeprPlusMainWindow():
    
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Xepr Plus")
        self.win.geometry("510x260")
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
        self.options_menu.add_command(label="Open Xepr API")
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
        self.transient_radiobutton = tk.Radiobutton(
            self.up_frame, text="Transient", variable=self.exp_type, value=1)
        self.transient_radiobutton.grid(row=0, column=1)
        self.pulse_radiobutton = tk.Radiobutton(
            self.up_frame, text="Pulse", variable=self.exp_type, value=2)
        self.pulse_radiobutton.grid(row=0, column=2)
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


class XeprPlusRunMeasWindow():

    def __init__(self, top_level):
        self.win = tk.Toplevel(top_level)
        self.win.title("Run Measurement")
        self.win.geometry("500x200")
        self.win.minsize(500, 200)
        self.win.resizable(True, False)

        # Upper frame (radio buttons)
        self.up_frame = tk.Frame(self.win, width=300, height=100)
        self.up_frame.pack(
            side=tk.TOP, expand=True, fill=tk.BOTH, padx=10, anchor='center')

        self.run_type = tk.IntVar()
        self.run_simple_meas_radiobutton = tk.Radiobutton(
            self.up_frame, text="Run simple measurement",
            variable=self.run_type, value=0)
        self.run_simple_meas_radiobutton.grid(row=0, column=0, sticky='w')
        self.run_goal_snr_radiobutton = tk.Radiobutton(
            self.up_frame, text="Repeat until goal SNR:",
            variable=self.run_type, value=1)
        self.run_goal_snr_radiobutton.grid(row=1, column=0, sticky="w")
        self.run_goal_snr_entry = ttk.Entry(self.up_frame)
        self.run_goal_snr_entry.grid(row=1, column=1, sticky="ew")
        self.run_for_time_radiobutton = tk.Radiobutton(
            self.up_frame, text="Repeat for (hours):",
            variable=self.run_type, value=2)
        self.run_for_time_radiobutton.grid(row=2, column=0, sticky="w")
        self.run_for_time_entry = ttk.Entry(self.up_frame)
        self.run_for_time_entry.grid(row=2, column=1, sticky="ew")
        self.empty_placeholder = tk.Frame(self.up_frame)  # For easthetics
        self.empty_placeholder.grid(row=0, column=2, rowspan=3, sticky='nsew')
        # Configure columns resize behavior
        self.up_frame.columnconfigure(0, weight=0)
        self.up_frame.columnconfigure(1, weight=1) 
        self.up_frame.columnconfigure(2, weight=0) 
        # Initialize
        self.run_type.initialize(0)
        self.run_goal_snr_entry.config(state="disabled")
        self.run_for_time_entry.config(state="disabled")

        # Middle frame
        self.mid_frame = tk.Frame(self.win, width=300, height=100)
        self.mid_frame.pack(
            side=tk.TOP, expand=True, fill=tk.BOTH, padx=10, anchor='center')

        self.save_folder_label = ttk.Label(
            self.mid_frame, text="Save to folder:")
        self.save_folder_label.grid(row=0, column=0, sticky="w")
        self.save_folder_entry = ttk.Entry(self.mid_frame)
        self.save_folder_entry.grid(row=0, column=1, sticky="ew")
        self.save_folder_browse_button = tk.Button(
            self.mid_frame, text="Browse...")
        self.save_folder_browse_button.grid(row=0, column=2, sticky="w")
        self.save_filename_label = ttk.Label(
            self.mid_frame, text="Filename:")
        self.save_filename_label.grid(row=1, column=0, sticky="w")
        self.save_filename_entry = ttk.Entry(self.mid_frame)
        self.save_filename_entry.grid(row=1, column=1, sticky="ew")
        # Configure columns resize behavior
        self.mid_frame.columnconfigure(0, weight=0)
        self.mid_frame.columnconfigure(1, weight=1) 
        self.mid_frame.columnconfigure(2, weight=0) 

        # Bottom frame (buttons)
        self.down_frame = tk.Frame(self.win, width=300, height=100)
        self.down_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH, anchor="center")

        self.run_button = tk.Button(self.down_frame, text="Run")
        self.run_button.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        self.cancel_button = tk.Button(self.down_frame, text="Cancel")
        self.cancel_button.grid(row=1, column=1, padx=15, pady=10, sticky="ew")
        # Configure columns resize behavior
        self.down_frame.columnconfigure(0, weight=1)
        self.down_frame.columnconfigure(1, weight=1) 

        self.win.rowconfigure(0, weight=1)
        self.win.columnconfigure(0, weight=1)

        # Make empty_placeholder as wide as save_folder_browse_button
        self.win.update_idletasks()  # update layout
        browse_width = self.save_folder_browse_button.winfo_width()
        self.empty_placeholder.config(width=browse_width)


class XeprPlusGui():
    
    def __init__(self, logic):
        self._logic = logic
        
        self._mw = XeprPlusMainWindow()
        self.print_log("Start XeprPlus.")
        self._newexpw = XeprPlusNewExpWindow(self._mw.win)
        self._runmeasw = XeprPlusRunMeasWindow(self._mw.win)

        # TODO remove this when features are implemented
        self._runmeasw.run_goal_snr_radiobutton.config(state="disabled")
        
        # Do not open as soon as called
        self._newexpw.win.withdraw()
        self._runmeasw.win.withdraw()
        # When clicking "X" button, change default behavior
        self._mw.win.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._newexpw.win.protocol("WM_DELETE_WINDOW",
                                   self._newexpw.win.withdraw)
        self._runmeasw.win.protocol("WM_DELETE_WINDOW",
                                    self._runmeasw.win.withdraw)

        # Connect
        # Menubar
        self._mw.options_menu.entryconfig(0, command=self.mw_open_xepr_api)
        self._mw.options_menu.entryconfig(1, command=self.mw_close_xepr_api)
        # Buttons
        self._mw.new_exp_button.config(command=self.mw_new_exp_button_clicked)
        self._mw.run_meas_button.config(command=self.mw_run_meas_button_clicked)
        
        self._newexpw.cancel_button.config(
            command=self.newexpw_cancel_button_clicked)
        self._newexpw.create_button.config(
            command=self.newexpw_create_button_clicked)
        
        self._runmeasw.save_folder_browse_button.config(
            command=self.runmeasw_save_folder_browse_button_clicked)
        self._runmeasw.cancel_button.config(
            command=self.runmeasw_cancel_button_clicked)
        self._runmeasw.run_button.config(
            command=self.runmeasw_run_button_clicked)

        # Radiobuttons
        self._runmeasw.run_simple_meas_radiobutton.config(
            command=self.runmeasw_update_win)
        self._runmeasw.run_goal_snr_radiobutton.config(
            command=self.runmeasw_update_win)
        self._runmeasw.run_for_time_radiobutton.config(
            command=self.runmeasw_update_win)

        # TODO add some if statement
        # Auto connect to XeprAPI at startup
        self.mw_open_xepr_api()


    def _on_closing(self):
        self._mw.win.destroy()
        self.mw_close_xepr_api()
        
        
    def mw_close_xepr_api(self):
        self._logic.close_xepr_api()


    def mw_new_exp_button_clicked(self):
        self._newexpw.win.deiconify()
        self._newexpw.win.lift()
        self._newexpw.win.focus()
    

    def mw_open_xepr_api(self):
        status = self._logic.open_xepr_api()
        if status == 0:
            self.print_log("Connected to XeprAPI.")


    def mw_run_meas_button_clicked(self):
        self._runmeasw.win.deiconify()
        self._runmeasw.win.lift()
        self._runmeasw.win.focus()


    def newexpw_cancel_button_clicked(self):
        self._newexpw.win.withdraw()
        
        
    def newexpw_create_button_clicked(self):
        self._logic.create_new_experiment(self._newexpw.exp_type.get())
        self._newexpw.win.withdraw()


    def runmeasw_cancel_button_clicked(self):
        self._runmeasw.win.withdraw()
        
        
    def runmeasw_run_button_clicked(self):
        folder = self._runmeasw.save_folder_entry.get()
        filename = self._runmeasw.save_filename_entry.get()
        path = os.path.join(folder, filename)
        if folder == "" or filename == "":
            # Error: missing entries
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select a folder and a filename.")
            self._runmeasw.win.lift()
            self._runmeasw.win.focus()
            return
        if os.path.isdir(path) or os.path.isfile(path):
            self._runmeasw.win.focus_force()
            res = tk.messagebox.askyesno(
                "Run measurement",
                f"A file or folder already exists at the chosen path" + 
                f"\n{path}.\nOverwrite?")
            if not res:
                self._runmeasw.win.lift()
                self._runmeasw.win.focus_force()
                return
        if self._runmeasw.run_type.get() == 0:
            self._logic.run_measurement(folder, filename)
        elif self._runmeasw.run_type.get() == 1:
            goal_snr = self._runmeasw.run_goal_snr_entry.get()
            # TODO add error handling for SNR here
            self._logic.run_measurement_goal_snr(folder, filename, goal_snr)
        elif self._runmeasw.run_type.get() == 2:
            for_time = self._runmeasw.run_for_time_entry.get()
            # TODO add error handling for time here
            # (and confirmation dialog as well????)
            self._logic.run_measurement_for_time(folder, filename, for_time)
        self._runmeasw.win.withdraw()


    def runmeasw_save_folder_browse_button_clicked(self):
        self._mw.win.focus()
        save_folder = filedialog.askdirectory()
        self._runmeasw.save_folder_entry.delete(0, tk.END)
        self._runmeasw.save_folder_entry.insert(0, save_folder)
        self._runmeasw.win.lift()
        self._runmeasw.win.focus()


    def runmeasw_update_win(self):
        if self._runmeasw.run_type.get() == 0:
            self._runmeasw.run_goal_snr_entry.config(state="disabled")
            self._runmeasw.run_for_time_entry.config(state="disabled")
        elif self._runmeasw.run_type.get() == 1:
            self._runmeasw.run_goal_snr_entry.config(state="active")
            self._runmeasw.run_for_time_entry.config(state="disabled")
        elif self._runmeasw.run_type.get() == 2:
            self._runmeasw.run_goal_snr_entry.config(state="disabled")
            self._runmeasw.run_for_time_entry.config(state="active")


    def print_log(self, msg):
        now = datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S >> ')
        self._mw.logs_area.insert(tk.END, now + msg + '\n')

