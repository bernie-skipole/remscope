##################################
#
# These functions populate the logged in control pages
#
##################################

from datetime import datetime, timedelta
from collections import namedtuple

import astropy.units as u
from astropy.coordinates import SkyCoord, EarthLocation, AltAz, name_resolve, solar_system_ephemeris, get_body, Angle, PrecessedGeocentric
from astropy.time import Time
from astroquery.mpc import MPC
from astroquery.exceptions import InvalidQueryError

from skipole import FailPage, GoTo, ValidateError, ServerError

from .. import sun, stars, database_ops, redis_ops, cfg

from indi_mr import tools

from .sessions import doorsession
from .. import redis_ops

Position = namedtuple('Position', ['ra', 'dec'])

#### may have to set a better 'parking position'

_PARKED = (0.0, 180.0)  # altitude, azimuth


def telescopegetproperties(skicall):
    "Sends a getproperties command for the telescope"
    # get telescope name
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    tools.getProperties(rconn, redisserver, device=telescope_name)



def get_parked_radec():
    "Returns Position object of the parked position"
    # now work out ra dec
    alt,az = _PARKED
    solar_system_ephemeris.set('jpl')
    longitude, latitude, elevation = cfg.observatory()
    astro_centre = EarthLocation.from_geodetic(longitude, latitude, elevation)
    altazcoord = SkyCoord(alt=alt*u.deg, az=az*u.deg, obstime = Time(datetime.utcnow(), format='datetime', scale='utc'), location = astro_centre, frame = 'altaz')
    # transform to ra, dec
    sc = altazcoord.transform_to('icrs')
    return Position(sc.ra.degree, sc.dec.degree)


def create_index(skicall):
    "Fills in the remscope index page, also used to refresh the page by JSON"

    # door is one of UNKNOWN, OPEN, CLOSED, OPENING, CLOSING
    door = redis_ops.get_door(skicall.proj_data.get("rconn"), skicall.proj_data.get("redisserver"))
    skicall.page_data['door_status', 'para_text'] = "Door : " + door
    if door == 'CLOSED':
        skicall.page_data['door', 'button_text'] = 'Open Door'
        skicall.page_data['door', 'action'] = 'open'
    elif door == 'OPEN':
        skicall.page_data['door', 'button_text'] = 'Close Door'
        skicall.page_data['door', 'action'] = 'close'
    else:
        skicall.page_data['door', 'button_text'] = 'Waiting'
        skicall.page_data['door', 'action'] = 'noaction'

    skicall.page_data['utc', 'para_text'] = datetime.utcnow().strftime("UTC Time : %H:%M")

    user_id = skicall.call_data['user_id']

    booked = database_ops.get_users_next_session(datetime.utcnow(), user_id)

    # does this user own the current session
    if user_id == skicall.call_data["booked_user_id"]:
        # the current slot has been booked by the current logged in user,
        skicall.page_data['booked', 'para_text'] = "Your session is live. You now have control."
    elif booked:
        skicall.page_data['booked', 'para_text'] = "Your next booked session starts at UTC : " + booked.strftime("%Y-%m-%d %H:%M")
    else:
        skicall.page_data['booked', 'para_text'] = "You do not have any sessions booked."


    if skicall.call_data["test_mode"]:
        skicall.page_data['booked', 'para_text'] = "You are operating in Test Mode."
        skicall.page_data['indiclient', 'hide'] = False
        skicall.page_data['test_warning', 'para_text'] = """WARNING: You are operating in Test Mode - Telescope commands will be sent regardless of the door status, or daylight situation. This could be damaging, please ensure you are in control of the test environment.
INDI client - this is a general purpose instrument control panel, which gives enhanced control of connected devices.
Note: A time slot booked by a user will override Test Mode, to avoid this you should operate within time slots which you have previously disabled."""
    elif skicall.call_data["role"] == 'ADMIN':
        skicall.page_data['test_warning', 'para_text'] = """The robotic telescope can be controlled by members during their valid booked session, or by Administrators who have enabled 'Test' mode.
Test Mode can be set by following the 'Admin' link on the left navigation panel.
Only one Admin user can enable Test Mode at a time.
Note: A time slot booked by a user will override Test Mode, to avoid this you should operate within time slots which you have previously disabled."""
    else:
        skicall.page_data['test_warning', 'para_text'] = ""


