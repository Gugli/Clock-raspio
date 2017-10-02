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
import datetime
import jinja2
import md5

SOUNDOUT_PERIOD = 1
CONFIG_SAVE_PERIOD = 30
CONFIG_FILE_PATH = '/var/lib/clock-raspio/config.json'
SHARE_FOLDER_PATH = '/usr/share/clock-raspio/'

EXAMPLE_FILE_PATH   = SHARE_FOLDER_PATH + 'wind-chimes_by_inspectorj.flac'
CSS_FILE_PATH       = SHARE_FOLDER_PATH + 'stylesheet.css'
TEMPLATE_FILE_PATH  = SHARE_FOLDER_PATH + 'template.html'

class SignalHandler:
    def __init__(self):
        self.must_leave = False
        
    def __call__(self, signum, frame):
        if signum == signal.SIGTERM:
            self.must_leave = True
            

class WebadminHandler(http.server.BaseHTTPRequestHandler):
    
    POST_SNOOZE        = 1
    
    GET_STYLESHEET      = 1
    GET_INDEX           = 2
    
    PATHS_FILES = '/files/'
    
    PATHS_POST = {
        '/snooze'       : POST_SNOOZE,
    }
    
    PATHS_GET = {
        '/stylesheet.css'       : GET_STYLESHEET,
        '/index.htm'            : GET_INDEX,
        '/index.html'           : GET_INDEX,
        '/'                     : GET_INDEX
    }
        
        
    logger = None
    template_index = None
    contents_stylesheet = None
    
    def log_message(self, format, *args):
        self.logger.info(format, *args)
    
    def do_GET(self):
        if self.path in self.PATHS_GET:   
            operation = self.PATHS_GET[self.path] 
            if operation == self.GET_STYLESHEET:
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
                self.end_headers()
                self.wfile.write(self.contents_stylesheet)
            elif operation == self.GET_INDEX:   
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.template_index.render().encode('utf-8'))
        elif self.path.startswith(self.PATHS_FILES):
            subpath = self.path[len(self.PATHS_FILES)]
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(404)
            self.end_headers()
        
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
        
    def do_POST(self):
        if self.path in self.PATHS_POST:         
            operation = self.PATHS_POST[self.path]
            if operation == self.POST_SNOOZE:
                pass
            self.send_response(200)
            self.end_headers()
        elif self.path.startswith(self.PATHS_FILES):
            subpath = self.path[len(self.PATHS_FILES)]
            self.send_response(200)
            self.end_headers()
        else:     
            self.send_error(404)
            self.end_headers()
        
class ConfigTimeslot:
    def __init__(self, set_sensible_default = False):
        self.begin_hour       = 0
        self.begin_minute     = 0
        self.begin_day        = 0
        self.duration         = 3600
        self.fade_in_duration = 600
        self.playlist_name    = ''
        
        if set_sensible_default:
            self.begin_hour       = 7
            self.begin_minute     = 15
            self.begin_day        = 0
            self.duration         = 3600
            self.fade_in_duration = 600
            self.playlist_name    = 'Default playlist'
        
    def get_id(self):    
        m = md5.new()
        m.update('{0}'.format(self.begin_hour))
        m.update('{0}'.format(self.begin_minute))
        m.update('{0}'.format(self.begin_day))
        m.update('{0}'.format(self.duration))
        m.update('{0}'.format(self.fade_in_duration))
        m.update(self.playlist_name)
        return m.digest()
        
    def to_json(self):
        dct = {}
        dct['begin_hour']       = self.begin_hour
        dct['begin_minute']     = self.begin_minute
        dct['begin_day']        = self.begin_day
        dct['duration']         = self.duration
        dct['fade_in_duration'] = self.fade_in_duration
        dct['playlist_name']    = self.playlist_name
        return dct
        
    def from_json(self, dct):
        self.begin_hour        = dct['begin_hour']      
        self.begin_minute      = dct['begin_minute']    
        self.begin_day         = dct['begin_day']       
        self.duration          = dct['duration']        
        self.fade_in_duration  = dct['fade_in_duration']
        self.playlist_name     = dct['playlist_name']   
            
