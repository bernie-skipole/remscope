

import random

from datetime import datetime

from indi_mr import tools

try:
    import redis
except:
    _REDIS_AVAILABLE = False
else:
    _REDIS_AVAILABLE = True


from skipole import FailPage, GoTo, ValidateError, ServerError

from . import cfg


def open_redis(redis_db=0):
    "Returns a connection to the redis database"

    if not _REDIS_AVAILABLE:
        raise FailPage(message = "redis module not loaded")

    rconn = None

    # redis server settings from cfg.py
    redis_ip, redis_port, redis_auth = cfg.get_redis()

    if not redis_ip:
        raise FailPage("Redis service not available")

    # create a connection
    try:
        rconn = redis.StrictRedis(host=redis_ip, port=redis_port, db=redis_db, password=redis_auth, socket_timeout=5)
    except:
        raise FailPage("Redis service not available")

    if rconn is None:
        raise FailPage("Redis service not available")

    return rconn


def get_control_user(prefix='', rconn=None):
    """Return user_id of the user who has current control of the telescope,
       or None if not found"""
    try:
        control_user_id = int(rconn.get(prefix+'control_user_id').decode('utf-8'))
    except:
        return
    return control_user_id


def set_control_user(user_id, prefix='', rconn=None):
    """Set the user who has current control of the telescope and resets chart parameters.
       Return True on success, False on failure"""
    if user_id is None:
        return False
    if rconn is None:
        return False
    try:
        rconn.set(prefix+'view', "100.0")
        rconn.set(prefix+'flip', '')
        rconn.set(prefix+'rot', "0.0")
        result = rconn.set(prefix+'control_user_id', user_id)
    except:
        return False
    if result:
        return True
    return False


def test_mode(user_id, prefix='', rconn=None):
    """Return True if this user has test mode, False otherwise"""
    if user_id is None:
        return False
    if rconn is None:
        return False
    try:
        test_user_id = int(rconn.get(prefix+'test_mode').decode('utf-8'))
    except:
        return False
    return bool(user_id == test_user_id)


def get_test_mode_user(prefix='', rconn=None):
    """Return user_id of test mode, or None if not found"""
    if rconn is None:
        return
    try:
        test_user_id = int(rconn.get(prefix+'test_mode').decode('utf-8'))
    except:
        return
    return test_user_id


def set_test_mode(user_id, prefix='', rconn=None):
    """Set this user with test mode.
       Return True on success, False on failure"""
    if user_id is None:
        return False
    if rconn is None:
        return False
    try:
        result = rconn.set(prefix+'test_mode', user_id, ex=3600, nx=True)  # expires after one hour, can only be set if it does not exist
    except:
        return False
    if result:
        return True
    return False


def delete_test_mode(prefix='', rconn=None):
    """Delete test mode.
       Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        rconn.delete(prefix+'test_mode')
    except:
        return False
    return True


def set_wanted_position(ra, dec, prefix='', rconn=None):
    """Sets the  wanted Telescope RA, DEC  - given as two floats in degrees
       Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        result_ra = rconn.set(prefix+'wanted_ra', str(ra))
        result_dec = rconn.set(prefix+'wanted_dec', str(dec))
    except Exception:
        return False
    if result_ra and result_dec:
        return True
    return False


def get_wanted_position(prefix='', rconn=None):
    """Return wanted Telescope RA, DEC as two floats in degrees
       On failure returns None"""
    if rconn is None:
        return
    try:
        wanted_ra = float(rconn.get(prefix+'wanted_ra').decode('utf-8'))
        wanted_dec = float(rconn.get(prefix+'wanted_dec').decode('utf-8'))
    except:
        return
    return wanted_ra, wanted_dec


def set_target_name(target_name, prefix='', rconn=None):
    """Sets the  wanted Telescope target_name
       Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        result = rconn.set(prefix+'target_name', target_name.lower())
    except Exception:
        return False
    if result:
        return True
    return False


def get_target_name(prefix='', rconn=None):
    """Return wanted Telescope named target.
       On failure, or no name returns empty string"""
    if rconn is None:
        return ''
    try:
        target_name = rconn.get(prefix+'target_name').decode('utf-8')
    except:
        return ''
    return target_name


def set_target_frame(target_frame, prefix='', rconn=None):
    """Sets the target_frame of the item currently being tracked
       Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        result = rconn.set(prefix+'target_frame', target_frame.lower())
    except Exception:
        return False
    if result:
        return True
    return False