@doorsession
def door_control(skicall):
    "A door control is requested, sends command and fills in the template page"

    call_data = skicall.call_data
    page_data = skicall.page_data

    if ('door', 'action') not in call_data:
        return

    page_data['utc', 'para_text'] = datetime.utcnow().strftime("UTC Time : %H:%M")

    door_name = cfg.door()

    # check current state of the door to ensure action is valid
    door = redis_ops.get_door(skicall.proj_data.get("rconn"), skicall.proj_data.get("redisserver"))

    if (door == 'CLOSED') and (call_data['door', 'action'] == 'open'):
        # open the door
        tools.newswitchvector(skicall.proj_data.get("rconn"), skicall.proj_data.get("redisserver"),
                          "DOME_SHUTTER", door_name, {"SHUTTER_OPEN":"On", "SHUTTER_CLOSE":"Off"})
        # connect the telescope
        telescope_connection(skicall, True)
        page_data['door_status', 'para_text'] = "An Open door command has been sent."
    elif (door == 'OPEN') and (call_data['door', 'action'] == 'close'):
        # close the door
        tools.newswitchvector(skicall.proj_data.get("rconn"), skicall.proj_data.get("redisserver"),
                          "DOME_SHUTTER", door_name, {"SHUTTER_OPEN":"Off", "SHUTTER_CLOSE":"On"})
        # disconnect the telescope
        telescope_connection(skicall, False)
        page_data['door_status', 'para_text'] = "A Close door command has been sent."

    # so if door,action is noaction, or door is either OPENING or CLOSING, no tools command is sent

    page_data['door', 'button_text'] = 'Waiting'
    skicall.page_data['door', 'action'] = 'noaction'

    if skicall.call_data["test_mode"]:
        skicall.page_data['booked', 'para_text'] = "You are operating in Test Mode."
        skicall.page_data['indiclient', 'hide'] = False
        skicall.page_data['test_warning', 'para_text'] = """WARNING: You are operating in Test Mode - Telescope commands will be sent regardless of the door status, or daylight situation. This could be damaging, please ensure you are in control of the test environment.
INDI client - this is a general purpose instrument control panel, which gives enhanced control of connected devices.
Note: A time slot booked by a user will override Test Mode, to avoid this you should operate within time slots which you have previously disabled."""
    else:
        skicall.page_data['test_warning', 'para_text'] = ""


def is_telescope_connected(skicall):
    "Returns True if the telescope is connected, False otherwise"
    # get telescope name
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return False
    # so the telescope is a known device, does it have a CONNECTION property
    properties_list = tools.properties(rconn, redisserver, telescope_name)
    if "CONNECTION" not in properties_list:
        return False
    attribs = tools.elements_dict(rconn, redisserver, "CONNECT", "CONNECTION" , telescope_name)
    if attribs['value'] == "On":
        return True
    return False


def telescope_connection(skicall, connect):
    """This sends a connect or disconnect to telescope command. connect should be True to CONNECT, False to DISCONNECT"""
    # get telescope name
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return
    # so the telescope is a known device, does it have a CONNECTION property
    properties_list = tools.properties(rconn, redisserver, telescope_name)
    if "CONNECTION" not in properties_list:
        return
    # and connect/disconnect
    if connect:
        tools.newswitchvector(rconn, redisserver, "CONNECTION" , telescope_name, {"CONNECT":"On", "DISCONNECT":"Off"})
    else:
        tools.newswitchvector(rconn, redisserver, "CONNECTION" , telescope_name, {"CONNECT":"Off", "DISCONNECT":"On"})


