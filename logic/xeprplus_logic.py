# Locate the XeprAPI module
from datetime import datetime, timedelta
import numpy as np
import os
import sys
import time

sys.path.insert(0, os.popen("Xepr --apipath").read())
import XeprAPI

class XeprPlusLogic():

    def __init__(self):
        self.xepr = None
        self.exps = []
        self.exp_names = []
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
        
        cur_offset = round(self.hidden_exp['LockOffset'].value, 2);
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
    
    
    def close_xepr_api(self):
        self.xepr.XeprClose()


    def open_xepr_api(self):
        try:
            self.xepr = XeprAPI.Xepr(verbose=False)
            self.hidden_exp = self.xepr.XeprExperiment('AcqHidden')
            return 0
        except:
            return -1


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
        self._command_wait(self.xepr.XeprCmds.aqExpNew, params)
        exp = self.xepr.XeprExperiment(self.exp_names[-1])
        self.exps.append(exp)
        
        
    def run_meas(self, folder, meas_name):
        cur_exp = self.xepr.XeprExperiment()
        self._command_wait(cur_exp.aqExpRunAndWait, waiting_time=5)
        self.save_meas(folder, meas_name)
        return 0
    
    
    def run_meas_goal_snr(self, folder, exp_name, goal_snr):
        # Create save folder and variables
        save_folder = os.path.join(folder, exp_name)
        os.mkdir(save_folder)
        
        # Run
        i_meas = 0
        cur_snr = 0
        cur_exp = self.xepr.XeprExperiment()
        while cur_snr < goal_snr:
            # Adjust lock offset
            status = self.adjust_lock_offset()
            # if status == -1:
                # logging.info('Exceeded max time for adjustLockOffset')
                
            i_meas += 1
            self._command_wait(cur_exp.aqExpRunAndWait, waiting_time=5)
            
            meas_name = exp_name + f"-{i_meas:05d}"
            self.save_meas(save_folder, meas_name)
            
            #
            # TODO calculate SNR
            # 
        
        return 0


    def run_meas_time_duration(self, folder, exp_name, hours, minutes):
        # Create save folder
        save_folder = os.path.join(folder, exp_name)
        os.mkdir(save_folder)
        
        # Run
        i_meas = 0
        time_now = datetime.now()
        time_end = time_now + timedelta(hours=hours, minutes=minutes)
        cur_exp = self.xepr.XeprExperiment()
        while time_now < time_end:
            # Adjust lock offset
            # status = self.adjust_lock_offset()
            # if status == -1:
                # logging.info('Exceeded max time for adjustLockOffset')
                
            i_meas += 1
            self._command_wait(cur_exp.aqExpRunAndWait, waiting_time=5)
            
            meas_name = exp_name + f"-{i_meas:05d}"
            self.save_meas(save_folder, meas_name)
            
            time_now = datetime.now()
            
        return 0


    def save_meas(self, folder, meas_name):
        save_path = os.path.join(folder, meas_name)
        cur_exp = self.xepr.XeprExperiment()
        # Exp to primary window
        self.xepr.XeprCmds.aqExpSelect(1, cur_exp.aqGetExpName())
        self.xepr.XeprCmds.vpSave("Current", "Primary", meas_name, save_path)
        # Exp to primary window
        self.xepr.XeprCmds.aqExpSelect(1, cur_exp.aqGetExpName())