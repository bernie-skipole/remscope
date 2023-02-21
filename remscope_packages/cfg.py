
# Edit this _CONFIG dictionary to set configuration parameters

# astronomy centre is 53:42:40N 2:09:16W

import csv, os

# The _CONFIG dictionary holds required constants, further items are added on startup
# by calling set_projectfiles(projectfiles) once the projectfiles directory is known

_CONFIG = { 
            'latitude' : 53.7111,
            'longitude' : -2.1544,
            'elevation' : 316,
            'redis_ip' : 'localhost',
            'redis_port' : 6379,
            'redis_auth' : '',
            'door_name' : "Roll off door",             # The name as given by the indi driver
            'telescope_name' : 'Telescope Simulator'   # The name as given by the indi driver
          }

# This is a dictionary of nominal planet magnitudes for the star chart
_PLANETS = {"mercury":  0.23,
            "venus":   -4.14,
            "mars":     0.71,
            "jupiter": -2.20,
            "saturn":   0.46,
            "uranus":   5.68,
            "neptune":  7.78,
            "pluto":   14.00}


# This list is filled in from a csv file on the first call to get_constellation_lines()
_CONSTELLATION_LINES = []


def set_projectfiles(projectfiles):
    global _CONFIG
    _CONFIG['astrodata_directory'] = os.path.join(projectfiles, 'astrodata')
    _CONFIG['servedfiles_directory'] = os.path.join(projectfiles, 'astrodata', 'served')
    _CONFIG['dbbackups_directory'] = os.path.join(projectfiles, 'astrodata', 'served', 'backups')
    _CONFIG['planetdb'] = os.path.join(projectfiles, 'astrodata', 'planet.db')
    _CONFIG['constellation_lines'] = os.path.join(projectfiles, 'astrodata', 'lines.csv')
    _CONFIG['star_catalogs'] = os.path.join(projectfiles, 'astrodata', 'dbases')
    _CONFIG['maindb'] = os.path.join(projectfiles, 'astrodata', 'maindb', 'main.db')
    

def planetmags():
    "Returns dictionary of planet magnitudes"
    return _PLANETS


def get_constellation_lines():
    "Returns a list of constellation lines"
    global _CONSTELLATION_LINES
    if not _CONSTELLATION_LINES:
        with open(_CONFIG['constellation_lines'], newline='') as f:
            reader = csv.reader(f)
            _CONSTELLATION_LINES = list(reader)
    return _CONSTELLATION_LINES


def get_redis():
    "Returns tuple of redis ip, port, auth"
    return (_CONFIG['redis_ip'], _CONFIG['redis_port'], _CONFIG['redis_auth'])

def get_astrodata_directory():
    "Returns the directory of support files"
    return _CONFIG['astrodata_directory']

def get_star_catalogs_directory():
    "Returns the directory of support files"
    return _CONFIG['star_catalogs']

def get_servedfiles_directory():
    "Returns the directory where served files are kept"
    return _CONFIG['servedfiles_directory']

def get_dbbackups_directory():
    "Returns the directory where database backup files are kept"
    return _CONFIG['dbbackups_directory']

def get_planetdb():
    "Returns the path to the database file which stores planet positions"
    return _CONFIG['planetdb']

def get_maindb():
    "Returns the path to the database file which stores slot sessions and usernames and passwords"
    return _CONFIG['maindb']

def observatory():
    "Returns the observatory longitude, latitude, elevation"
    return _CONFIG['longitude'], _CONFIG['latitude'], _CONFIG['elevation']

def telescope():
    "Returns the telescope name, as given by its indi driver"
    return _CONFIG['telescope_name']

def door():
    "Returns the door name, as given by its indi driver"
    return _CONFIG['door_name']