def get_actual_position(skicall):
    """Gets actual Telescope position,
       return (True, Position, (alt,az)) if known, (False, Position (alt,az))
       if unknown"""

    # get telescope name
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return False, get_parked_radec(), _PARKED

    properties_list = tools.properties(rconn, redisserver, telescope_name)

    ra_act = None
    dec_act = None
    alt_act = None
    az_act = None
    targettime = None


    if 'EQUATORIAL_COORD' in properties_list:
        # get ra_act and dec_act

        # tools.elements_dict returns a dictionary of element attributes for the given element, property and device
        ra_dict = tools.elements_dict(rconn, redisserver, 'RA', 'EQUATORIAL_COORD', telescope_name)
        ra_act = ra_dict['float_number'] * 360.0/24.0
        dec_dict = tools.elements_dict(rconn, redisserver, 'DEC', 'EQUATORIAL_COORD', telescope_name)
        dec_act = dec_dict['float_number']
        targettime = Time(ra_dict['timestamp'], format='isot', scale='utc')

    if 'HORIZONTAL_COORD' in properties_list:
        # get alt_act, az_act

        # tools.elements_dict returns a dictionary of element attributes for the given element, property and device
        alt_dict = tools.elements_dict(rconn, redisserver, 'ALT', 'HORIZONTAL_COORD', telescope_name)
        alt_act = alt_dict['float_number']
        az_dict = tools.elements_dict(rconn, redisserver, 'AZ', 'HORIZONTAL_COORD', telescope_name)
        az_act = az_dict['float_number']
        targettime = Time(alt_dict['timestamp'], format='isot', scale='utc')

    if ('EQUATORIAL_COORD' in properties_list) and ('HORIZONTAL_COORD' in properties_list):
        # all properties have been found
        return True, Position(ra_act, dec_act), (alt_act, az_act)

    # one or both are missing so need to be able to calculate properties
    solar_system_ephemeris.set('jpl')
    longitude, latitude, elevation = cfg.observatory()
    astro_centre = EarthLocation.from_geodetic(longitude, latitude, elevation)

    if 'EQUATORIAL_COORD' in properties_list:
        # 'HORIZONTAL_COORD' is missing so calculate them from equatorial coords
        target = SkyCoord(ra_act*u.deg, dec_act*u.deg, frame='icrs')
        target_altaz = target.transform_to(AltAz(obstime = targettime, location = astro_centre))
        return True, Position(ra_act, dec_act), (target_altaz.alt.degree, target_altaz.az.degree)

    if 'HORIZONTAL_COORD' in properties_list:
        # 'EQUATORIAL_COORD' is missing so calculate them from horizontal coords
        target = SkyCoord(alt=alt_act*u.deg, az=az_act*u.deg, obstime = targettime, location = astro_centre, frame = 'altaz')
        # transform to ra, dec
        target_eq = target.transform_to('icrs')
        return True, Position(target_eq.ra.degree, target_eq.dec.degree), (alt_act, az_act)

    # so neither EQUATORIAL_COORD or HORIZONTAL_COORD are in the properties list

    if 'EQUATORIAL_EOD_COORD' not in properties_list:
        # no coords are available
        return False, get_parked_radec(), _PARKED

    # must calculate ra,dec, alt and az from EQUATORIAL_EOD_COORD

    # tools.elements_dict returns a dictionary of element attributes for the given element, property and device
    ra_dict = tools.elements_dict(rconn, redisserver, 'RA', 'EQUATORIAL_EOD_COORD', telescope_name)
    ra = ra_dict['float_number'] * 360.0/24.0
    dec_dict = tools.elements_dict(rconn, redisserver, 'DEC', 'EQUATORIAL_EOD_COORD', telescope_name)
    dec = dec_dict['float_number']
    targettime = Time(ra_dict['timestamp'], format='isot', scale='utc')

    target_frame = redis_ops.get_target_frame(skicall.proj_data.get("rconn_0"), skicall.proj_data.get("rconn"))
    if target_frame == 'icrs':
        # undo the precession calculation to get icrs back
        target = SkyCoord(ra*u.deg, dec*u.deg, obstime = targettime, equinox=targettime, frame='precessedgeocentric')
        target_eq = target.transform_to(frame ='icrs')
    elif target_frame == 'gcrs':
        # this is used for planets and minor planets
        target = SkyCoord(ra*u.deg, dec*u.deg, obstime = targettime, equinox=targettime, frame='precessedgeocentric')
        target_eq = target.transform_to(frame ='gcrs')
    else:
        return False, get_parked_radec(), _PARKED

    target_altaz = target.transform_to(AltAz(obstime = targettime, location = astro_centre))

    return True, Position(target_eq.ra.degree, target_eq.dec.degree), (target_altaz.alt.degree, target_altaz.az.degree)


