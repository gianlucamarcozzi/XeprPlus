# %%

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import glob
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os
# import peasyspin as pes
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
from xeprplus_widgets.vertical_navigation_toolbar_2_tk import VerticalNavigationToolbar2Tk
    
        
class XeprPlusMainWindow():
    
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("XeprPlus")
        self.win.wm_attributes("-zoomed", True)

        # Menubar
        # Menubar with file menu and options menu
        self.menubar = tk.Menu(self.win)
        self.win.config(menu=self.menubar)

        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        # self.file_menu.add_command(label="Open")
        # self.file_menu.add_command(label="Save")
        self.file_menu.add_command(label="Load dataset")
        self.file_menu.add_command(label="Load folder")

        # Options menu
        self.options_menu = tk.Menu(self.menubar, tearoff=0)
        self.options_menu.add_command(label="Open XeprAPI")
        self.options_menu.add_command(label="Close XeprAPI")

        # Measurement menu
        self.meas_menu = tk.Menu(self.menubar, tearoff=0)
        self.create_exp_menu = tk.Menu(self.meas_menu, tearoff=0)
        self.create_exp_menu.add_command(label="C.W.")
        self.create_exp_menu.add_command(label="Transient")
        self.create_exp_menu.add_command(label="Pulse")
        self.meas_menu.add_command(label="Activate VTU")

        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Options", menu=self.options_menu)
        self.menubar.add_cascade(label="Options", menu=self.meas_menu)
        self.meas_menu.add_cascade(label="Create experiment", 
                                   menu=self.create_exp_menu)

        # Measurement frame
        # In this frame will be placed everything concerning measurement
        # (selecting experiments, parameters, plot of the current measurement).
        # The hierarchy inside meas_frame is as follows:
        # - run_save_frame
        #   - run_frame
        #   - save_frame
        # - meas_params_frame
        self.meas_frame = ttk.Frame(self.win)
        self.meas_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Run save frame
        # This covers the upper part of the window. In this frame there are:
        # - run_frame: on the left, with buttons relative to running and
        #     stopping measurements
        # - save_frame: on the right, with entries for the folder and the
        #     filename to save the measurements
        self.run_save_frame = ttk.Frame(self.meas_frame)
        self.run_save_frame.pack(side=tk.TOP, expand=False, fill=tk.BOTH)

        # Run frame (on the left)
        self.run_frame = ttk.Frame(self.run_save_frame)
        self.run_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.exp_select_combobox = ttk.Combobox(
            self.run_frame,
            textvariable="",
            values=["CW", "Transient", "Pulse"]
        )
        self.exp_select_combobox.grid(row=0, column=0, sticky="ew")
        self.send_to_spectrometer_button = tk.Button(
            self.run_frame,
            text="Send to spectrometer"
        )
        self.send_to_spectrometer_button.grid(row=0, column=1, sticky="ew")     
        self.run_button = tk.Button(
            self.run_frame,
            text="Run"
        )
        self.run_button.grid(row=1, column=0, sticky="ew")
        self.stop_end_button = tk.Button(
            self.run_frame,
            text="Stop (end)"
        )
        self.stop_end_button.grid(row=1, column=1, sticky="ew")
        self.stop_now_button = tk.Button(
            self.run_frame,
            text="Stop (now)"
        )
        self.stop_now_button.grid(row=1, column=2, sticky="ew")
        
        # Save frame (on the right)
        self.save_frame = ttk.Frame(self.run_save_frame)
        self.save_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        self.save_folder_label = ttk.Label(
            self.save_frame,
            text="Save to folder:"
        )
        self.save_folder_label.grid(row=0, column=0, sticky="w")
        self.save_folder_entry = ttk.Entry(self.save_frame)
        self.save_folder_entry.grid(row=0, column=1, sticky="ew")
        self.save_folder_browse_button = tk.Button(
            self.save_frame,
            text="Browse..."
        )
        self.save_folder_browse_button.grid(row=0, column=2, sticky="w")
        self.save_name_label = ttk.Label(
            self.save_frame,
            text="Dataset name:"
        )
        self.save_name_label.grid(row=1, column=0, sticky="w")
        self.save_name_entry = ttk.Entry(self.save_frame)
        self.save_name_entry.grid(row=1, column=1, sticky="ew")
        # Configure columns resize behavior
        self.save_frame.columnconfigure(0, weight=0)
        self.save_frame.columnconfigure(1, weight=1) 
        
        # Frame for measurement parameters
        # Here there are entries for the experimental parameters. The entries
        # change dynamically depending on the experiment that was last sent to
        # the spectrometer.
        self.meas_params_frame = tk.Frame(self.meas_frame)
        self.meas_params_frame.pack(side=tk.TOP, expand=False, fill=tk.X)

        # Two empty spaced for aesthetics. The actual parameter entries are
        # updated when a new experiment is sent to the spectrometer.
        empty_label = tk.Label(self.meas_params_frame, name="empty_label")
        empty_label.grid(row=0, column=0)
        empty_label_2 = tk.Label(self.meas_params_frame, name="empty_label_2")
        empty_label_2.grid(row=1, column=0)
        
        # The entries and labels are created here but packed in the
        # meas_params_frame afterwards.abs
        self.cw_field_start_label = ttk.Label(
            self.meas_params_frame,
            text="Start Field (G)",
            name="cw_field_start_label")
        self.cw_field_start_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_start_entry")
        self.cw_field_stop_label = ttk.Label(
            self.meas_params_frame,
            text="Stop Field (G)",
            name="cw_field_stop_label")
        self.cw_field_stop_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_stop_entry")
        self.cw_field_step_label = ttk.Label(
            self.meas_params_frame,
            text="Step Field (G)",
            name="cw_field_step_label")
        self.cw_field_step_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_step_entry")
        self.cw_field_center_label = ttk.Label(
            self.meas_params_frame, 
            text="Center Field (G)",
            name="cw_field_center_label"
        )
        self.cw_field_center_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_center_entry")
        self.cw_field_sweep_label = ttk.Label(
            self.meas_params_frame,
            text="Sweep Width (G)",
            name="cw_field_sweep_label")
        self.cw_field_sweep_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_sweep_entry")
        self.cw_field_npoints_label = ttk.Label(
            self.meas_params_frame,
            text="Field Points",
            name="cw_field_npoints_label")
        self.cw_field_npoints_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_field_npoints_entry")

        self.cw_mw_atten_label = ttk.Label(
            self.meas_params_frame,
            text="Microwave Attenuation (dB)",
            name="cw_mw_atten_label"
            )
        self.cw_mw_atten_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_mw_atten_entry")
        self.cw_mw_power_label = ttk.Label(
            self.meas_params_frame,
            text="Microwave Power (mW)",
            name="cw_mw_power_label"
        )
        self.cw_mw_power_entry = ttk.Entry(
            self.meas_params_frame,
            state="readonly",
            name="cw_mw_power_entry")
        self.cw_mod_freq_label = ttk.Label(
            self.meas_params_frame,
            text="Modulation Frequency (kHz)",
            name="cw_mod_freq_label"
        )
        self.cw_mod_freq_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_mod_freq_entry"
        )
        self.cw_mod_amp_label = ttk.Label(
            self.meas_params_frame,
            text="Modulation Amplitude (G)",
            name="cw_mod_amp_label"
        )
        self.cw_mod_amp_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_mod_amp_entry"
        )
        self.cw_mod_phase_label = ttk.Label(
            self.meas_params_frame, 
            text="Modulation phase (degrees)",
            name="cw_mod_phase_label"
        )
        self.cw_mod_phase_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_mod_phase_entry"
        )
        self.cw_harmonic_label = ttk.Label(
            self.meas_params_frame,
            text="Harmonic",
            name="cw_harmonic_label"
        )
        self.cw_harmonic_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_harmonic_entry"
        )
        
        self.cw_receiver_gain_label = ttk.Label(
            self.meas_params_frame,
            text="Receiver Gain (dB)",
            name="cw_receiver_gain_label"
        )
        self.cw_receiver_gain_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_receiver_gain_entry"
        )
        self.cw_conv_time_label = ttk.Label(
            self.meas_params_frame, 
            text="Conversion time (ms)",
            name="cw_conv_time_label"
        )
        self.cw_conv_time_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_conv_time_entry")
        self.cw_offset_label = ttk.Label(
            self.meas_params_frame,
            text="Offset (%)",
            name="cw_offset_label"
        )
        self.cw_offset_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_offset_entry"
        )
        self.cw_sweep_time_label = ttk.Label(
            self.meas_params_frame,
            text="Sweep Time (s)",
            name="cw_sweep_time_label"
        )
        self.cw_sweep_time_entry = ttk.Entry(
            self.meas_params_frame,
            name="cw_sweep_time_entry"
        )

        # Transient
        self.tr_field_start_label = ttk.Label(
            self.meas_params_frame,
            text="Start Field (G)",
            name="tr_field_start_label")
        self.tr_field_start_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_start_entry"
        )
        self.tr_field_stop_label = ttk.Label(
            self.meas_params_frame,
            text="Stop Field (G)",
            name="tr_field_stop_label"
        )
        self.tr_field_stop_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_stop_entry"
        )
        self.tr_field_step_label = ttk.Label(
            self.meas_params_frame,
            text="Step Field (G)",
            name="tr_field_step_label"
        )
        self.tr_field_step_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_step_entry"
        )
        self.tr_field_center_label = ttk.Label(
            self.meas_params_frame, 
            text="Center Field (G)",
            name="tr_field_center_label"
        )
        self.tr_field_center_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_center_entry"
        )
        self.tr_field_sweep_label = ttk.Label(
            self.meas_params_frame,
            text="Sweep Width (G)",
            name="tr_field_sweep_label"
        )
        self.tr_field_sweep_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_sweep_entry"
        )
        self.tr_field_npoints_label = ttk.Label(
            self.meas_params_frame,
            text="Field Points",
            name="tr_field_npoints_label"
        )
        self.tr_field_npoints_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_field_npoints_entry"
        )

        self.tr_mw_atten_label = ttk.Label(
            self.meas_params_frame,
            text="Microwave Attenuation (dB)",
            name="tr_mw_atten_label"
        )
        self.tr_mw_atten_entry = ttk.Entry(
            self.meas_params_frame,
            name="tr_mw_atten_entry"
        )
        self.tr_mw_power_label = ttk.Label(
            self.meas_params_frame,
            text="Microwave Power (mW)",
            name="tr_mw_power_label"
        )
        self.tr_mw_power_entry = ttk.Entry(
            self.meas_params_frame,
            state="readonly",
            name="tr_mw_power_entry"
        )

        # Set minsize of entry widgets and validation commands
        self._validators = {}
        self._validators["integer"] = self.win.register(
            lambda value: value.isdigit() or value == ""
        )
        self._validators["float"] = self.win.register(
            lambda value: value.replace('.', '', 1).isdigit() or value == ""
        )
        widgets = self.meas_params_frame.winfo_children()
        for widget in widgets:
            wname = widget.winfo_name()
            if '_entry' in wname:
                widget.config(justify="center", width=10)
                must_validate_float = [
                    "field_start",
                    "field_stop",
                    "field_step",
                    "field_center",
                    "field_width",
                    "mod_amp",
                    "mod_phase",
                    "mw_atten",
                    "conv_time",
                    "sweep_time",
                    "receiver_gain",
                    "offset"
                ]
                must_validate_int = [
                    "field_npoints",
                    "mod_freq",
                    "harmonic",
                ]
                if any([s in wname for s in must_validate_float]):
                    widget.configure(
                        validate="key",
                        validatecommand=(self._validators["float"], '%P')
                    )
                elif any([s in wname for s in must_validate_int]):
                    widget.configure(
                        validate="key",
                        validatecommand=(self._validators["integer"], '%P')
                    )

        # Display pane
        # In the display pane are present:
        # - fig_frame, on top, with the canvas for plotting datasets
        # - dset_tree_and_log_pane, at the bottom, divided in:
        #   - dset_tree_frame, on the left, for a radiobutton treeview of the
        #       loaded datasets
        #   - logs_frame, on the right, for a text area for logs (and maybe a
        #       terminal in the future?)
        self.display_pane = tk.PanedWindow(
            self.meas_frame,
            orient="vertical"
        )
        self.display_pane.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # Canvas for plots
        # Canvas to visualize datasets in the middle of the window. A vertical
        # toolbar is on the left side of the frame.
        self.fig_frame = tk.Frame(self.display_pane)
        self.display_pane.add(self.fig_frame, stretch="always")

        self.fig = Figure(dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()
        self.fig_canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.fig_frame
        )
        self.fig_canvas_widget = self.fig_canvas.get_tk_widget()
        self.fig_canvas_widget.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Navigation toolbar (on the left)
        self.fig_toolbar_frame = tk.Frame(self.fig_frame)
        self.fig_toolbar_frame.pack(side=tk.RIGHT, fill=tk.X)

        self.fig_toolbar = VerticalNavigationToolbar2Tk(
            self.fig_canvas,
            self.fig_toolbar_frame
        )
        self.fig_toolbar.update()
        self.fig_toolbar.pack(side=tk.TOP, expand=False)

        # Draw
        self.fig_canvas.draw()
        
        # Treeview with radiobuttons and logs text area
        # In this paned window: on the left, a frame with a custom made
        # treeview with radiobuttons to select the datasets to display on the
        # above fig canvas (with scrollbar); on the right, a frame with a text
        # area to print logs.
        self.dset_tree_and_logs_pane = tk.PanedWindow(
            self.display_pane, 
            orient="horizontal"
        )
        self.display_pane.add(
            self.dset_tree_and_logs_pane,
            stretch="always"
        )

        # Treeview frame
        # This treeview is updated every time a new dataset is loaded.
        # Moreover, the user can select the datasets to plot on the figure above
        # this frame.
        self.dset_tree_frame = tk.Frame(self.dset_tree_and_logs_pane)
        self.dset_tree_and_logs_pane.add(
            self.dset_tree_frame,
            stretch="always"
        )

        self.dset_tree = RadioTreeview(
            self.dset_tree_frame,
            columns=("name",),      # 'radio' will be added automatically
            show="tree headings"    # show tree column (#0) + headings
        )
        self.dset_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.dset_scrollbar = ttk.Scrollbar(
            self.dset_tree_frame,
            orient="vertical", 
            command=self.dset_tree.yview
        )
        self.dset_scrollbar.pack(side=tk.LEFT, fill="y")
        self.dset_tree.configure(
            yscrollcommand=self.dset_scrollbar.set
        )
        
        # Logs frame
        # Here a text area displays logs.
        self.logs_frame = tk.Frame(self.dset_tree_and_logs_pane)
        self.dset_tree_and_logs_pane.add(
            self.logs_frame, stretch="always"
        )
        self.logs_area = tk.Text(self.logs_frame)
        self.logs_area.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        

