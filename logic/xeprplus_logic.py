# Locate the XeprAPI module
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
            
    def _on_closing(self):
        self.xepr.XeprClose()
            
    def connect_to_xepr_api(self):
        self.xepr = XeprAPI.Xepr()
        self.hidden_exp = self.xepr.XeprExperiment('AcqHidden')
        return 0

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
        