def get_target_frame(prefix='', rconn=None):
    """Returns the target_frame of the item currently being tracked
       On failure, or no name returns empty string"""
    if rconn is None:
        return ''
    try:
        target_frame = rconn.get(prefix+'target_frame').decode('utf-8')
    except:
        return ''
    return target_frame


def del_target_name(prefix='', rconn=None):
    """Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        rconn.delete(prefix+'target_name')
    except:
        return False
    return True


def get_chart_parameters(prefix='', rconn=None):
    """Return view, flip and rotate values of the control chart"""
    if rconn is None:
        return (100.0, False, 0.0)
    try:
        view = rconn.get(prefix+'view').decode('utf-8')
        flip = rconn.get(prefix+'flip').decode('utf-8')
        rot = rconn.get(prefix+'rot').decode('utf-8')
    except:
        return (100.0, False, 0.0)
    return float(view), bool(flip), float(rot)


def set_chart_parameters(view, flip, rot, prefix='', rconn=None):
    """Set view, flip, rot
       Return True on success, False on failure"""
    if rconn is None:
        return False
    try:
        result_view = rconn.set(prefix+'view', str(view))
        if flip:
            result_flip = rconn.set(prefix+'flip', 'true')
        else:
            result_flip = rconn.set(prefix+'flip', '')
        result_rot = rconn.set(prefix+'rot', str(rot))
    except Exception:
        return False
    if result_view and result_flip and result_rot:
        return True
    return False


def get_chart_actual(prefix='', rconn=None):
    """Return True if the chart is showing actual view, False if target view"""
    if rconn is None:
        return False
    try:
        actual = rconn.get(prefix+'chart_actual').decode('utf-8')
    except:
        return False
    return bool(actual)


def set_chart_actual(actual, prefix='', rconn=None):
    """Set actual value
       Return True on success, False on failure, if rconn is None, it is created."""

    if rconn is None:
        return False

    try:
        if actual:
            result_actual = rconn.set(prefix+'chart_actual', 'true')
        else:
            result_actual = rconn.set(prefix+'chart_actual', '')
    except Exception:
        return False
    if result_actual:
        return True
    return False


def get_led(rconn, redisserver):
    """Return led status string."""

    if rconn is None:
        return 'UNKNOWN'
    try:
        #led_status = rconn.get('led').decode('utf-8')
        led = tools.elements_dict(rconn, redisserver, "LED ON", "LED", "Rempico01")
        # led should be a dictionary, key 'value' should be On or Off
        if not led:
            return "UNKNOWN"
        led_status = led.get("value", "UNKNOWN")
    except:
        return 'UNKNOWN'
    return led_status


def get_door_message(rconn, redisserver):
    """Return door status string."""
    # returns a door status message
    if rconn is None:
        return 'UNKNOWN'
    door_name = cfg.door()
    door_attribs = tools.attributes_dict(rconn, redisserver, "DOOR_STATE", door_name)
    if not door_attribs:
        return get_door(rconn, redisserver)
    if 'message' in door_attribs:
        message = door_attribs['message']
        if message:
            return message
    return get_door(rconn, redisserver)



def get_door(rconn, redisserver):
    """Return door status string."""
    # returns one of UNKNOWN, OPEN, CLOSED, OPENING, CLOSING
    if rconn is None:
        return 'UNKNOWN'
    door_name = cfg.door()
    try:
        door_status = tools.elements_dict(rconn, redisserver, "CLOSED", "DOOR_STATE", door_name)
        if door_status['value'] == "Ok":
            return "CLOSED"
        door_status = tools.elements_dict(rconn, redisserver, "OPEN", "DOOR_STATE", door_name)
        if door_status['value'] == "Ok":
            return "OPEN"
        door_status = tools.elements_dict(rconn, redisserver, "OPENING", "DOOR_STATE", door_name)
        if door_status['value'] == "Ok":
            return "OPENING"
        door_status = tools.elements_dict(rconn, redisserver, "CLOSING", "DOOR_STATE", door_name)
        if door_status['value'] == "Ok":
            return "CLOSING"
    except:
        return 'UNKNOWN'
    return 'UNKNOWN'


def get_temperatures(rconn, redisserver):
    """Return temperature log."""

    if rconn is None:
        raise FailPage("Unable to access redis temperature variable")
    # get data from redis
    try:
        elementlogs = tools.logs(rconn, redisserver, 48, 'elementattributes', "TEMPERATURE", "ATMOSPHERE", "Rempico01")
        if not elementlogs:
            return []
        dataset = [] # needs to be a list of lists of [day, time, temperature]
        for t,data in elementlogs:
            if ("formatted_number" not in data) or ("timestamp" not in data):
                continue
            number = float(data["formatted_number"]) - 273.15
            numberstring = "%.2f" % number
            daytime = data["timestamp"].split("T")
            dataset.append([daytime[0], daytime[1], numberstring])
    except:
        raise FailPage("Unable to access redis temperature variable")
    return dataset


def last_temperature(rconn, redisserver):
    """Return last date and temperature.

       String returned is of the form %Y-%m-%d %H:%M temperature, if unable to get
       the temperature, an empty string is returned"""

    if rconn is None:
        return ''
    # get data from redis
    try:
        element_att = tools.elements_dict(rconn, redisserver, "TEMPERATURE", "ATMOSPHERE", "Rempico01")
        # element_att should be a dictionary
        if not element_att:
            return ''
        temperature_value = element_att.get("formatted_number")
        if temperature_value is None:
            return ''
        # Convert from Kelvin to Centigrade
        temperature = float(temperature_value) - 273.15
        temperature_string = "%.2f" % temperature
        timestamp_value = element_att.get("timestamp")
        if timestamp_value is None:
            return ''
        temperature_date, temperature_time =  timestamp_value.split("T")
    except:
        return ''
    return f"{temperature_date} {temperature_time} {temperature_string}"


def system_error(rconn, redisserver):
    "Returns an error message if system or network error, otherwise returns an empty string"
    # get timestamp of the picoalive monitor, display alarm if greater than 20 seconds
    # tools.elements_dict returns a dictionary of element attributes for the given element, property and device
    monitor = tools.elements_dict(rconn, redisserver, 'PICOALIVE', 'MONITOR', 'Rempico01')
    try:
        # fromisoformat (available in python 3.7+) requires 3 digits of decimal, ie seconds as 20.500 not 20.5, so pad it with zeros
        timestamp = monitor['timestamp'].ljust(23, '0')
        timed = datetime.utcnow() - datetime.fromisoformat(timestamp)
        if timed.total_seconds() > 20:
            return "Network Error : Communications to observatory lost"
        elif monitor["value"] == "Alert":
            return "System Error : Pi to Pico connection failed"
    except:
        return "Network Error : Unable to read monitor timestamp"
    return ''


############################################################
#
# The following deals with cookies and user logged in status
#
############################################################


def logged_in(cookie_string, prefix='', rconn=None):
    """Check for a valid cookie, if logged in, return user_id
       If not, return None."""

    if rconn is None:
        return

    if (not cookie_string) or (cookie_string == "noaccess"):
        return

    cookiekey = prefix+cookie_string
    try:
        if not rconn.exists(cookiekey):
            return
        user_info = rconn.lrange(cookiekey, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number, added to input pin form and checked on submission
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        user_id = int(user_info[0].decode('utf-8'))
        # and update expire after two hours
        rconn.expire(cookiekey, 7200)
    except:
        return
    return user_id


def set_cookie(cookie_string, user_id, prefix='', rconn=None):
    """Return True on success, False on failure"""

    if rconn is None:
        return False

    if (not  user_id) or (not cookie_string):
        return False

    cookiekey = prefix+cookie_string
    # set value as a list of [user_id, random_number, pair number]
    try:
        if rconn.exists(cookiekey):
            # cookie already delete it
            rconn.delete(cookiekey)
            # and return False, as this should not happen
            return False
        # set the cookie into redis
        rconn.rpush(cookiekey, str(user_id), str(random.randint(10000000, 99999999)), str(random.randint(1,6)))
        rconn.expire(cookiekey, 7200)
    except:
        return False
    return True



def del_cookie(cookie_string, prefix='', rconn=None):
    """Return True on success, False on failure"""

    if rconn is None:
        return False

    if not cookie_string:
        return False
    cookiekey = prefix+cookie_string
    try:
        rconn.delete(cookiekey)
    except:
        return False
    return True


def set_rnd(cookie_string, prefix='', rconn=None):
    """Sets a random number against the cookie, return the random number on success,
       None on failure"""

    if rconn is None:
        return

    if not cookie_string:
        return
    cookiekey = prefix+cookie_string

    rnd = random.randint(10000000, 99999999)

    # set a random_number
    try:
        if not rconn.exists(cookiekey):
            return
        # set the random number into the database
        rconn.lset(cookiekey, 1, str(rnd))
    except:
        return
    return rnd


def get_rnd(cookie_string, prefix='', rconn=None):
    """Gets the saved random number from the cookie, return the random number on success,
       None on failure.
       Once called, it creates a new random number to store in the database,
       so the number returned is then lost from the database."""

    if rconn is None:
        return

    if not cookie_string:
        return
    cookiekey = prefix+cookie_string

    # get and set a random_number
    try:
        if not rconn.exists(cookiekey):
            return
        user_info = rconn.lrange(cookiekey, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        rnd = int(user_info[1].decode('utf-8'))
        # after obtaining rnd, insert a new one
        newrnd = random.randint(10000000, 99999999)
        rconn.lset(cookiekey, 1, str(newrnd))
    except:
        return
    return rnd


def get_pair(cookie_string, prefix='', rconn=None):
    """Gets the saved pair random number from the cookie, return it on success,
       None on failure."""

    if rconn is None:
        return

    if not cookie_string:
        return
    cookiekey = prefix+cookie_string

    # get the pair number
    try:
        if not rconn.exists(cookiekey):
            return
        user_info = rconn.lrange(cookiekey, 0, -1)
        # user_info is a list of binary values
        # user_info[0] is user id
        # user_info[1] is a random number
        # user_info[2] is a random number between 1 and 6, sets which pair of PIN numbers to request
        pair = int(user_info[2].decode('utf-8'))
    except:
        return
    return pair


##################################################
#
# admin user authenticated state,
#
##################################################

def is_authenticated(cookie_string, prefix='', rconn=None):
    """Check for a valid cookie, if exists, return True
       If not, return False."""

    if rconn is None:
        return False

    if (not cookie_string) or (cookie_string == "noaccess"):
        return False

    cookiekey = prefix+cookie_string

    try:
        if rconn.exists(cookiekey):
            # key exists, and update expire after ten minutes
            rconn.expire(cookiekey, 600)
        else:
            return False
    except:
        return False
    return True


def set_authenticated(cookie_string, user_id, prefix='', rconn=None):
    """Sets cookie into redis, with user_id as value
       If successfull return True, if not return False."""

    if rconn is None:
        return False

    if (not  user_id) or (not cookie_string):
        return False

    cookiekey = prefix+cookie_string

    try:
        if rconn.exists(cookiekey):
            # already authenticated, delete it
            rconn.delete(cookiekey)
            # and return False, as this should not happen
            return False
        # set the cookie into the database
        rconn.rpush(cookiekey, str(user_id))
        rconn.expire(cookiekey, 600)
    except:
        return False
    return True


##################################################
#
# count of pin failures for a user,
#
##################################################



def increment_try(user_id, prefix='', rconn=None):
    """creates an incrementing count against the user_id
       which expires after one hour"""

    if rconn is None:
        return

    str_user_id = prefix+str(user_id)

    # increment and reset expire
    tries = rconn.incr(str_user_id)
    rconn.expire(str_user_id, 3600)
    return int(tries)


def get_tries(user_id, prefix='', rconn=None):
    """Gets the count against the user_id"""

    if rconn is None:
        return

    str_user_id = prefix+str(user_id)

    if not rconn.exists(str_user_id):
        # No count, equivalent to 0
        return 0

    tries = rconn.get(str_user_id)
    return int(tries)


def clear_tries(user_id, prefix='', rconn=None):
    """Clears the count to zero against the user_id"""

    if rconn is None:
        return

    str_user_id = prefix+str(user_id)

    rconn.set(str_user_id, 0)
    return



################################################
#
# Two timed random numbers
#
################################################

def two_min_numbers(rndset, prefix='', rconn=None):
    """returns two random numbers
       one valid for the current two minute time slot, one valid for the previous
       two minute time slot.  Four sets of such random numbers are available
       specified by argument rndset which should be 0 to 3"""

    # limit rndset to 0 to 3
    if rndset not in (0,1,2,3):
        return None, None

    # call timed_random_numbers with timeslot of two minutes in seconds
    return timed_random_numbers(rndset, 120, prefix, rconn)



def timed_random_numbers(rndset, timeslot, prefix, rconn=None):
    """returns two random numbers
       one valid for the current time slot, one valid for the previous
       time slot.  Multiple sets of such random numbers are available
       specified by argument rndset which should be an integer."""

    if rconn is None:
        return None, None

    key = prefix + "rndset_" + str(rndset)
    now = rconn.time()[0]     # time in seconds

    try:

        if not rconn.exists(key):
            rnd1 = random.randint(10000000, 99999999)
            rnd2 = random.randint(10000000, 99999999)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2

        start, rnd1, rnd2 = rconn.lrange(key, 0, -1)
        start = int(start.decode('utf-8'))
        rnd1 = int(rnd1.decode('utf-8'))
        rnd2 = int(rnd2.decode('utf-8'))

        if now < start + timeslot:
            # now is within timeslot of start time, so current random numbers are valid
            return rnd1, rnd2

        elif now < start + timeslot + timeslot:
            # now is within twice the timeslot of start time, so rnd1 has expired. but rnd2 is valid
            # set rnd2 equal to rnd1 and create new rnd1
            rnd2 = rnd1
            rnd1 = random.randint(10000000, 99999999)
            rconn.delete(key)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2

        else:
            # now is greater than twice timeslot after start time, ro rnd1 and rnd2 are invalid, create new ones
            rnd1 = random.randint(10000000, 99999999)
            rnd2 = random.randint(10000000, 99999999)
            rconn.delete(key)
            rconn.rpush(key, str(now), str(rnd1), str(rnd2))
            return rnd1, rnd2
    except:
        pass

    return None, None


######################################################################
#
# temporary session values, lifetime 7200 (two hours)
#
# each key contains a list of strings, note the string '_'
# should not be used as it has a special meaning
#
######################################################################



def set_session_value(key_string, value_list, prefix='', rconn=None):
    """Return True on success, False on failure

       Given a key_string, saves a value_list
       with an expirey time of 7200 seconds (2 hours)
       The items are saved as strings.
       empty values are stored as '_'"""

    if not key_string:
        return False
    if not value_list:
        return False
    if rconn is None:
        return False

    keystring = prefix+key_string

    # dbsize() returns the number of keys in the database
    numberofkeys = rconn.dbsize()
    # If the database is getting bigger, reduce the expire time of
    # these session keys to help reduce it
    if numberofkeys > 2000:
        return False
    elif numberofkeys > 1500:
        exptime = 900  # 15 minutes
    elif numberofkeys > 1000:
        exptime = 1800  # 30 minutes
    elif numberofkeys > 500:
        exptime = 3600  # one hour
    else:
        exptime = 7200  # two hours

    # Create a 'values' list, with '' replaced by '_'
    values = []
    for val in value_list:
        str_val = str(val)
        if not str_val:
            str_val = '_'
        values.append(str_val)

    try:
        if rconn.exists(key_string):
            # key_string already exists, delete it
            rconn.delete(key_string)
        # set the key and list of values into the database
        rconn.rpush(key_string, *values)
        rconn.expire(key_string, exptime)
    except:
        return False
    return True



def get_session_value(key_string, prefix='', rconn=None):
    """If key_string is not found, return None"""

    if not key_string:
        return
    if rconn is None:
        return

    keystring = prefix+key_string

    if not rconn.exists(key_string):
        # no value exists
        return

    binvalues = rconn.lrange(key_string, 0, -1)
    # binvalues is a list of binary values
    values = []
    for bval in binvalues:
        val = bval.decode('utf-8')
        if val == '_':
            str_val = ''
        else:
            str_val = val
        values.append(str_val)

    return values


######################### log information to redis,

def log_info(messagetime=None, topic = '', message='', prefix='', rconn=None):
    """Log the given message to the redis connection rconn, return True on success, False on failure.
       messagetime is a datetime object or not given, if not given a current timestamp will be created
       topic is optional, if given the resultant log will be topic : message"""
    if not message:
        return False
    if rconn is None:
        return False
    if messagetime is None:
        messagetime = datetime.utcnow()
    if topic:
        topicmessage = " " + topic + " : " + message
    else:
        topicmessage = " " + message
    try:
        # create a log entry to set in the redis server
        fullmessage = messagetime.strftime("%Y-%m-%d %H:%M:%S") + topicmessage
        rconn.rpush(prefix+"log_info", fullmessage)
        # and limit number of messages to 50
        rconn.ltrim(prefix+"log_info", -50, -1)
    except:
        return False
    return True


def get_log_info(prefix='', rconn=None):
    """Return info log as a list of log strings, newest first. On failure, returns empty list"""
    if rconn is None:
        return []
    # get data from redis
    try:
        logset = rconn.lrange(prefix+"log_info", 0, -1)
    except:
        return []
    if logset:
        loglines = [ item.decode('utf-8') for item in logset ]
    else:
        return []
    loglines.reverse()
    return loglines