class XeprPlusGui():
    
    def __init__(self, logic):
        self._logic = logic
        
        # Call an instance of main window
        self._mw = XeprPlusMainWindow()
        self._print_log("Start XeprPlus.")
        
        # Threading variables
        self.executor = ThreadPoolExecutor(max_workers=1)  # Create once
        self.meas_fut = None  # Initialize as None
        
        # Change default window behavior of clicking "X" button
        self._mw.win.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Default values to entries
        for widget in self._mw.meas_params_frame.winfo_children():
            name = widget.winfo_name()
            if not "entry" in name:
                continue
            val = getattr(self._logic, name[:-6])
            widget.insert(0, val)

        # Connect widgets to functions
        # Menubar
        self._mw.file_menu.entryconfig(
            0,
            command=self.file_menu_load_dataset_clicked
        )
        self._mw.file_menu.entryconfig(
            1,
            command=self.file_menu_load_folder_clicked
            )
        self._mw.options_menu.entryconfig(0, command=self.open_xepr_api)
        self._mw.options_menu.entryconfig(1, command=self.close_xepr_api)

        # Buttons
        self._mw.send_to_spectrometer_button.config(
            command=self.send_to_spectrometer_button_clicked
        )

        # Entries in meas_params_frame
        start_stop_step = ["field_start", "field_stop", "field_step"]
        for widget in self._mw.meas_params_frame.winfo_children():
            name = widget.winfo_name()
            if not "entry" in name:
                continue
            if not any(s in name for s in start_stop_step):
                # Most common
                widget.bind("<FocusOut>", self.set_cw_tr_params)
            else:
                widget.bind("<FocusOut>", self.set_field_start_stop_step)

        # Treeview dset_tree
        self._mw.dset_tree.bind("<Button-1>", self.dset_tree_clicked)
        
        # TODO add some if statement
        # Auto connect to XeprAPI at startup
        self.open_xepr_api()
        

    def _on_closing(self):
        self._mw.win.destroy()
        self.close_xepr_api()
        

    def _print_log(self, msg):
        now = datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S >> ')
        self._mw.logs_area.insert(tk.END, now + msg + '\n')
        self._mw.logs_area.see(tk.END)
    
    
    def _update_gui(self, future=None, **kwargs):
        for param_name, value in kwargs.items():
            print(f"Trying to update {param_name}, {value}, ({type(value)})")
            fullname = param_name + "_entry"
            widget = self._mw.meas_params_frame.nametowidget(fullname)
            widget.delete(0, tk.END)
            widget.insert(0, round(value, 4))
            
        '''
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
    
    
    def dset_tree_clicked(self, event):
        old_selected_iids = self._mw.dset_tree.selected_iids.copy()
        row = self._mw.dset_tree.on_click(event)
        new_selected_iids = self._mw.dset_tree.selected_iids.copy()
        if row == -1:
            # The click did not hit a row of the treeview
            return

        # Radiobutton was not clicked but now it is clicked
        add_iids = [i for i in new_selected_iids if i not in old_selected_iids]
        for iid in add_iids:
            # The radiobutton is now clicked, add to the canvas
            idset = self._mw.dset_tree.index(iid)
            
            # TODO THIS SHOULD GO TO THE LOGIC?
            # The GUI instance should store no variables that are not 
            # or graphical parts
            dset = self._daw.dsets[idset]
            color = self.datan_get_new_plot_color()
            self._mw.ax.plot(dset.x,
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
        self._mw.ax.legend()
        self._mw.canvas.draw()


    def datan_get_new_plot_color(self):
        i = 0
        while True:
            if i not in self._mw.datan_selected_colors:
                self._daw.selected_colors.append(i)
                return self._daw.plot_colors[i]
            i += 1


    def daw_new_figure_tab_title(self):
        if not self.datan_fig_notebook_tabs:
            return "Fig 0"
        
        last_title = self.datan_fig_notebook_tabs[-1].tab_title
        return (last_title.split(" ")[0] + " " + 
                str(int(last_title.split(" ")[1]) + 1))


    def daw_remove_selected_colors(self, rmv_iids):
        for i in sorted(rmv_iids, reverse=True):
            self._daw.selected_colors.pop(i)


    def send_to_spectrometer_button_clicked(self):
        exp = self._mw.exp_select_combobox.get()
        self._logic.send_to_spectrometer(exp)
        
        frame = self._mw.meas_params_frame
        # Clear widgets from the frame
        for widget in frame.winfo_children():
            widget.grid_forget()

        exp_type = self._mw.exp_select_combobox.get()
        if exp_type == "CW":
            mode = "cw"
        elif exp_type == "Transient":
            mode = "tr"

        if mode == "cw":
            # cw
            self._mw.cw_field_start_label.grid(row=0, column=0, sticky="ew")
            self._mw.cw_field_start_entry.grid(row=0, column=1, sticky="ew")
            self._mw.cw_field_stop_label.grid(row=0, column=2, sticky="ew")
            self._mw.cw_field_stop_entry.grid(row=0, column=3, sticky="ew")
            self._mw.cw_field_step_label.grid(row=0, column=4, sticky="ew")
            self._mw.cw_field_step_entry.grid(row=0, column=5, sticky="ew")
            self._mw.cw_field_center_label.grid(row=1, column=0, sticky="ew")
            self._mw.cw_field_center_entry.grid(row=1, column=1, sticky="ew")
            self._mw.cw_field_sweep_label.grid(row=1, column=2, sticky="ew")
            self._mw.cw_field_sweep_entry.grid(row=1, column=3, sticky="ew")
            self._mw.cw_field_npoints_label.grid(row=1, column=4, sticky="ew")
            self._mw.cw_field_npoints_entry.grid(row=1, column=5, sticky="ew")
            self._mw.cw_mw_atten_label.grid(row=0, column=6, sticky="ew")
            self._mw.cw_mw_atten_entry.grid(row=0, column=7, sticky="ew")
            self._mw.cw_mw_power_label.grid(row=1, column=6, sticky="ew")
            self._mw.cw_mw_power_entry.grid(row=1, column=7, sticky="ew")
            self._mw.cw_mod_freq_label.grid(row=0, column=8, sticky="ew")
            self._mw.cw_mod_freq_entry.grid(row=0, column=9, sticky="ew")
            self._mw.cw_mod_amp_label.grid(row=0, column=10, sticky="ew")
            self._mw.cw_mod_amp_entry.grid(row=0, column=11, sticky="ew")
            self._mw.cw_mod_phase_label.grid(row=1, column=8, sticky="ew")
            self._mw.cw_mod_phase_entry.grid(row=1, column=9, sticky="ew")
            self._mw.cw_harmonic_label.grid(row=1, column=10, sticky="ew")
            self._mw.cw_harmonic_entry.grid(row=1, column=11, sticky="ew")
            self._mw.cw_receiver_gain_label.grid(row=0, column=12, sticky="ew")
            self._mw.cw_receiver_gain_entry.grid(row=0, column=13, sticky="ew")
            self._mw.cw_conv_time_label.grid(row=0, column=14, sticky="ew")
            self._mw.cw_conv_time_entry.grid(row=0, column=15, sticky="ew")
            self._mw.cw_offset_label.grid(row=1, column=12, sticky="ew")
            self._mw.cw_offset_entry.grid(row=1, column=13, sticky="ew")
            self._mw.cw_sweep_time_label.grid(row=1, column=14, sticky="ew")
            self._mw.cw_sweep_time_entry.grid(row=1, column=15, sticky="ew")

        elif mode == "tr":
            # Transient
            self._mw.tr_field_start_label.grid(row=0, column=0, sticky="ew")
            self._mw.tr_field_start_entry.grid(row=0, column=1, sticky="ew")
            self._mw.tr_field_stop_label.grid(row=0, column=2, sticky="ew")
            self._mw.tr_field_stop_entry.grid(row=0, column=3, sticky="ew")
            self._mw.tr_field_step_label.grid(row=0, column=4, sticky="ew")
            self._mw.tr_field_step_entry.grid(row=0, column=5, sticky="ew")
            self._mw.tr_field_center_label.grid(row=1, column=0, sticky="ew")
            self._mw.tr_field_center_entry.grid(row=1, column=1, sticky="ew")
            self._mw.tr_field_sweep_label.grid(row=1, column=2, sticky="ew")
            self._mw.tr_field_sweep_entry.grid(row=1, column=3, sticky="ew")
            self._mw.tr_field_npoints_label.grid(row=1, column=4, sticky="ew")
            self._mw.tr_field_npoints_entry.grid(row=1, column=5, sticky="ew")

            self._mw.tr_mw_atten_label.grid(row=0, column=6, sticky="ew")
            self._mw.tr_mw_atten_entry.grid(row=0, column=7, sticky="ew")
            self._mw.tr_mw_power_label.grid(row=1, column=6, sticky="ew")
            self._mw.tr_mw_power_entry.grid(row=1, column=7, sticky="ew")

        new_params = self._logic.get_cw_tr_params(mode=mode)

        self._mw.win.update()
        self._update_gui(new_params)


    def file_menu_load_dataset_clicked(self):
        self._mw.win.focus()
        load_files = filedialog.askopenfiles(
            parent=self._mw.win,
            title='Load files',
            filetypes =[('Description files', ['*.DSC', '*.DTA', '*.YGA'])]
        )
        
        for f in load_files:            
            if f.name.endswith((".DSC", ".DTA", ".YGA")):
                self.load_single_dataset(f.name)
                self._print_log("Load dataset ")
            else:
                self._print_log(
                    f"Could not load {f}.\nFile extension " + 
                    "must be '.DSC', '.DTA' or '.YGA'")

    
    def file_menu_load_folder_clicked(self):
        self._mw.win.focus()
        load_folder = filedialog.askdirectory(
            parent=self._mw.win, 
            title='Load folder'
        )
        
        if not load_folder:
            return

        dir_files = sorted(os.listdir(load_folder))
        load_files = [f for f in dir_files if f.endswith('.DSC')]

        if not load_files:
            # No files found
            self._print_log(f"No files with '.DSC' extension in {load_folder}")

        # Create a level in the treeview for the folder
        tree_upper_level = self._mw.datan_dset_tree.add_radio_item(
            "",
            tk.END,
            os.path.basename(load_folder)
        )
        self.datan_dset_tree_items.append(tree_upper_level)

        # Import items
        for f in load_files:
            self.load_single_dataset(
                os.path.join(load_folder, f),
                tree_upper_level
            )
        
        
    def load_single_dataset(self, path_to_file, folder=""):
        # Load from memory to Xepr secondary viewport
        self._logic.load_data(path_to_file, 'secondary')
        # Load from Xepr to window
        dset = self._logic.get_dataset(xeprset="secondary")
        # Store in meas_dsets
        params = {"title": dset.getTitle(),
                  "mw_freq": dset.getSPLReal("MWFQ"),
                  "mw_": dset.getSPLReal("MWPW")}
        ds = SimpleNamespace(x=dset.X, o=dset.O, params=params)
        self.meas_dsets = np.append(self.meas_dsets, ds)
        # Append to treeview
        self.datan_dset_tree_items.append(
            self._mw.datan_dset_tree.add_radio_item(
                folder,
                tk.END,
                params['title']
            )
        )


    def datan_dset_tree_clicked(self, event):
        old_selected_iids = self._mw.datan_dset_tree.selected_iids.copy()
        row = self._mw.datan_dset_tree.on_click(event)
        new_selected_iids = self._mw.datan_dset_tree.selected_iids.copy()
        if row == -1:
            # The click did not hit a row of the treeview
            return

        # Radiobutton was not clicked but now it is clicked
        add_iids = [i for i in new_selected_iids if i not in old_selected_iids]
        for iid in add_iids:
            # The radiobutton is now clicked, add to the canvas
            idset = self._mw.datan_dset_tree.index(iid)
            dset = self._daw.dsets[idset]
            color = self.datan_get_new_plot_color()
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


    def close_xepr_api(self):
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
            

    def open_xepr_api(self):
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
        
        # Handle error missing entries
        if save_folder == "" or save_name == "":
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select a folder and a name.")
            self._rmw.win.lift()
            self._rmw.win.focus()
            return
        
        # Handle error folder does not exist
        if not os.path.isdir(save_folder):
            self._mw.win.focus()
            tk.messagebox.showerror("Run measurement",
                                    "Please select an existing folder.")
            self._rmw.win.lift()
            self._rmw.win.focus()
            
        # Handle warning overwriting
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
        
        # Prepare for run measurement
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
            
        # Get the set tempeature value
        temperature_after = self._rmw.set_temperature_entry.get()
        
        self.meas_fut = self.executor.submit(meas_fun, *args)
        # update_gui as soon as starts and at the end
        self._update_gui()
        self.meas_fut.add_done_callback(self._update_gui)
        
        # Set new temperature at the end
        if temperature_after:
            self.meas_fut.add_done_callback(
                lambda fut: self._logic.set_temperature(temperature_after)
            )
            print_msg = f"Temperature set to {temperature_after}"
            self.meas_fut.add_done_callback(
                lambda fut: self._print_log(print_msg)
            )


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


    def set_field_start_stop_step(self, event):
        frame = self._mw.meas_params_frame
        start = float(frame.nametowidget(f"{mode}_field_start_entry").get())
        stop = float(frame.nametowidget(f"{mode}_field_stop_entry").get())
        step = float(frame.nametowidget(f"{mode}_field_step_entry").get())

        new_params = self._logic.set_field_start_stop_step(
            mode=mode,
            field_start=start,
            field_stop=stop,
            field_step=step 
        )
        self._update_gui(**new_params)


    def set_cw_tr_params(self, event):
        mode = event.widget.winfo_name()[:2]
        param = event.widget.winfo_name()[3:-6]
        value = float(event.widget.get())
        if not np.mod(value, 1):
            value = int(value)

        print(f"set_cw_tr_params: {param}, {value} ({type(value)})")

        new_params = self._logic.set_cw_tr_params(mode=mode, **{param: value})
        self._update_gui(**new_params)
    