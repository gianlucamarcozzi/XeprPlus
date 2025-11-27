# Locate the XeprAPI module
import os
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


    def create_save_folder(project_folder, exp_name):
        save_folder = os.path.join(project_folder, exp_name)

        if not os.path.isdir(save_folder):
            os.mkdir(save_folder)
        else:
            print("save_folder already exists at location:\n%s\n" % save_folder)
            print("How to proceed? " + 
            "[O]verwrite, [A]ppend, [I]nsert new folder name, [C]ancel")
            while True:
                user_input = input()
                if user_input.lower() == "o":
                    shutil.rmtree(save_folder)
                    os.mkdir(save_folder)
                    break
                elif user_input.lower() == "a":
                    break
                elif user_input.lower() == "i":
                    while os.path.isdir(save_folder):
                        print("The folder %s already exists." % exp_name)
                        print("Give a new folder name:")
                        exp_name = input()
                        exp_name = exp_name.replace(" ", "_")
                        save_folder = os.path.join(project_folder, exp_name)
                    os.mkdir(save_folder)
                    break
                elif user_input.lower() == "c":
                    sys.exit(1)
                else:
                    print("Please enter 'o', 'a', 'i' or 'c'")
        return save_folder, exp_name
    
        # Initialize variables for saving the measurement
        save_folder, exp_name = ut.create_save_folder(project_folder, exp_name)
        meas_name_template = exp_name + "-%05u"
        filename_template = os.path.join(save_folder, meas_name_template)

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
        def repeat_experiment_transient(api):    
    
    
    # User defined parameters
    project_folder = "/home/gianlum33/files/projects/zech_psi/"
    exp_name = "ZePSI-E-021-010"
    STOP_AT_SNR = False
    GOAL_SNR = 100
    STOP_AT_TIMEDATE = False
    STOP_DATETIME = datetime.datetime(2025, 11, 7, 8, 0, 0, 0)
    NEXT_TEMP = 150
            
    xepr = api['xepr']
    exp = api['exp']
    hidden_exp = api['hidden_exp']
    exp_name_xepr = api['exp_name_xepr']
    
    # Start
    if exp.isRunning:
        exp.aqExpAbort()
        logging.info("Starting experiment %s" % exp_name)
        exp.aqExpRun()
    else:
        logging.info("Waiting for experiment to start...")
    
    logging.info('Experiment started')
    
    i = 1
    
    snr = 101
    while True:
        
        if STOP_AT_SNR:
            if snr > GOAL_SNR:
                logging.info('SNR (%.2f) > GOAL SNR (%.2f).' % (
                    snr, GOAL_SNR))
                break
            
        
        logging.info('Waiting for scans to finish')
        ut.command_wait(api['exp'].aqExpRunAndWait, waiting_time=5)

        meas_name = meas_name_template % (i)
        filename = filename_template % (i)
        
        xepr.XeprCmds.aqExpSelect(1, exp_name_xepr)  # Exp to primary window
        xepr.XeprCmds.vpSave("Current", "Primary", meas_name, filename)
        xepr.XeprCmds.aqExpSelect(1, exp_name_xepr)  # Exp to primary window
        
        logging.info("Acquired composite scan %u" % (i))
        
        # Adjust lock offset
        is_adjusted = ut.adjust_lock_offset(api)
        if not is_adjusted:
            logging.info('Exceeded max time for adjustLockOffset')
              
        if STOP_AT_TIMEDATE:
            t_now = datetime.datetime.now()
            if t_now > STOP_DATETIME:
                ut.aq_par_set(api, 'gTempCtrl', 'Temperature', NEXT_TEMP)
                logging.info("Stop datetime.")  
                logging.info("Exit repeat_experiment_transient.")  
                return
            
        # snr = ut.get_snr_tr(filename)
        i += 1
        
    logging.info("Exit repeat_experiment_transient.")  
    print("Exit repeat_experiment_transient.")  
    return



