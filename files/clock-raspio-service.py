#!/usr/bin/python
import time
import http.server
import signal
import os
import logging
import sys
import json
import pickle
import shutil

SOUNDOUT_PERIOD = 1
#CONFIG_FILE_PATH = '/var/lib/clock-raspio/config.json'
CONFIG_FILE_PATH = 'C:\\Users\\Gugli\\Desktop\\config.json'

class SignalHandler:
    def __init__(self):
        self.must_leave = False
        
    def __call__(self, signum, frame):
        if signum == signal.SIGTERM:
            self.must_leave = True
            

class WebadminHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(b"<html><body><h1>hi!</h1></body></html>")

    def do_HEAD(self):
        self._set_headers()
        
        
    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write(b"<html><body><h1>POST!</h1></body></html>")

class ConfigTimeslot:
    def __init__(self):
        self.delay_from_timetable = 0
            

class ConfigTimetable:
    def __init__(self):
        self.timeslots = []        
    

class ConfigProfile:
    def __init__(self):
        self.Timetable = ConfigTimetable()
        
    def to_json(self):
        pass
        
    def from_json(self, dct):
        pass
        
    def get_current_timeslot(self, now):
        return None
        
class ConfigPlaylist:
    def __init__(self):
        self.items = []
    
class Config:
    def __init__(self, set_sensible_default = False):
        self.profiles = {}        
        self.current_profile_name = ''
        self.playlists = {}        
        
        if set_sensible_default:
            profile_work = ConfigProfile()
            profile_holidays = ConfigProfile()        
            self.profiles['Work'] = profile_work
            self.profiles['Holidays'] = profile_holidays            
            self.current_profile_name = 'Work'
           
    def to_json(self):
        dct = {}
        dct['profiles'] = {}
        for profile_name in self.profiles:            
            dct['profiles'][profile_name] = self.profiles[profile_name].to_json()
        return dct
        
    def from_json(self, dct):
        dct_profiles = dct['profiles']
        for dct_profile in dct_profiles:
            profile = ConfigProfile()
            profile.from_json(dct_profiles[dct_profile])
            self.profiles[dct_profile] = profile
            
    def get_current_timeslot(self, now):
        if not self.current_profile_name in self.profiles:
            return None
            
        current_profile = self.profiles[self.current_profile_name]
        return current_profile.get_current_timeslot(now)
    
class ConfigDecoder:
    def __call__(self, dct):
        config = Config()
        config.from_json(dct)
        return config
        
class ConfigEncoder:
    def __call__(self, object):
        return object.to_json()      
    
def config_load(path):    
    # no file return new config
    if not os.path.isfile(path):
        return Config(set_sensible_default = True)
    
    try:
        with open(path, "r") as file:
            config_decoder = ConfigDecoder()
            config = json.load(file, object_hook=config_decoder)
            return config    
    except:
        # An error occured while trying to read the config file    
        # backup file
        shutil.copyfile(path, path + '.bak')
        # create new config
        return Config(set_sensible_default = True)

def config_save(path, config):
    with open(path, "w") as file:
        config_encoder = ConfigEncoder()
        dct = config_encoder(config)
        json.dump(dct, file)
        
def main_loop():
    webadmin_server = http.server.HTTPServer( server_address=('', 80), RequestHandlerClass=WebadminHandler )
    webadmin_server.timeout = 0.1
    
    signal_handler = SignalHandler()
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logging_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging_stdout = logging.StreamHandler(sys.stdout)
    logging_stdout.setFormatter(logging_formatter)
    logging_stdout.setLevel(logging.DEBUG)
    logging_stderr = logging.StreamHandler(sys.stderr)   
    logging_stderr.setFormatter(logging_formatter) 
    logging_stderr.setLevel(logging.ERROR)
    logger.addHandler(logging_stdout)
    logger.addHandler(logging_stderr)

    config = config_load(CONFIG_FILE_PATH)
    # imediately save config to apply format updates
    config_save(CONFIG_FILE_PATH, config)
    
    logger.info('Starting daemon')
    latest_soundout_tick = 0
    while True:    
        now = time.time()
        logger.info('Loop at {0}'.format(now))
        
        # Leave
        if signal_handler.must_leave:
            break
                        
        # Run webadmin
        webadmin_server.handle_request()
                
        # Soundout
        if now > latest_soundout_tick + SOUNDOUT_PERIOD:
            logger.info('Apply sound ')
            latest_soundout_tick = now
            # Check if we should be playing
            current_timeslot = config.get_current_timeslot(now)
            if current_timeslot != None:
                pass
                    
    logger.info('Exiting daemon')

if __name__ == "__main__":
    main_loop()
