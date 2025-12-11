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
        if exp_type == 0:
            self.exp_names.append(self._check_exp_name('cwEPR'))
            params = [self.exp_names[-1], 'C.W.', 'Field', 'None', 
                      "'Signal channel'", 'Off', 'Off', 'On']
        elif exp_type == 1:
            self.exp_names.append(self._check_exp_name('trEPR'))
            params = [self.exp_names[-1], 'C.W.', 'Time', 'Field', 
                      "'Transient recorder'", 'Off', 'Off', 'On']
        elif exp_type == 2:
            self.exp_names.append(self._check_exp_name('pEPR'))
            params = [self.exp_names[-1], 'Pulse', 'Field', 'None', 
                      "'Transient recorder'", 'Off', 'Off', 'On']
        else:
            raise Exception("exp_type must be a number between 0 and 2.")
        print("Create new experiment.")
        self.exps.append(params)


    def get_dataset(self, xeprset='primary'):
        print('Get dataset. viewport:', xeprset)
        dset = DatasetXepr()
        return dset


    def load_data(self, path, viewport):
        print('Load data. path:', path, ', viewport:', viewport)


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
    