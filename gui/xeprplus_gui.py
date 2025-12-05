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
        self.fig_notebook_tabs = []
        self.cur_tab = None
        self.selected_colors = []

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
        self.new_figure_button = ttk.Button(
            self.left_mid_frame, text="New figure")
        self.new_figure_button.grid(
            row=1, column=0, padx=5, pady=5, sticky="ew")
        self.close_figure_button = ttk.Button(
            self.left_mid_frame, text="Close figure")
        self.close_figure_button.grid(
            row=2, column=0, padx=5, pady=5, sticky="ew")
        self.close_all_figures_button = ttk.Button(
            self.left_mid_frame, text="Close all figures")
        self.close_all_figures_button.grid(
            row=3, column=0, padx=5, pady=5, sticky="ew")
        self.load_dataset_button = ttk.Button(self.left_mid_frame,
                                             text="Load dataset")
        self.load_dataset_button.grid(
            row=4, column=0, padx=5, pady=5, sticky="ew")
        self.load_folder_button = ttk.Button(self.left_mid_frame,
                                             text="Load folder")
        self.load_folder_button.grid(
            row=5, column=0, padx=5, pady=5, sticky="ew")
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
        self.fig_notebook = ttk.Notebook(self.right_frame)
        self.fig_notebook.pack(expand=True, fill=tk.BOTH)
        self.plot_colors = rcParams['axes.prop_cycle'].by_key()['color']
        
        
        # Configure rows and columns for general right frame
        self.right_frame.grid_rowconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=0)
        self.right_frame.grid_columnconfigure(1, weight=1)
        
        
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
        self._print_log("Start XeprPlus.")
        # New experiment window (nexw)
        self._nexw = XeprPlusNewExpWindow(self._mw.win)
        # Run measurement window (rmw)
        self._rmw = XeprPlusRunMeasWindow(self._mw.win)
        # Data analysis window (daw)
        self._daw = XeprPlusDataAnalysisWindow(self._mw.win)

        self.executor = ThreadPoolExecutor(max_workers=1)  # Create once
        self.meas_fut = None  # Initialize as None
        
        # Do not open as soon as called
        self._nexw.win.withdraw()
        self._rmw.win.withdraw()
        self._daw.win.withdraw()
        # Change default behavior of clicking "X" button
        self._mw.win.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._nexw.win.protocol("WM_DELETE_WINDOW",
                                   self._nexw.win.withdraw)
        self._rmw.win.protocol("WM_DELETE_WINDOW",
                                    self._rmw.win.withdraw)        
        self._daw.win.protocol("WM_DELETE_WINDOW",
                                   self._daw.win.withdraw)

        # Create first canvas for data analysis window
        self.daw_new_figure_button_clicked()

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
        
        self._nexw.cancel_button.config(
            command=self.nexw_cancel_button_clicked)
        self._nexw.create_button.config(
            command=self.nexw_create_button_clicked)
        
        self._rmw.save_folder_browse_button.config(
            command=self.rmw_save_folder_browse_button_clicked)
        self._rmw.cancel_button.config(
            command=self.rmw_cancel_button_clicked)
        self._rmw.run_button.config(
            command=self.rmw_run_button_clicked)
        
        # Radiobuttons
        self._rmw.run_simple_meas_radiobutton.config(
            command=self.rmw_update_win)
        self._rmw.run_goal_snr_radiobutton.config(
            command=self.rmw_update_win)
        self._rmw.run_time_duration_radiobutton.config(
            command=self.rmw_update_win)

        # TODO connect self._daw.advanced_options_button
        self._daw.clear_figure_button.config(
            command=self.daw_clear_figure_button_clicked)
        self._daw.close_figure_button.config(
            command=self.daw_close_figure_button_clicked)
        self._daw.close_all_figures_button.config(
            command=self.daw_close_all_figures_button_clicked)
        self._daw.correct_baseline_button.config(
            command=self.daw_correct_baseline_button_clicked)
        self._daw.correct_frequency_button.config(
            command=self.daw_correct_frequency)
        self._daw.load_dataset_button.config(
            command=self.daw_load_dataset_button_clicked)
        self._daw.load_folder_button.config(
            command=self.daw_load_folder_button_clicked)
        self._daw.new_figure_button.config(
            command=self.daw_new_figure_button_clicked)
        self._daw.dataset_treeview.bind("<Button-1>",
                                        self.daw_dataset_treeview_clicked)
        self._daw.fig_notebook.bind("<<NotebookTabChanged>>",
                                    self.daw_fig_notebook_tab_changed)

        # TODO add some if statement
        # Auto connect to XeprAPI at startup
        self.mw_open_xepr_api()
        

    def _daw_update_current_fig_notebook_tab(self):
        itab = self._daw.fig_notebook.index("current")
        self._daw.cur_tab = self._daw.fig_notebook_tabs[itab]


    def _on_closing(self):
        self._mw.win.destroy()
        self.mw_close_xepr_api()
        

    def _print_log(self, msg):
        now = datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S >> ')
        self._mw.logs_area.insert(tk.END, now + msg + '\n')
        self._mw.logs_area.see(tk.END)
    
    
    def _update_gui(self):
        if self._logic.xepr and self._logic.xepr.XeprActive():
            self._mw.new_exp_button.config(state="active")
            self._mw.run_meas_button.config(state="active")   
        else:
            self._mw.new_exp_button.config(state="disabled") #
            self._mw.run_meas_button.config(state="disabled") #
        if self.meas_fut:
            if self.meas_fut.running():
                exp_name = self._rmw.save_name_entry.get()
                self._print_log("Started experiment '" + exp_name + "'.")
                self._mw.new_exp_button.config(state="disabled") #
                self._mw.run_meas_button.config(state="disabled") #  
            elif self.meas_fut.done():
                exp_name = self._rmw.save_name_entry.get()
                self._print_log("Finished experiment '" + exp_name + "'.")
                self.meas_fut = None
                self._mw.new_exp_button.config(state="active")
                self._mw.run_meas_button.config(state="active")   
                
        '''
        if self.meas_thread and self.meas_thread.is_alive():
            # Disable buttons while running
            self._mw.nexw_exp_button.config(state="disabled")
            self._mw.run_meas_button.config(state="disabled")
            self._print_log("Measurement running...")
            
            # Schedule next check in 1000ms
            
        else:
            # Re-enable buttons when done
            self._mw.nexw_exp_button.config(state="active")
            self._mw.run_meas_button.config(state="active")
            self._print_log("Measurement completed.")
        
        
        # self._mw.win.after(1000, self._update_gui)
        '''
    
    
    def daw_fig_notebook_tab_changed(self, event):
        # Update current tab
        self._daw_update_current_fig_notebook_tab()


    def daw_clear_figure_button_clicked(self):
        self.daw_untoggle_treeview()
        self._daw.cur_tab.ax.clear()
        self._daw.cur_tab.canvas.draw()
            

    def daw_close_figure_button_clicked(self):
        itab = self._daw.fig_notebook.index("current")
        self._daw.fig_notebook.forget(itab)

        # Clear variables
        self._daw.fig_notebook_tabs.pop(itab)
        
        # If empty, create one tab
        if not self._daw.fig_notebook.tabs():
            self.daw_new_figure_button_clicked()

        # Update current tab
        self._daw_update_current_fig_notebook_tab()


    def daw_close_all_figures_button_clicked(self):
        for tab in self._daw.fig_notebook.tabs():
            itab = self._daw.fig_notebook.index(tab)
            self._daw.fig_notebook.forget(itab)

        # Clear all previously saved variables
        self._daw.fig_notebook_tabs = []
        
        # Create one tab
        self.daw_new_figure_button_clicked()

        # Update current tab
        self._daw_update_current_fig_notebook_tab()


    def daw_correct_baseline_button_clicked(self):
        iid = self._daw.dataset_treeview.focus()
        idset = self._daw.dataset_treeview.index(iid)
        dset = self._daw.dsets[idset]

        if dset.o.ndim == 1:
            left = np.min(dset.x) + (np.max(dset.x) - np.min(dset.x)) * 0.15
            right = np.max(dset.x) - (np.max(dset.x) - np.min(dset.x)) * 0.15
            region = (dset.x < left) | (dset.x > right)
            dset.ycorr, dset.bl = self._logic.correct_baseline(
                dset.o, dim=0, n=1, region=region)
            
            color = self.daw_get_new_plot_color()
            self._daw.cur_tab.ax.plot(dset.x,
                                      dset.ycorr,
                                      color=color,                            label=dset.params['title'] + " corr")
            color = self.daw_get_new_plot_color()
            self._daw.cur_tab.ax.plot(dset.x,
                                      dset.bl,
                                      color=color,                            label=dset.params['title'] + "bl")

            # Update canvas
            self._daw.cur_tab.ax.legend()
            self._daw.cur_tab.canvas.draw()
        
        return
    
    
    def daw_correct_frequency(self):
        '''
        iset = self._daw.dataset_combobox.current()
        dset = self._daw.dsets[iset]
        mwf = 9.6
        x2 = dset.x * mwf / dset.params["mw_freq"] * 1e9
        self._daw.ax.plot(x2, dset.o)
        self._daw.canvas.draw()
        '''
        return
    
    
    def daw_dataset_treeview_clicked(self, event):
        old_selected_iids = self._daw.dataset_treeview.selected_iids.copy()
        row = self._daw.dataset_treeview.on_click(event)
        new_selected_iids = self._daw.dataset_treeview.selected_iids.copy()
        if row == -1:
            # The click did not hit a row of the treeview
            return

        # Radiobutton was not clicked but now it is clicked
        add_iids = [i for i in new_selected_iids if i not in old_selected_iids]
        for iid in add_iids:
            # The radiobutton is now clicked, add to the canvas
            idset = self._daw.dataset_treeview.index(iid)
            dset = self._daw.dsets[idset]
            color = self.daw_get_new_plot_color()
            self._daw.cur_tab.ax.plot(dset.x,
                                      dset.o,
                                      color=color,                            label=dset.params['title'])
        
        # Radiobutton was clicked but now is not clicked anymore
        rmv_iids = [i for i in old_selected_iids if i not in new_selected_iids]
        rmv_idxs = [old_selected_iids.index(i) for i in rmv_iids]
        rmv_lines = [self._daw.cur_tab.ax.lines[i] for i in rmv_idxs]
        for line in rmv_lines:
            line.remove()
        self.daw_remove_selected_colors(rmv_idxs)
        
        # Update canvas
        self._daw.cur_tab.ax.legend()
        self._daw.cur_tab.canvas.draw()


    def daw_get_new_plot_color(self):
        i = 0
        while True:
            if i not in self._daw.selected_colors:
                self._daw.selected_colors.append(i)
                return self._daw.plot_colors[i]
            i += 1


    def daw_load_dataset_button_clicked(self):
        self._mw.win.focus()
        load_files = filedialog.askopenfiles(
            parent=self._daw.win, title='Load files',
            filetypes =[('Description files', '*.DSC')])
        # TODO check extension file
        self._daw.win.deiconify()
        self._daw.win.lift()
        self._daw.win.focus()
        
        for f in load_files:
            if f.endswith('.DSC') or f.endswith('.DTA') or f.endswith('.YGA'):
                self.daw_load_single_dataset(f.name)
                self._print_log("Load dataset ")
            else:
                self._print_log(f"Could not load {f}.\nFile extension " + 
                                "must be '.DTA', '.DSC' or '.YGA'")

    def daw_load_folder_button_clicked(self):
        self._mw.win.focus()
        load_folder = filedialog.askdirectory(parent=self._daw.win, 
                                              title='Load folder')
        self._daw.win.deiconify()
        self._daw.win.lift()
        self._daw.win.focus()
        
        if not load_folder:
            return
        dir_files = sorted(os.listdir(load_folder))
        load_files = [f for f in dir_files if f.endswith('.DSC')]
        if not load_files:
            # No files found
            self._print_log(f"No files with '.DSC' extension in {load_folder}")
        folder_level = self._daw.dataset_treeview.add_radio_item(
                "", tk.END, os.path.basename(load_folder))
        self._daw.dset_treeview_items.append(folder_level)
        for f in load_files:
            self.daw_load_single_dataset(os.path.join(load_folder, f),
                                             folder_level)

        
    def daw_load_single_dataset(self, path_to_file, folder=""):
        # Load from memory to Xepr secondary viewport
        self._logic.load_data(path_to_file, 'secondary')
        # Load from Xepr to window
        dset = self._logic.get_dataset(xeprset="secondary")
        # Store in dsets
        params = {"title": dset.getTitle(),
                  "mw_freq": dset.getSPLReal("MWFQ"),
                  "mw_": dset.getSPLReal("MWPW")}
        ds = SimpleNamespace(x=dset.X, o=dset.O, params=params)
        self._daw.dsets = np.append(self._daw.dsets, ds)
        # Append to treeview
        self._daw.dset_treeview_items.append(
            self._daw.dataset_treeview.add_radio_item(folder,
                                                          tk.END,
                                                          params['title'])
        )


    def daw_new_figure_button_clicked(self):
        # Create frame inside the notebook
        frame = ttk.Frame(self._daw.fig_notebook)
        tab_title = self.daw_new_figure_tab_title()

        # Plot canvas
        fig = Figure(figsize=(7.5, 6), dpi=100)
        ax = fig.add_subplot(111)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.grid(row=0, column=0, sticky="nsew")

        # Navigation toolbar
        toolbar = NavigationToolbar2Tk(canvas, frame, pack_toolbar=False)
        toolbar.grid(row=1, column=0)
        toolbar.update()

        # Arangement
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=0)
        frame.grid_columnconfigure(0, weight=1)

        # Add to notebook
        self._daw.fig_notebook.add(frame, text=tab_title)

        # Draw
        canvas.draw()

        # Store
        self._daw.fig_notebook_tabs.append(
            SimpleNamespace(
                frame=frame, tab_title=tab_title, fig=fig, ax=ax,
                canvas=canvas, canvas_widget=canvas_widget, toolbar=toolbar
                )
        )
        
        # Update current tab
        self._daw_update_current_fig_notebook_tab()

        return


    def daw_new_figure_tab_title(self):
        if not self._daw.fig_notebook_tabs:
            return "Fig 0"
        
        last_title = self._daw.fig_notebook_tabs[-1].tab_title
        return (last_title.split(" ")[0] + " " + 
                str(int(last_title.split(" ")[1]) + 1))


    def daw_untoggle_treeview(self):
        selected_iids = self._daw.dataset_treeview.selected_iids.copy()
        for iid in selected_iids:
            self._daw.dataset_treeview.toggle_radio(iid)


    def daw_remove_selected_colors(self, rmv_iids):
        for i in sorted(rmv_iids, reverse=True):
            self._daw.selected_colors.pop(i)


    def mw_close_xepr_api(self):
        if self._logic.xepr:
            self._logic.close_xepr_api()


    def mw_data_analysis_button_clicked(self):
        if not self._daw.win.winfo_viewable():
            self._daw.win.deiconify()
            self._daw.win.lift()
            self._daw.win.focus()
        else:
            self._daw.win.withdraw()

        
    def mw_new_exp_button_clicked(self):
        if not self._nexw.win.winfo_viewable():
            self._nexw.win.deiconify()
            self._nexw.win.lift()
            self._nexw.win.focus()
        else:
            self._nexw.win.withdraw()
            

    def mw_open_xepr_api(self):
        status = self._logic.open_xepr_api()
        if status == 0:
            self._print_log("Connected to XeprAPI.")
        elif status == -1:
            self._print_log("Could not connect to XeprAPI. In Xepr, click " + 
                            "'Processing>XeprAPI>Enable XeprAPI'. " + 
                            "In XeprPlus, click 'Options>Open XeprAPI.'")
        self._update_gui()


    def mw_run_meas_button_clicked(self):
        if not self._rmw.win.winfo_viewable():
            self._rmw.win.deiconify()
            self._rmw.win.lift()
            self._rmw.win.focus()
        else:
            self._rmw.win.withdraw()


    def nexw_cancel_button_clicked(self):
        self._nexw.win.withdraw()
        
        
    def nexw_create_button_clicked(self):
        self._logic.create_new_experiment(self._nexw.exp_type.get())
        self._nexw.win.withdraw()


    def rmw_cancel_button_clicked(self):
        self._rmw.win.withdraw()
        
        
    def rmw_run_button_clicked(self):
        save_folder = self._rmw.save_folder_entry.get()
        save_name = self._rmw.save_name_entry.get()
        path = os.path.join(save_folder, save_name)
        
        # Handle missing entries
        if save_folder == "" or save_name == "":
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select a folder and a name.")
            self._rmw.win.lift()
            self._rmw.win.focus()
            return
        
        # Handle folder does not exist
        if not os.path.isdir(save_folder):
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select an existing folder.")
            self._rmw.win.lift()
            self._rmw.win.focus()
            
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
                self._rmw.win.lift()
                self._rmw.win.focus()
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
                self._rmw.win.lift()
                self._rmw.win.focus()
                return
        
        self._rmw.win.withdraw()
        if self._rmw.run_type.get() == 0:
            args = (save_folder, save_name)
            meas_fun = self._logic.run_meas
        elif self._rmw.run_type.get() == 1:
            goal_snr = self._rmw.run_goal_snr_entry.get()
            if not goal_snr.isdigit():
                self._mw.win.focus()
                tk.messagebox.showerror("Run measurement",
                                        "Time duration entries must be integers.")
                self._rmw.win.lift()
                self._rmw.win.focus()
            args = (save_folder, save_name, int(goal_snr))
            meas_fun = self._logic.run_meas_goal_snr
        elif self._rmw.run_type.get() == 2:
            time_duration_h = self._rmw.run_time_duration_h_entry.get()
            time_duration_m = self._rmw.run_time_duration_m_entry.get()
            if not time_duration_h.isdigit() or not time_duration_m.isdigit():
                self._mw.win.focus()
                tk.messagebox.showerror("Run measurement",
                                        "Time duration entries must be integers.")
                self._rmw.win.lift()
                self._rmw.win.focus()
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


    def rmw_save_folder_browse_button_clicked(self):
        self._mw.win.focus()
        save_folder = filedialog.askdirectory(
            parent=self._rmw.win, title="Select folder")
        self._rmw.save_folder_entry.delete(0, tk.END)
        self._rmw.save_folder_entry.insert(0, save_folder)
        self._rmw.win.lift()
        self._rmw.win.focus()


    def rmw_update_win(self):
        if self._rmw.run_type.get() == 0:
            self._rmw.run_goal_snr_entry.config(state="disabled")
            self._rmw.run_time_duration_h_entry.config(state="disabled")
            self._rmw.run_time_duration_m_entry.config(state="disabled")
        elif self._rmw.run_type.get() == 1:
            self._rmw.run_goal_snr_entry.config(state="active")
            self._rmw.run_time_duration_h_entry.config(state="disabled")
            self._rmw.run_time_duration_m_entry.config(state="disabled")
        elif self._rmw.run_type.get() == 2:
            self._rmw.run_goal_snr_entry.config(state="disabled")
            self._rmw.run_time_duration_h_entry.config(state="active")
            self._rmw.run_time_duration_m_entry.config(state="active")




