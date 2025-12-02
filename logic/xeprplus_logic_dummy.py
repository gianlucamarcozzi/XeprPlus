# Locate the XeprAPI module
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
            
    
    def close_xepr_api(self):
        print('Close xepr api.')


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
        return 0

        
    def run_measurement(self, folder, filename):
        print("run simple measurement")
        print("folder:", folder)
        print("filename", filename)
        return 0
    
    def run_measurement_goal_snr(self, folder, filename, goal_snr):
        print("run measurement with goal snr")
        print("folder:", folder)
        print("filename", filename)
        print("goal_snr", goal_snr)
        return 0

    def run_measurement_for_time(self, folder, filename, for_time):
        print("run measurement for time")
        print("folder:", folder)
        print("filename", filename)
        print("for_time:", for_time, "hours")
        return 0
    

class DatasetXepr():

    def __init__(self):
        N = 1024
        self.X = np.linspace(320, 350, N)
        self.O = pes.gaussian(self.X,
                              self.X.mean() + random.uniform(-5, 5),
                              8,
                              0)

    def getSPLReal(self, par):
        if par == "MWFQ":
            return 9876543210
        elif par == "MWPQ":
            return 0.001
        
    def getTitle(self):
        return "Test set " + str(random.randint(10, 99))