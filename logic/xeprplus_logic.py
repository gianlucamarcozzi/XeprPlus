# Locate the XeprAPI module
from datetime import datetime, timedelta
import numpy as np
import os
import sys
import time

# sys.path.insert(0, os.popen("Xepr --apipath").read())
sys.path.insert(0, "/usr/local/lib/python3.9/dist-packages")

import XeprAPI

class XeprPlusLogic():

    def __init__(self):
        self.xepr = None
        self.exps = []
        self.exp_names = []
        self.stop_meas = 0
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
        MAX_TIME = 120
        WAIT_TIME = 1.5  # Not too short or the Lock offset is more prone to jumps
        GOAL_OFFSET = 5.
        
        cur_offset = round(self.hidden_exp['LockOffset'].value, 2)
        # if np.abs(cur_offset) > GOAL_OFFSET:
        #     ts = time.strftime("%H:%M:%S")  # Timestamp        
        #     print(ts + ': adjusting lock offset...')
            
        # The for loop is to check for jumps of the lock offset.
        start_time = time.time()

        while np.abs(cur_offset) > GOAL_OFFSET:
                
            # Check time
            current_time = time.time()
            if current_time - start_time > MAX_TIME:
                return -1  # Failed
                
            # Direction of adjustment of lock offset
            sgn_offset = np.sign(cur_offset)
            sgn_adjust = -sgn_offset
            
            self.xepr.XeprCmds.aqParStep(
                'AcqHidden', '*cwBridge.Frequency', 'Fine', sgn_adjust)
            
            # Wait and update
            time.sleep(WAIT_TIME)
            cur_offset = self.hidden_exp['LockOffset'].value
                
        return 0
    

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
        if self.xepr:
            self.xepr.XeprClose()


    def correct_baseline(self, data, dim=0, n=0, region=0):
        if data.ndim > 2:
            raise ValueError(f"Only 1D or 2D data supported, got ndim={data.ndim}.")

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
            # Restore initial dimension for 1D array
            data = np.squeeze(data)
            baseline = np.squeeze(baseline)
            
        datacorr = data - baseline
        
        return datacorr, baseline
    

    def create_new_experiment(self, exp_name):
        if exp_name == "CW":
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
        elif exp_name == "Transient":
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
        elif exp_name == "Pulse":
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
            
        self._command_wait(self.xepr.XeprCmds.aqExpNew, params)
        

    def get_dataset(self, xeprset='primary'):
        return self.xepr.XeprDataset(xeprset=xeprset)
    
        
    def load_data(self, path, viewport):
        # Viewport should be 'primary' or 'secondary'
        args = [path, 'None', viewport]
        self._command_wait(self.xepr.XeprCmds.vpLoad, *args)


    def open_xepr_api(self):
        try:
            self.xepr = XeprAPI.Xepr(verbose=False)
            self.hidden_exp = self.xepr.XeprExperiment('AcqHidden')
            return 0
        except Exception as e:
            print(e)
            return -1


    def run_meas(self, folder, meas_name):
        exp = self.xepr.XeprExperiment()
        self._command_wait(exp.aqExpRunAndWait, waiting_time=5)
        self.save_meas(folder, meas_name)
        return 0
    
    
    def run_meas_goal_snr(self, folder, exp_name, goal_snr):
        # Create save folder and variables
        save_folder = os.path.join(folder, exp_name)
        os.mkdir(save_folder)
        
        # Get current experiment
        exp = self.xepr.XeprExperiment()
        
        # Run first scan
        status = self.adjust_lock_offset()
        self._command_wait(exp.aqExpRunAndWait, waiting_time=5)
        meas_name = exp_name + f"-{1:05d}"
        self.save_meas(save_folder, meas_name)
        
        # SNR per scan
        # Calculate SNR after baseline correction
        dset = self.get_dataset(xeprset="primary")
        ord0 = np.array(dset.O)
        # Abscissa 1 is field for 1D data, time for 2D data
        x = np.array(dset.X)  # Abscissa 1
        
        if ord0.ndim == 1:
            # Correct along field
            bl_region_bfield = self.baseline_region(x, "width", 0.15)
            
            ord_fin, bl_fin = self.correct_baseline(
                ord0, region=bl_region_bfield)
        else:
            # Here x is time and y is field
            y = np.array(dset.Y)  # Abscissa 2
            # Correct along time
            # Assuming flash after 30 ns
            bl_region_t = self.baseline_region(x, "range", [0, 30])
            ord_mid, bl_mid = self.correct_baseline(
                ord0, dim=1, region=bl_region_t)

            # Correct along field
            bl_region_bfield = self.baseline_region(y, "width", 0.15)
            ord_fin, bl_fin = self.correct_baseline(
                ord_mid, dim=0, region=bl_region_bfield)
            
        # SNR of first scan
        snr, _, _ = self.calculate_snr(ord_fin, bl_region_bfield)
        
        n_scan = int(np.ceil((goal_snr/snr)**2))
        if n_scan < 2:
            return
        
        for i_meas in range(2, n_scan + 1):
            # Check if stop measurement was requested
            if self.stop_meas == 1:
                self.stop_meas = 0
                break
            
            # Adjust lock offset
            status = self.adjust_lock_offset()
            # if status == -1:
                # logging.info('Exceeded max time for adjustLockOffset')
                
            # Run scan
            self._command_wait(exp.aqExpRunAndWait, waiting_time=5)
            
            meas_name = exp_name + f"-{i_meas:05d}"
            self.save_meas(save_folder, meas_name)
        
        return 0


    def run_meas_time_duration(self, folder, exp_name, hours, minutes):
        # Create save folder
        save_folder = os.path.join(folder, exp_name)
        os.mkdir(save_folder)
        
        # Run
        i_meas = 0
        time_now = datetime.now()
        time_end = time_now + timedelta(hours=hours, minutes=minutes)
        exp = self.xepr.XeprExperiment()
        while time_now < time_end:
            # Check if stop measurement was requested
            if self.stop_meas == 1:
                self.stop_meas = 0
                break

            # Adjust lock offset
            status = self.adjust_lock_offset()
            # if status == -1:
                # logging.info('Exceeded max time for adjustLockOffset')
                
            i_meas += 1
            self._command_wait(exp.aqExpRunAndWait, waiting_time=5)
            
            meas_name = exp_name + f"-{i_meas:05d}"
            self.save_meas(save_folder, meas_name)
            
            time_now = datetime.now()
            
        return 0


    def save_meas(self, folder, meas_name):
        save_path = os.path.join(folder, meas_name)
        exp = self.xepr.XeprExperiment()
        # Exp to primary window
        self.xepr.XeprCmds.aqExpSelect(1, exp.aqGetExpName())
        self.xepr.XeprCmds.vpSave("Current", "Primary", meas_name, save_path)
        # Exp to primary window
        self.xepr.XeprCmds.aqExpSelect(1, exp.aqGetExpName())

        
    def send_to_spectrometer(self, exp_name):
        try:
            self.xepr.XeprExperiment(exp_name).aqExpActivate()
            return 0
        except XeprAPI.ExperimentError:
            self.create_new_experiment(exp_name)
            self.xepr.XeprExperiment(exp_name).aqExpActivate()
            return 1
    
    
    def set_cw_center_field(self, center_field):
        self.XeprExperiment()["CenterField"].value()
        
    def set_temperature(self, t):
        self.xepr.XeprCmds.aqParSet('AcqHidden', '*gTempCtrl.Temperature', t)
        