class ConfigTimetable:
    PERIOD_ONEDAY = 1
    PERIOD_ONEWEEK = 2
    PERIOD_TWOWEEKS = 3
    PERIOD_ONEMONTH = 4
    def __init__(self, set_sensible_default = False):
        self.period = self.PERIOD_ONEDAY
        self.timeslots = []   
        if set_sensible_default:
            self.timeslots.append( ConfigTimeslot(set_sensible_default = set_sensible_default) )
    
    def to_json(self):
        dct = {}
        if   self.period == self.PERIOD_ONEDAY:   dct['period'] = 'PERIOD_ONEDAY'
        elif self.period == self.PERIOD_ONEWEEK:  dct['period'] = 'PERIOD_ONEWEEK'
        elif self.period == self.PERIOD_TWOWEEKS: dct['period'] = 'PERIOD_TWOWEEKS'
        elif self.period == self.PERIOD_ONEMONTH: dct['period'] = 'PERIOD_ONEMONTH'
        dct['timeslots'] = []
        for timeslot in self.timeslots:
            dct['timeslots'].append(timeslot.to_json())
        return dct
        
    def from_json(self, dct):
        if 'period' in dct: 
            if   dct['period'] == 'PERIOD_ONEDAY':   self.period = self.PERIOD_ONEDAY
            elif dct['period'] == 'PERIOD_ONEWEEK':  self.period = self.PERIOD_ONEWEEK
            elif dct['period'] == 'PERIOD_TWOWEEKS': self.period = self.PERIOD_TWOWEEKS
            elif dct['period'] == 'PERIOD_ONEMONTH': self.period = self.PERIOD_ONEMONTH
            
        if 'timeslots' in dct: 
            self.timeslots = []
            for dct_timeslot in dct['timeslots']:
                timeslot = ConfigTimeslot()
                timeslot.from_json(dct_timeslot)
                self.timeslots.append(timeslot)
            
    def get_current_timeslot(self, now):
        nowdt = datetime.datetime.fromtimestamp(now)
        current_day = 0
        (isoyear, isoweek, isoday) = nowdt.date().isocalendar()
        if   self.period == self.PERIOD_ONEDAY:   current_day = 0
        elif self.period == self.PERIOD_ONEWEEK:  current_day = (isoday - 1)
        elif self.period == self.PERIOD_TWOWEEKS: current_day = (isoday - 1) + (((isoweek-1)%2)*7)
        elif self.period == self.PERIOD_ONEMONTH: current_day = nowdt.date().day
        current_s = nowdt.hour * 3600 + nowdt.minute *60
        for timeslot in self.timeslots:
            matches_day = timeslot.begin_day == current_day
            timeslot_begin_s = (timeslot.begin_hour *3600 + timeslot.begin_minute * 60)
            matches_s = timeslot_begin_s <= current_s and current_s < timeslot_begin_s + timeslot.duration
            if( matches_day and matches_s ):
                fade_in_percent = (current_s - timeslot_begin_s) / (timeslot.fade_in_duration - timeslot_begin_s)
                if fade_in_percent >= 1. : fade_in_percent = 1.
                duration_percent = (current_s - timeslot_begin_s) / (timeslot.duration - timeslot_begin_s)
                return (timeslot, duration_percent, fade_in_percent)
        return None

class ConfigProfile:
    def __init__(self, set_sensible_default = False):
        self.timetable = ConfigTimetable(set_sensible_default = set_sensible_default)
        
    def to_json(self):
        dct = {}
        dct['timetable'] = self.timetable.to_json()
        return dct
        
    def from_json(self, dct):
        if 'timetable' in dct: 
            self.timetable = ConfigTimetable()
            self.timetable.from_json(dct)
        
    def get_current_timeslot(self, now):
        return self.timetable.get_current_timeslot(now)
        
class ConfigPlaylist:
    def __init__(self, set_sensible_default = False):
        self.items = []
        if set_sensible_default:
            self.items.append(EXAMPLE_FILE_PATH)
        
    def to_json(self):
        dct = {}
        dct['items'] = []
        for item_name in self.items:            
            dct['items'].append(item_name)
        return dct
            
    def from_json(self, dct):    
        if 'items' in dct:
            dct_items = dct['items']
            for dct_item in dct_items:            
                self.items.append(dct_item)
                
