# %%
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import glob
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import os
import peasyspin as pes
import shutil
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from types import SimpleNamespace
from xeprplus_widgets.long_press_button import LongPressButton
from xeprplus_widgets.radio_treeview import RadioTreeview


class XeprPlusDataAnalysisWindow():
    
    def __init__(self, top_level):
        self.dsets = np.empty(0, dtype=object)
        self.dset_treeview_items = []

        self.win = tk.Toplevel(top_level)
        self.win.title("Data Analysis")
        self.win.geometry("1200x800")
        self.win.minsize(1200, 800)
        
        # Left frame (buttons)
        self.left_frame = ttk.Frame(self.win, width=300, height=800)
        self.left_frame.pack(side=tk.LEFT, expand=False, padx=25, pady=50)

        # Left frame, upper part: advanced options
        self.left_up_frame = ttk.Frame(self.left_frame)
        self.left_up_frame.pack(side=tk.TOP, pady=20)
        self.advanced_options_button = ttk.Button(
            self.left_up_frame, text="Advanced options")
        self.advanced_options_button.grid(
            row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Left frame, middle part: buttons for file, figure
        self.left_mid_frame = ttk.Frame(self.left_frame)
        self.left_mid_frame.pack(side=tk.TOP, pady=20)
        self.clear_figure_button = LongPressButton(
            self.left_mid_frame, text="Clear figure (hold)")
        self.clear_figure_button.grid(
            row=0, column=0, padx=5, pady=5, sticky="ew")
        self.load_dataset_button = tk.Button(self.left_mid_frame,
                                             text="Load dataset")
        self.load_dataset_button.grid(
            row=1, column=0, padx=5, pady=5, sticky="ew")
        self.load_folder_button = tk.Button(self.left_mid_frame,
                                             text="Load folder")
        self.load_folder_button.grid(
            row=2, column=0, padx=5, pady=5, sticky="ew")
        '''
        self.plot_dataset_button = ttk.Button(
            self.left_mid_frame, text="Plot dataset")
        self.plot_dataset_button.grid(
            row=3, column=0, padx=5, pady=5, sticky="ew")
        self.plot_dataset_entry_placeholder = "1,4-8,..."
        self.plot_dataset_entry = PlaceholderEntry(
            self.left_mid_frame,
            placeholder=self.plot_dataset_entry_placeholder)
        self.plot_dataset_entry.grid(
            row=4, column=0, padx=5, pady=0, sticky="ew")
        '''
        # Left frame, bottom part: buttons for data analysis
        self.left_down_frame = ttk.Frame(self.left_frame)
        self.left_down_frame.pack(side=tk.TOP, pady=20)
        self.correct_frequency_button = tk.Button(self.left_down_frame, 
                                                  text="Correct frequency")
        self.correct_frequency_button.grid(
             row=1, column=0, padx=5, pady=5, sticky="ew")
        self.correct_baseline_button = tk.Button(self.left_down_frame,
                                                 text="Correct baseline")
        self.correct_baseline_button.grid(
            row=2, column=0, padx=5, pady=5, sticky="ew")

        # Right frame
        # Load dataset on top, notebook with plot canvases in the middle and
        # navigation toolbar at the bottom.

        # Frame: general frame on the right side
        self.right_frame = ttk.Frame(self.win, width=900, height=800)
        self.right_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Load dataset frame
        self.dataset_frame = ttk.Frame(self.right_frame)
        self.dataset_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.dataset_treeview = RadioTreeview(
            self.dataset_frame,
            columns=("name",),      # 'radio' will be added automatically
            show="tree headings"    # show tree column (#0) + headings
        )
        self.dataset_treeview.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.dataset_scrollbar = ttk.Scrollbar(
            self.dataset_frame, orient="vertical",
            command=self.dataset_treeview.yview)
        self.dataset_scrollbar.pack(side=tk.RIGHT, fill="y")
        self.dataset_treeview.configure(
            yscrollcommand=self.dataset_scrollbar.set)

        # Notebook
        self.nb = ttk.Notebook(self.right_frame)
        self.nb.pack(expand=True, fill=tk.BOTH)
        self.nb_tab1 = ttk.Frame(self.nb)
        self.nb.add(self.nb_tab1, text="Fig 1")

        # Plot canvas
        self.fig = Figure(figsize=(7.5, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()
        self.plot_colors = rcParams['axes.prop_cycle'].by_key()['color']
        self.selected_colors = []
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.nb_tab1)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.nb_tab1, pack_toolbar=False)
        self.toolbar.grid(row=1, column=0)
        self.toolbar.update()
        self.nb_tab1.grid_rowconfigure(0, weight=1)
        self.nb_tab1.grid_rowconfigure(1, weight=0)
        self.nb_tab1.grid_columnconfigure(0, weight=1)
        
        # Configure rows and columns for general right frame
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=0)
        self.right_frame.grid_columnconfigure(1, weight=1)
        
        # Draw
        self.canvas.draw()
        
        
