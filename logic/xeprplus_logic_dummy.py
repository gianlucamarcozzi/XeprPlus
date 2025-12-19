# %%
#  Locate the XeprAPI module
from datetime import datetime, timedelta
import numpy as np
import os
import peasyspin as pes
import random
import sys
import time

class XeprPlusLogic():

    def __init__(self):
        self.xepr = None
        self.exp_names = ["CW", "Transient", "Pulse"]
        self.stop_meas = 0

        # Default variables
        self.cw_field_start = 3300.
        self.cw_field_stop = 3400.
        self.cw_field_step = 1.
        self.cw_field_center = 335.0
        self.cw_field_sweep = 1000.
        self.cw_field_npoints = 1001
        self.cw_mw_atten = 60
        self.cw_mw_power = 200e-6
        self.cw_mod_freq = 100
        self.cw_mod_amp = 1.
        self.cw_mod_phase = 0
        self.cw_harmonic = 1
        self.cw_receiver_gain = 60.
        self.cw_offset = 0.
        self.cw_conv_time = 5.12  # ms
        self.cw_sweep_time = 5.12 * self.cw_field_npoints / 1000  # s
        self.tr_field_start = 3300.
        self.tr_field_stop = 3400.
        self.tr_field_step = 10.
        self.tr_field_center = 3350.
        self.tr_field_sweep = 1000.
        self.tr_field_npoints = 1001
        self.tr_mw_atten = 60.
        self.tr_mw_power = 200e-6

        # Dictionaries with mapping between XeprPlus and Xepr parameters 
        cw_param_map = {
            'field_center': '*fieldCtrl.CenterField',
            'field_sweep': '*fieldCtrl.SweepWidth', 
            'field_npoints': '*signalChannel.Resolution',
            'mod_freq': '*signalChannel.ModFreq',
            'mod_amp': '*signalChannel.ModAmp',
            'mod_phase': '*signalChannel.ModPhase',
            'harmonic': '*signalChannel.Harmonic',
            'mw_atten': '*mwBridge.PowerAttenuation',
            'conv_time': '*signalChannel.ConvTime',
            'sweep_time': '*signalChannel.SweepTime',
            'receiver_gain': '*mwBridge.Gain',
            'offset': '*signalChannel.Offset'
        }

        tr_param_map = {
            'field_center': '*fieldCtrl.CenterField',
            'field_sweep': '*fieldCtrl.SweepWidth', 
            'field_npoints': '*signalChannel.Resolution',
            'mw_atten': '*mwBridge.PowerAttenuation',
        }
        return

    def _check_exp_name(self, exp_name):
        if not exp_name in self.exp_names:
            return exp_name
        else:
            i = 1
            while f"{exp_name}:{i}" in self.exp_names:
                i += 1
        return exp_name
    

    def _command_wait(self, command, parameters='', waiting_time=0.25):
            if parameters == '':
                command()
            else:
                if not isinstance(parameters, list):
                    parameters = [parameters]
                command(*parameters)
            
            time.sleep(waiting_time)
            
    
    def adjust_lock_offset(self):
        return
    

    def baseline_region(self, x, bl_type="width", region=0.15):
        if bl_type == "width":
            left = np.min(x) + (np.max(x) - np.min(x)) * region
            right = np.max(x) - (np.max(x) - np.min(x)) * region
            return (x <= left) | (x >= right)
        elif bl_type == "range":
            if not isinstance(region, list):
                raise Exception(
                    "For bl_type equal 'range' region must be a list.")
            if not isinstance(region[0], list):
                region = [region]
                if not len(region[0]) == 2:
                    raise Exception(
                        "For bl_type equal 'range' region must be a list of " + 
                        "len 2 or a list of lists of len 2.")
            if isinstance(region[0], list):
                for reg in region:
                    if not len(reg) == 2:
                        raise Exception(
                            "For bl_type equal 'range' region " +
                            "be a list of len 2 or a list of lists of len 2.")
            
            bl = [False for _ in range(len(x))]
            for reg in region:
                new_bl = (x >= reg[0]) & (x <= reg[1])
                bl = bl | new_bl
            return bl
        

    def calculate_snr(self, y, noise_idx, mode="std"):
        if y.ndim == 1:
            sig_lev = np.max(y) - np.min(y)
            if mode == "std":
                noise_lev = np.std(y[noise_idx])
            elif mode == "pkpk":
                noise_lev = np.max(y[noise_idx]) - np.min(y[noise_idx])
            else:
                raise Exception("mode must be 'std' or 'pkpk'")
            snr = sig_lev / noise_lev

            return snr, sig_lev, noise_lev
        elif y.ndim == 2:
            # First identify the time slice
            t_argmaxs = np.argmax(np.abs(y), axis=1)
            t_argmax = np.max(np.bincount(t_argmaxs))
            return self.calculate_snr(y[:, t_argmax], noise_idx, mode)


    def close_xepr_api(self):
        print('Close xepr api.')


    def correct_baseline(self, data, dim=0, n=0, region=0):
        if data.ndim > 2:
            raise ValueError(
                f"Only 1D or 2D data supported, got ndim={data.ndim}.")

        if dim not in (0, 1):
            raise ValueError("dim must be 0, 1. Only 1D or 2D data supported.")
        
        # One dim fit
        if isinstance(n, (list, tuple, np.ndarray)):
            if len(n) != 1:
                raise ValueError("For 1D fit, polynomial order n must be a scalar")
            n = n[0]

        if n >= data.shape[dim]:
            raise ValueError(
                f"Polynomial order n={n} must be smaller than"
                "data size {data.shape[dim]}"
            )
        
        orig_ndim = data.ndim
        if orig_ndim == 1:
            data = np.reshape(data, [data.size, 1])

        x = np.linspace(-1, 1, data.shape[dim])
        poly_exponents = np.arange(n + 1)
        # Vandermonde matrix shape (len(x), n+1)
        D = x[:, None] ** poly_exponents[None, :]

        if dim == 1:
            # The dimension along which the data is corrected must be dim 0
            data = data.T

        if region is not None:
            if region.size != data.shape[0]:
                raise ValueError("Region length must match data dimension")
            p = np.linalg.lstsq(D[region], data[region, :], rcond=None)[0]
        else:
            p, _, _, _ = np.linalg.lstsq(D, data, rcond=None)
        
        baseline = D.dot(p)

        if dim == 1:
            # Transpose back if necessary
            baseline = baseline.T
            data = data.T

        if orig_ndim == 1:
            data = np.squeeze(data)
            baseline = np.squeeze(baseline)
            
        datacorr = data - baseline
        
        return datacorr, baseline


    def create_new_experiment(self, exp_type):
        if exp_name == self.exp_names[0]:
            # CW
            params = [
                exp_name,
                'C.W.',
                'Field',
                'None',
                "'Signal channel'",
                'Off',
                'Off',
                'Off'
            ]
        elif exp_name == self.exp_names[1]:
            # Transient
            params = [
                exp_name,
                'C.W.',
                'Time',
                'Field',
                "'Transient recorder'",
                'Off',
                'Off',
                'Off'
            ]
        elif exp_name == self.exp_names[2]:
            # Pulse
            params = [
                exp_name,
                'Pulse',
                'Field',
                'None',
                "'Transient recorder'",
                'Off',
                'Off',
                'Off'
            ]
        print("Create new experiment.")
        # self.exps.append(params)


    def get_dataset(self, xeprset='primary'):
        print('Get dataset. viewport:', xeprset)
        dset = DatasetXepr()
        return dset


    def get_field_start_stop_step(
        self, mode, field_center, field_sweep, field_npoints
    ):
        # Validate input
        if not isinstance(field_center, (int, float)) or field_center < 0:
            return
        if not isinstance(field_sweep, (int, float)) or field_sweep < 0:
            return
        if not isinstance(field_npoints, int) or field_npoints < 1:
            return
        if not isinstance(mode, str) or (mode != "cw" and mode != "tr"):
            print("mode must be 'cw' or 'tr'")
            return

        # Calculate new start, stop, step
        field_start = field_center - field_sweep / 2
        field_stop = field_center + field_sweep / 2
        field_step = (field_stop - field_start) / (field_npoints - 1)
        
        return field_start, field_stop, field_step


    def get_field_center_sweep_npoints(
        self, mode, field_start, field_stop, field_step
    ):
        # Validate input
        if not isinstance(field_start, (int, float)) or field_start < 0:
            return
        if not isinstance(field_stop, (int, float)) or field_stop < 0:
            return
        if not isinstance(field_step, (int, float)) or field_step < 0:
            return
        if not isinstance(mode, str) or (mode != "cw" and mode != "tr"):
            print("mode must be 'cw' or 'tr'")
            return

        # Calculate new center, sweep, npoints
        field_center = (field_stop + field_start) / 2
        field_sweep = field_stop - field_start
        field_npoints = int((field_stop - field_start) / field_step) + 1
        
        return field_center, field_sweep, field_npoints


    def load_data(self, path, viewport):
        # Viewport should be 'primary' or 'secondary'
        args = [path, 'None', viewport]
        self._command_wait(self.xepr.XeprCmds.vpLoad, *args)


    def open_xepr_api(self):
        print('Open xepr api.')
        self.xepr = XeprXepr()
        return 0

        
    def run_meas(self, folder, meas_name):
        print("run simple measurement")
        print("folder:", folder)
        print("meas_name:", meas_name)
        return 0
    

    def run_meas_goal_snr(self, folder, exp_name, goal_snr):
        print("run measurement with goal snr")
        print("folder:", folder)
        print("exp_name", exp_name)
        print("goal_snr", goal_snr)
        return 0


    def run_meas_time_duration(self, folder, exp_name, hours, minutes):
        print("run_meas_time_duration")
        print("folder:", folder)
        print("exp_name", exp_name)
        print("hours:", hours)
        print("minutes:", minutes)

        time_now = datetime.now()
        time_end = time_now + timedelta(hours=hours, minutes=minutes)
        while time_now < time_end:
            print('self stop:', self.stop)
            time.sleep(3)
            if self.stop == 1:
                break

        return 0
    

    def save_meas(self, folder, meas_name):
        print("save_meas")


    def send_to_spectrometer(self, exp):
        print("Send to spectrometer:", exp)
        print("Get values from spectrometer (here default values).")
    
    
    def set_cw_tr_params(self, mode, **kwargs):
        # TODO there is no signal channel in transient experiment, therefore 
        # probably the resolution of the field_npoints must be set in another
        # way if mode == transient

        # Validate input
        if not isinstance(mode, str) or (mode != "cw" and mode != "tr"):
            print("mode must be 'cw' or 'tr'")
            return

        new_params = {}
        if mode == "cw":
            param_map = cw_param_map
        elif mode == "tr":
            param_map = tr_param_map

        for param_name, value in kwargs.items():
            # Validate input
            if value is None:
                continue
            if not param_name in param_map:
                print(f"{param_name} is not a supported parameter.")
                return
            if param_name in ["field_center", "field_sweep"]:
                if not isinstance(value, (int, float)) or value < 1:
                    continue
            elif param_name == "field_npoints":
                if not isinstance(value, int) or value < 1:
                    continue
            elif param_name == "mod_freq":
                if not isinstance(value, int) or value < 1:
                    continue
            elif param_name == "mod_amp":
                if (not isinstance(value, (int, float)) or
                        value <= 0 or
                        value >= 10):  
                    continue
            elif param_name == "mod_phase":
                if not isinstance(value, (int, float)):
                    continue
            elif param_name == "harmonic":
                if not isinstance(value, int) or value < 0 or value > 1:
                    continue
            elif param_name == "mw_atten":
                if (not isinstance(value, (int, float)) or
                        value < 0 or
                        value > 60):
                    continue
            elif param_name == "conv_time":
                if not isinstance(value, (int, float)) or value < 0:
                    continue
            elif param_name == "sweep_time":
                if not isinstance(value, (int, float)) or value < 0:
                    continue
            elif param_name == "receiver_gain":
                if (not isinstance(value, (int, float)) or
                        value < 0 or
                        value > 60):
                    continue
            elif param_name == "offset":
                if not isinstance(value, (int, float)):
                    continue
            
            # Set new parameter on the hardware
            print(f"\nSet {param_name}: {value}")
            setattr(self, f"{mode}_{param_name}", value)

        # Get all parameters from the hardware
        for param_name, cmd in param_map.items():
            par = f"{mode}_{param_name}"
            new_params[par] = getattr(self, par)

        # Update field start, stop, step if necessary 
        field_params = ["field_center", "field_sweep", "field_npoints"]
        if any(s in kwargs.keys() for s in field_params):
            start, stop, step = self.get_field_start_stop_step(
                mode=mode,
                field_center=new_params[f"{mode}_field_center"],
                field_sweep=new_params[f"{mode}_field_sweep"],
                field_npoints=new_params[f"{mode}_field_npoints"]
            )
            new_params[f"{mode}_field_start"] = start
            new_params[f"{mode}_field_stop"] = stop
            new_params[f"{mode}_field_step"] = step

        return new_params


    def set_field_start_stop_step(
        self, mode, field_start, field_stop, field_step
    ):
        # Validate input
        if not isinstance(field_start, (int, float)) or field_start < 0:
            return
        if not isinstance(field_stop, (int, float)) or field_stop < 0:
            return
        if not isinstance(field_step, (int, float)) or field_step < 0:
            return
        if not isinstance(mode, str) or (mode != "cw" and mode != "tr"):
            print("mode must be 'cw' or 'tr'")
            return

        # Adjust stop
        if field_stop <= field_start:
            stop_corrected = field_start + field_step
            print("\nSTOP CORRECTED:", stop_corrected)
        else:
            stop_corrected = (
                field_stop + np.mod((field_stop - field_start), field_step)
            )
        
        # Calculate new start, stop, step
        center, sweep, npoints = self.get_field_center_sweep_npoints(
            mode=mode,
            field_start=field_start,
            field_stop=stop_corrected,
            field_step=field_step
        )

        new_params = self.set_cw_tr_params(
            mode=mode,
            field_center=center,
            field_sweep=sweep,
            field_npoints=npoints,
            )
        
        return new_params


    def set_temperature(self, temperature):
        args = ['AcqHidden', '*gTempCtrl.Temperature', temperature]
        self._command_wait(self.xepr.XeprCmds.aqParSet, *args)


class DatasetXepr():

    def __init__(self):
        N = 1024
        self.X = np.linspace(320, 350, N)
        self.O = pes.gaussian(self.X,
                              self.X.mean() + random.uniform(-5, 5),
                              2,
                              0)

    def getSPLReal(self, par):
        if par == "MWFQ":
            return 9876543210
        elif par == "MWPQ":
            return 0.001
        
    def getTitle(self):
        return "Test set " + str(random.randint(10, 99))
    
class XeprXepr():
    def XeprActive(self):
        return 1
    