class Config:
    def __init__(self, set_sensible_default = False):
        self.profiles = {}        
        self.current_profile_name = ''
        self.playlists = {}        
        
        if set_sensible_default:           
            profile_work = ConfigProfile(set_sensible_default = set_sensible_default)    
            self.profiles['Work'] = profile_work
            
            profile_holidays = ConfigProfile()
            self.profiles['Holidays'] = profile_holidays            
            
            playlist_webradio = ConfigPlaylist(set_sensible_default = set_sensible_default)
            self.playlists['Default playlist'] = playlist_webradio
            
            self.current_profile_name = 'Work'            
           
    def to_json(self):
        dct = {}
        dct['current_profile_name'] = self.current_profile_name
        dct['profiles'] = {}
        for profile_name in self.profiles:            
            dct['profiles'][profile_name] = self.profiles[profile_name].to_json()
        dct['playlists'] = {}
        for playlist_name in self.playlists:            
            dct['playlists'][playlist_name] = self.playlists[playlist_name].to_json()
            
        return dct
        
    def from_json(self, dct):
        if 'current_profile_name' in dct:
            self.current_profile_name = dct['current_profile_name']
            
        if 'profiles' in dct:
            dct_profiles = dct['profiles']
            for dct_profile in dct_profiles:
                profile = ConfigProfile()
                profile.from_json(dct_profiles[dct_profile])
                self.profiles[dct_profile] = profile
                
        if 'playlists' in dct:
            dct_playlists = dct['playlists']
            for dct_playlist in dct_playlists:
                playlist = ConfigPlaylist()
                playlist.from_json(dct_playlists[dct_playlist])
                self.playlists[dct_playlist] = playlist
            
    def get_current_timeslot(self, now):
        if not self.current_profile_name in self.profiles:
            return None
            
        current_profile = self.profiles[self.current_profile_name]
        return current_profile.get_current_timeslot(now)
    
    def get_playlist_from_timeslot(self, timeslot):
        if not timeslot.playlist_name in self.playlists:
            return None
        return self.playlists[timeslot.playlist_name]
        
class ConfigDecoder:
    def __call__(self, dct):
        config = Config()
        config.from_json(dct)
        return config
        
class ConfigEncoder:
    def __call__(self, object):
        return object.to_json()      
    
def config_load(logger, path):    
    # no file return new config
    if not os.path.isfile(path):
        return Config(set_sensible_default = True)
    
    try:
        with open(path, "r") as file:
            config_decoder = ConfigDecoder()
            dct = json.load(file)
            return config_decoder(dct)  
    except:
        logger.debug('An error occured while trying to read the config file', exc_info=True)
        # backup file
        shutil.copyfile(path, path + '.bak')
        # create new config
        return Config(set_sensible_default = True)


def config_save(logger, path, config):
    with open(path, "w") as file:
        config_encoder = ConfigEncoder()
        dct = config_encoder(config)
        json.dump(dct, file)
        
def audio_set_volume(percent):
    pass
    
def audio_set_playlist(playlist):
    pass
    
def audio_play()       
    pass
    
def main_loop():
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
    
    WebadminHandler.logger = logger
    with open(CSS_FILE_PATH, 'rb') as file:
        WebadminHandler.contents_stylesheet = file.read()
    with open(TEMPLATE_FILE_PATH, 'rb') as file:
        WebadminHandler.template_index = jinja2.Template(file.read().decode('utf-8'))
    
    webadmin_server = http.server.HTTPServer( server_address=('', 80), RequestHandlerClass=WebadminHandler )
    webadmin_server.timeout = 0.1
    
    signal_handler = SignalHandler()
    signal.signal(signal.SIGTERM, signal_handler)
    

    config = config_load(logger, CONFIG_FILE_PATH)
    # imediately save config to apply format updates
    config_save(logger, CONFIG_FILE_PATH, config)
    
    logger.info('Starting daemon')
    latest_soundout_tick = 0
    previous_timeslot_id = None
    config_save_latest_tick = time.time()
    config_save_requested = False
    while True:    
        now = time.time()
        
        # Leave
        if signal_handler.must_leave:
            break
                        
        # Run webadmin
        webadmin_server.handle_request()
                
        # save config
        if config_save_requested and now > config_save_latest_tick + CONFIG_SAVE_PERIOD:
            config_save_requested = False
            config_save_latest_tick = now
            config_save(logger, CONFIG_FILE_PATH, config)
                
        # Soundout
        if now > latest_soundout_tick + SOUNDOUT_PERIOD:
            latest_soundout_tick = now
            # Check if we should be playing
            result = config.get_current_timeslot(now)
            if result != None:
                (current_timeslot, duration_percent, fade_in_percent ) = result
                logger.info('Updating sound player')
                audio_set_volume( fade_in_percent )
                new_timeslot_id = current_timeslot.get_id()
                if new_timeslot_id != previous_timeslot_id:
                    previous_timeslot_id = new_timeslot_id
                    # set current playlist
                    audio_set_playlist( config.get_playlist_from_timeslot(current_timeslot) )                    
                    # start playback
                    audio_play()
            else:
                previous_timeslot_id = None
                    
    logger.info('Exiting daemon')

if __name__ == "__main__":
    main_loop()