def set_target(skicall, target_ra, target_dec, target_name):
    "Set the target. Return target_altaz, target_pg, or None on failure"

    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return

    properties_list = tools.properties(rconn, redisserver, telescope_name)


    solar_system_ephemeris.set('jpl')
    # longitude, latitude, elevation of the astronomy centre
    longitude, latitude, elevation = cfg.observatory()
    astro_centre = EarthLocation.from_geodetic(longitude, latitude, elevation)
    tstamp = Time(datetime.utcnow(), format='datetime', scale='utc')

    try:
        if target_name:
            target, target_altaz = stars.get_named_object(target_name, tstamp)
    except:
        target_name = ''

    if not target_name:
        # target name not given, so fixed ra and dec values, find alt az
        target = SkyCoord(target_ra*u.deg, target_dec*u.deg, frame='icrs')
        target_altaz = target.transform_to(AltAz(obstime=tstamp, location=astro_centre))

    if target.frame.name == 'icrs':
        target_pg = target.transform_to(PrecessedGeocentric(obstime=tstamp, equinox=tstamp))
    else:
        # frame is gcrs
        target_pg = target.transform_to(PrecessedGeocentric(obstime=tstamp, equinox=tstamp))

    # record the original frame used in redis
    redis_ops.set_target_frame(target.frame.name, skicall.proj_data.get("rconn_0"), skicall.proj_data.get("rconn"))

    if 'HORIZONTAL_COORD' in properties_list:
        result = tools.newnumbervector(rconn, redisserver, 'HORIZONTAL_COORD', telescope_name, {'ALT':str(target_altaz.alt.degree),
                                                                                                 'AZ':str(target_altaz.az.degree)})
        if result is None:
            return

    elif 'EQUATORIAL_EOD_COORD' in properties_list:
        result = tools.newnumbervector(rconn, redisserver, 'EQUATORIAL_EOD_COORD', telescope_name, {'RA':str(target_pg.ra.hour),
                                                                                                    'DEC':str(target_pg.dec.degree)})
        if result is None:
            return
    else:
        return

    return target_altaz, target_pg


def altaz_goto(skicall, altitude, azimuth):
    """Moves telescope to given altitude and azimuth, returns True if command sent
       False otherwise"""
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return False
    # so the telescope is a known device, does it have a CONNECTION property
    properties_list = tools.properties(rconn, redisserver, telescope_name)
    if "CONNECTION" not in properties_list:
        return False
    attribs = tools.elements_dict(rconn, redisserver, "CONNECT", "CONNECTION" , telescope_name)
    if attribs['value'] == "Off":
        return False

    if 'ON_COORD_SET' in properties_list:
        result = tools.newswitchvector(rconn, redisserver, 'ON_COORD_SET', telescope_name, {'SLEW':'On',
                                                                                            'TRACK':'Off',
                                                                                            'SYNC':'Off'})

    if 'HORIZONTAL_COORD' in properties_list:
        result = tools.newnumbervector(rconn, redisserver, 'HORIZONTAL_COORD', telescope_name, {'ALT':str(altitude),
                                                                                                 'AZ':str(azimuth)})
        if result is None:
            return False
        else:
            return True

    # longitude, latitude, elevation of the astronomy centre
    longitude, latitude, elevation = cfg.observatory()
    astro_centre = EarthLocation.from_geodetic(longitude, latitude, elevation)
    targettime = Time(datetime.utcnow(), format='datetime', scale='utc')

    target = SkyCoord(alt=altitude*u.deg, az=azimuth*u.deg, obstime = targettime, location = astro_centre, frame = 'altaz')

    if 'EQUATORIAL_EOD_COORD' in properties_list:
        # transform to ra, dec
        target_pg = target.transform_to(PrecessedGeocentric(obstime=targettime, equinox=targettime))
        result = tools.newnumbervector(rconn, redisserver, 'EQUATORIAL_EOD_COORD', telescope_name, {'RA':str(target_pg.ra.hour),
                                                                                                    'DEC':str(target_pg.dec.degree)})
        if result is None:
            return False
        else:
            return True
    return False


def set_track_state(skicall, state):
    "Turn tracking on or off, set state True for On, False for off" 
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    if state:
        tools.newswitchvector(rconn, redisserver, 'TELESCOPE_TRACK_STATE', telescope_name, {'TRACK_ON':'On',
                                                                                            'TRACK_OFF':'Off'})
    else:
        tools.newswitchvector(rconn, redisserver, 'TELESCOPE_TRACK_STATE', telescope_name, {'TRACK_ON':'Off',
                                                                                            'TRACK_OFF':'On'})


def get_track_state(skicall):
    "Returns On, Off or UKNOWN"
    telescope_name = cfg.telescope()
    rconn = skicall.proj_data.get("rconn")
    redisserver = skicall.proj_data.get("redisserver")
    device_list = tools.devices(rconn, redisserver)
    if telescope_name not in device_list:
        return "UNKNOWN"
    # so the telescope is a known device, does it have a TELESCOPE_TRACK_STATE property
    properties_list = tools.properties(rconn, redisserver, telescope_name)
    if "TELESCOPE_TRACK_STATE" not in properties_list:
        return "UNKNOWN"
    attribs = tools.elements_dict(rconn, redisserver, "TRACK_ON", "TELESCOPE_TRACK_STATE" , telescope_name)
    if attribs['value'] == "On":
        return "On"
    else:
        return "Off"