class XeprPlusMainWindow():
    
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("XeprPlus")
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
        self.options_menu.add_command(label="Open XeprAPI")
        self.options_menu.add_command(label="Close XeprAPI")
        self.menubar.add_cascade(label="Options", menu=self.options_menu)

        self.win.config(menu=self.menubar)

        # Text
        self.logs_area = tk.Text(self.win, height=10, width=50)
        self.logs_area.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # Buttons
        self.bottom_frame = ttk.Frame(self.win, height=5, width=200)
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

        self.new_exp_button.config(state="disabled")
        self.run_meas_button.config(state="disabled")
        
        
class XeprPlusNewExpWindow():

    def __init__(self, top_level):
        self.win = tk.Toplevel(top_level)
        self.win.title("New Experiment")
        self.win.geometry("300x100")
        # Non resizable width nor height
        self.win.resizable(False, False)

        # Upper frame (radio buttons)
        self.up_frame = ttk.Frame(self.win, width=300, height=100)
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
        self.down_frame = ttk.Frame(self.win, width=300, height=100)
        self.down_frame.pack(side=tk.TOP, expand=True, anchor='center')

        self.create_button = tk.Button(self.down_frame, text="Create")
        self.create_button.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        self.cancel_button = tk.Button(self.down_frame, text="Cancel")
        self.cancel_button.grid(row=0, column=1, padx=15, pady=10, sticky="ew")
    
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
        self.up_frame = ttk.Frame(self.win, width=300, height=100)
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
        self.run_goal_snr_entry = ttk.Entry(self.up_frame, width=5)
        self.run_goal_snr_entry.grid(row=1, column=1, sticky="ew")
        self.run_time_duration_radiobutton = tk.Radiobutton(
            self.up_frame, text="Repeat for time duration:",
            variable=self.run_type, value=2)
        self.run_time_duration_radiobutton.grid(row=2, column=0, sticky="w")
        self.run_time_duration_h_entry = ttk.Entry(self.up_frame, width=5)
        self.run_time_duration_h_entry.grid(row=2, column=1, sticky="ew")
        self.run_time_duration_h_label = ttk.Label(
            self.up_frame, text="hours")
        self.run_time_duration_h_label.grid(row=2, column=2)
        self.run_time_duration_m_entry = ttk.Entry(self.up_frame, width=5)
        self.run_time_duration_m_entry.grid(row=2, column=3, sticky="ew")
        self.run_time_duration_m_label = ttk.Label(
            self.up_frame, text="minutes")
        self.run_time_duration_m_label.grid(row=2, column=4)
        self.empty_placeholder = ttk.Frame(self.up_frame)  # For easthetics
        self.empty_placeholder.grid(row=0, column=5, rowspan=3, sticky='nsew')
        # Configure columns resize behavior
        self.up_frame.columnconfigure(0, weight=0)
        self.up_frame.columnconfigure(1, weight=1) 
        self.up_frame.columnconfigure(2, weight=10)
        self.up_frame.columnconfigure(3, weight=1) 
        self.up_frame.columnconfigure(4, weight=10)
        self.up_frame.columnconfigure(5, weight=0) 
        # Initialize
        self.run_type.initialize(0)
        self.run_goal_snr_entry.config(state="disabled")
        self.run_time_duration_h_entry.config(state="disabled")
        self.run_time_duration_m_entry.config(state="disabled")

        # Middle frame
        self.mid_frame = ttk.Frame(self.win, width=300, height=100)
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
        self.save_name_label = ttk.Label(
            self.mid_frame, text="Dataset name:")
        self.save_name_label.grid(row=1, column=0, sticky="w")
        self.save_name_entry = ttk.Entry(self.mid_frame)
        self.save_name_entry.grid(row=1, column=1, sticky="ew")
        # Configure columns resize behavior
        self.mid_frame.columnconfigure(0, weight=0)
        self.mid_frame.columnconfigure(1, weight=1) 
        self.mid_frame.columnconfigure(2, weight=0) 

        # Bottom frame (buttons)
        self.down_frame = ttk.Frame(self.win, width=300, height=100)
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
        self._dataanw = XeprPlusDataAnalysisWindow(self._mw.win)

        self.executor = ThreadPoolExecutor(max_workers=1)  # Create once
        self.meas_fut = None  # Initialize as None
        
        # TODO remove this when features are implemented
        self._runmeasw.run_goal_snr_radiobutton.config(state="disabled")
        
        # Do not open as soon as called
        self._newexpw.win.withdraw()
        self._runmeasw.win.withdraw()
        self._dataanw.win.withdraw()
        # Change default behavior of clicking "X" button
        self._mw.win.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._newexpw.win.protocol("WM_DELETE_WINDOW",
                                   self._newexpw.win.withdraw)
        self._runmeasw.win.protocol("WM_DELETE_WINDOW",
                                    self._runmeasw.win.withdraw)        
        self._dataanw.win.protocol("WM_DELETE_WINDOW",
                                   self._dataanw.win.withdraw)

        # Connect widgets to functions
        # Menubar
        self._mw.options_menu.entryconfig(0, command=self.mw_open_xepr_api)
        self._mw.options_menu.entryconfig(1, command=self.mw_close_xepr_api)

        # Buttons
        self._mw.new_exp_button.config(command=self.mw_new_exp_button_clicked)
        self._mw.run_meas_button.config(
            command=self.mw_run_meas_button_clicked)
        self._mw.data_analysis_button.config(
            command=self.mw_data_analysis_button_clicked)
        
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
        self._runmeasw.run_time_duration_radiobutton.config(
            command=self.runmeasw_update_win)

        # TODO connect selft._dataanw.advanced_options_button
        self._dataanw.correct_baseline_button.config(
            command=self.dataanw_correct_baseline)
        self._dataanw.clear_figure_button.config(
            command=self.dataanw_clear_figure_button_clicked)
        self._dataanw.correct_frequency_button.config(
            command=self.dataanw_correct_frequency)
        self._dataanw.dataset_treeview.bind(
            "<Button-1>", self.dataanw_dataset_treeview_clicked)
        self._dataanw.load_dataset_button.config(
            command=self.dataanw_load_dataset_button_clicked)
        self._dataanw.load_folder_button.config(
            command=self.dataanw_load_folder_button_clicked)
        # self._dataanw.plot_dataset_button.config(
        #     command=self.dataanw_plot_dataset)

        # TODO add some if statement
        # Auto connect to XeprAPI at startup
        self.mw_open_xepr_api()
        


    def _on_closing(self):
        self._mw.win.destroy()
        self.mw_close_xepr_api()
        

    def dataanw_clear_figure_button_clicked(self):
        self.dataanw_untoggle_treeview()
        self._dataanw.ax.clear()
        self._dataanw.canvas.draw()
            

    def dataanw_correct_baseline(self):
        return
    
    
    def dataanw_correct_frequency(self):
        iset = self._dataanw.dataset_combobox.current()
        dset = self._dataanw.dsets[iset]
        mwf = 9.6
        x2 = dset.x * mwf / dset.params["mw_freq"] * 1e9
        self._dataanw.ax.plot(x2, dset.o)
        self._dataanw.canvas.draw()
        return
    
    
    def dataanw_dataset_treeview_clicked(self, event):
        '''
        iset = self._dataanw.dataset_combobox.current()
        dset = self._dataanw.dsets[iset]
        # Plot
        self._dataanw.ax.clear()
        self._dataanw.ax.plot(dset.x, dset.o)
        self._dataanw.canvas.draw()
        '''
        old_selected_iids = self._dataanw.dataset_treeview.selected_iids.copy()
        row = self._dataanw.dataset_treeview.on_click(event)
        new_selected_iids = self._dataanw.dataset_treeview.selected_iids.copy()
        if row == -1:
            # The click did not hit a row of the treeview
            return

        # Radiobutton was not clicked but now it is clicked
        add_iids = [i for i in new_selected_iids if i not in old_selected_iids]
        for iid in add_iids:
            # The radiobutton is now clicked, add to the canvas
            idset = self._dataanw.dataset_treeview.index(iid)
            dset = self._dataanw.dsets[idset]
            color = self.dataanw_get_new_plot_color()
            self._dataanw.ax.plot(dset.x,
                                    dset.o,
                                    color=color,
                                    label=dset.params['title'])
        
        # Radiobutton was clicked but now is not clicked anymore
        rmv_iids = [i for i in old_selected_iids if i not in new_selected_iids]
        rmv_idxs = [old_selected_iids.index(i) for i in rmv_iids]
        rmv_lines = [self._dataanw.ax.lines[i] for i in rmv_idxs]
        for line in rmv_lines:
            line.remove()
        self.dataanw_remove_selected_colors(rmv_idxs)
        
        # Update canvas
        self._dataanw.ax.legend()
        self._dataanw.canvas.draw()


    def dataanw_get_new_plot_color(self):
        i = 0
        while True:
            if i not in self._dataanw.selected_colors:
                self._dataanw.selected_colors.append(i)
                return self._dataanw.plot_colors[i]
            i += 1


    def dataanw_load_dataset_button_clicked(self):
        self._mw.win.focus()
        load_files = filedialog.askopenfiles(
            parent=self._dataanw.win, title='Load files')
        # TODO check extension file
        self._dataanw.win.deiconify()
        self._dataanw.win.lift()
        self._dataanw.win.focus()
        
        # TODO Avoid double load of files due to different extensions (DTA DSC)
        for f in load_files:
            self.dataanw_load_single_dataset(f.name)


    def dataanw_load_folder_button_clicked(self):
        self._mw.win.focus()
        load_folder = filedialog.askdirectory(parent=self._dataanw.win, 
                                              title='Load folder')
        self._dataanw.win.deiconify()
        self._dataanw.win.lift()
        self._dataanw.win.focus()
        
        if not load_folder:
            return
        dir_files = sorted(os.listdir(load_folder))
        load_files = [f for f in dir_files if f.endswith('.DSC')]
        if not load_files:
            # No files found
            self.print_log(f"No files with '.DSC' extension in {load_folder}")
        folder_level = self._dataanw.dataset_treeview.add_radio_item(
                "", tk.END, os.path.basename(load_folder))
        self._dataanw.dset_treeview_items.append(folder_level)
        for f in load_files:
            self.dataanw_load_single_dataset(os.path.join(load_folder, f),
                                             folder_level)

        
    def dataanw_load_single_dataset(self, path_to_file, folder=""):
        # Load from memory to Xepr secondary viewport
        self._logic.load_data(path_to_file, 'secondary')
        # Load from Xepr to window
        dset = self._logic.get_dataset(xeprset="secondary")
        # Store in dsets
        params = {"title": dset.getTitle(),
                  "mw_freq": dset.getSPLReal("MWFQ"),
                  "mw_": dset.getSPLReal("MWPW")}
        ds = SimpleNamespace(x=dset.X, o=dset.O, params=params)
        self._dataanw.dsets = np.append(self._dataanw.dsets, ds)
        # Append to treeview
        self._dataanw.dset_treeview_items.append(
            self._dataanw.dataset_treeview.add_radio_item(folder,
                                                          tk.END,
                                                          params['title'])
        )


    def dataanw_untoggle_treeview(self):
        selected_iids = self._dataanw.dataset_treeview.selected_iids.copy()
        for iid in selected_iids:
            self._dataanw.dataset_treeview.toggle_radio(iid)


    def dataanw_remove_selected_colors(self, rmv_iids):
        for i in sorted(rmv_iids, reverse=True):
            self._dataanw.selected_colors.pop(i)

    def mw_close_xepr_api(self):
        if self._logic.xepr:
            self._logic.close_xepr_api()


    def mw_data_analysis_button_clicked(self):
        if not self._dataanw.win.winfo_viewable():
            self._dataanw.win.deiconify()
            self._dataanw.win.lift()
            self._dataanw.win.focus()
        else:
            self._dataanw.win.withdraw()

        
    def mw_new_exp_button_clicked(self):
        if not self._newexpw.win.winfo_viewable():
            self._newexpw.win.deiconify()
            self._newexpw.win.lift()
            self._newexpw.win.focus()
        else:
            self._newexpw.win.withdraw()
            

    def mw_open_xepr_api(self):
        status = self._logic.open_xepr_api()
        if status == 0:
            self.print_log("Connected to XeprAPI.")
        elif status == -1:
            self.print_log("Could not connect to XeprAPI. In Xepr, click " + 
                           "'Processing>XeprAPI>Enable XeprAPI'. " + 
                           "In XeprPlus, click 'Options>Open XeprAPI.'")
        self._update_gui()


    def mw_run_meas_button_clicked(self):
        if not self._runmeasw.win.winfo_viewable():
            self._runmeasw.win.deiconify()
            self._runmeasw.win.lift()
            self._runmeasw.win.focus()
        else:
            self._runmeasw.win.withdraw()


    def newexpw_cancel_button_clicked(self):
        self._newexpw.win.withdraw()
        
        
    def newexpw_create_button_clicked(self):
        self._logic.create_new_experiment(self._newexpw.exp_type.get())
        self._newexpw.win.withdraw()


    def runmeasw_cancel_button_clicked(self):
        self._runmeasw.win.withdraw()
        
        
    def runmeasw_run_button_clicked(self):
        save_folder = self._runmeasw.save_folder_entry.get()
        save_name = self._runmeasw.save_name_entry.get()
        path = os.path.join(save_folder, save_name)
        
        # Handle missing entries
        if save_folder == "" or save_name == "":
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select a folder and a name.")
            self._runmeasw.win.lift()
            self._runmeasw.win.focus()
            return
        
        # Handle folder does not exist
        if not os.path.isdir(save_folder):
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select an existing folder.")
            self._runmeasw.win.lift()
            self._runmeasw.win.focus()
            
        # Handle overwriting
        if os.path.isdir(path):
            # Folder
            self._mw.win.focus()
            res = tk.messagebox.askyesno(
                "Run measurement",
                "A folder already exists at the chosen path:\n\n" + path + 
                "\n\nDelete it and continue?")
            if res:
                shutil.rmtree(path)
            else:
                self._runmeasw.win.lift()
                self._runmeasw.win.focus()
                return
        match_files = glob.glob(path + ".*")
        if match_files:
            fstr = "".join([s[s.find(save_name):] + '\n' for s in match_files])
            self._mw.win.focus()
            res = tk.messagebox.askyesno(
                "Run measurement",
                "One or more files already exist in the folder:\n\n" + fstr + 
                "\nDelete all and continue?")
            if res:
                for f in match_files:
                    os.remove(f)
            else:
                self._runmeasw.win.lift()
                self._runmeasw.win.focus()
                return
        
        self._runmeasw.win.withdraw()
        if self._runmeasw.run_type.get() == 0:
            args = (save_folder, save_name)
            meas_fun = self._logic.run_meas
        elif self._runmeasw.run_type.get() == 1:
            goal_snr = self._runmeasw.run_goal_snr_entry.get()
            if not goal_snr.isdigit():
                self._mw.win.focus()
                tk.messagebox.showerror("Run measurement",
                                        "Time duration entries must be integers.")
                self._runmeasw.win.lift()
                self._runmeasw.win.focus()
            args = (save_folder, save_name, int(goal_snr))
            meas_fun = self._logic.run_meas_goal_snr
        elif self._runmeasw.run_type.get() == 2:
            time_duration_h = self._runmeasw.run_time_duration_h_entry.get()
            time_duration_m = self._runmeasw.run_time_duration_m_entry.get()
            if not time_duration_h.isdigit() or not time_duration_m.isdigit():
                self._mw.win.focus()
                tk.messagebox.showerror("Run measurement",
                                        "Time duration entries must be integers.")
                self._runmeasw.win.lift()
                self._runmeasw.win.focus()
            time_duration_h = int(time_duration_h)
            time_duration_m = int(time_duration_m)
            args = (save_folder, save_name, time_duration_h, time_duration_m)
            meas_fun = self._logic.run_meas_time_duration
        self.meas_fut = self.executor.submit(meas_fun, *args)
        # update_gui as soon as starts and at the end
        self._update_gui()
        self.meas_fut.add_done_callback(self._update_gui)
        '''
        self.meas_thread = threading.Thread(
            target=self._logic.run_meas_time_duration,
            args=(save_folder, save_name, time_duration_h, time_duration_m)
        )
        self.meas_thread.daemon = True  # Dies with main thread
        self.meas_thread.start()
        self.is_running = 1
        
        self._update_gui()
        '''

    def runmeasw_save_folder_browse_button_clicked(self):
        self._mw.win.focus()
        save_folder = filedialog.askdirectory(
            parent=self._runmeasw.win, title="Select folder")
        self._runmeasw.save_folder_entry.delete(0, tk.END)
        self._runmeasw.save_folder_entry.insert(0, save_folder)
        self._runmeasw.win.lift()
        self._runmeasw.win.focus()


    def runmeasw_update_win(self):
        if self._runmeasw.run_type.get() == 0:
            self._runmeasw.run_goal_snr_entry.config(state="disabled")
            self._runmeasw.run_time_duration_h_entry.config(state="disabled")
            self._runmeasw.run_time_duration_m_entry.config(state="disabled")
        elif self._runmeasw.run_type.get() == 1:
            self._runmeasw.run_goal_snr_entry.config(state="active")
            self._runmeasw.run_time_duration_h_entry.config(state="disabled")
            self._runmeasw.run_time_duration_m_entry.config(state="disabled")
        elif self._runmeasw.run_type.get() == 2:
            self._runmeasw.run_goal_snr_entry.config(state="disabled")
            self._runmeasw.run_time_duration_h_entry.config(state="active")
            self._runmeasw.run_time_duration_m_entry.config(state="active")


    def _update_gui(self):
        if self._logic.xepr and self._logic.xepr.XeprActive():
            self._mw.new_exp_button.config(state="active")
            self._mw.run_meas_button.config(state="active")   
        else:
            self._mw.new_exp_button.config(state="disabled") #
            self._mw.run_meas_button.config(state="disabled") #
        if self.meas_fut:
            if self.meas_fut.running():
                exp_name = self._runmeasw.save_name_entry.get()
                self.print_log("Started experiment '" + exp_name + "'.")
                self._mw.new_exp_button.config(state="disabled") #
                self._mw.run_meas_button.config(state="disabled") #  
            elif self.meas_fut.done():
                exp_name = self._runmeasw.save_name_entry.get()
                self.print_log("Finished experiment '" + exp_name + "'.")
                self.meas_fut = None
                self._mw.new_exp_button.config(state="active")
                self._mw.run_meas_button.config(state="active")   
                
        '''
        if self.meas_thread and self.meas_thread.is_alive():
            # Disable buttons while running
            self._mw.new_exp_button.config(state="disabled")
            self._mw.run_meas_button.config(state="disabled")
            self.print_log("Measurement running...")
            
            # Schedule next check in 1000ms
            
        else:
            # Re-enable buttons when done
            self._mw.new_exp_button.config(state="active")
            self._mw.run_meas_button.config(state="active")
            self.print_log("Measurement completed.")
        '''
        
        # self._mw.win.after(1000, self._update_gui)
        
            
    def print_log(self, msg):
        now = datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S >> ')
        self._mw.logs_area.insert(tk.END, now + msg + '\n')
        self._mw.logs_area.see(tk.END)

