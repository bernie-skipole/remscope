import json, datetime

from urllib.request import Request, urlopen

from os.path import join, expanduser


# SET THE CORRECT LONGITUDE, LATITUDE AND MET OFFICE KEYS IN THE FUNCTION CALL
# AT THE END OF THIS FILE


def get_weather(weatherfile, longitude, latitude, met_client_id, met_client_secret):
    "Creates json file of weather data" 

    if (not met_client_id) or (not met_client_secret):
        return

    headers = {
        'X-IBM-Client-Id': met_client_id,
        'X-IBM-Client-Secret': met_client_secret,
        'accept': "application/json"
        }

    url = ('https://api-metoffice.apiconnect.ibmcloud.com/'
           'metoffice/production/v0/forecasts/point/hourly'
           '?excludeParameterMetadata=false&includeLocationName=false'
           f'&latitude={latitude}&longitude={longitude}')

    apiurl = Request(url, headers=headers)

    with urlopen(apiurl) as response:
       received_data = json.loads(response.read())

    # break down the received dictionary into component parts

    _features = received_data['features'] # list containing a dictionary
    _geometry = _features[0]['geometry']
    _properties = _features[0]['properties'] # dictionary with elements modelRunDate, requestPointDistance, timeSeries
    _timeSeries = _properties['timeSeries'] # list containing dictionaries, each dictionary is the data for one hour
    _parameters = received_data['parameters'] # list containing a dictionary
    parameter_dictionary = _parameters[0] # each element of the dictionary describes a parameter

    weather_dict = {}
    for data in _timeSeries:
        # each data dictionary contains parameter:value
        value_list = []
        for parameter,value in data.items():
            if parameter == 'time':
                key = value
                continue
            p_dict = parameter_dictionary[parameter]
            p_description = p_dict['description']
            p_label = p_dict['unit']['label']
            value_list.append([p_description, value, p_label])
        weather_dict[key] = value_list

    # weather_dict has keys equal to iso time strings
    # and values equal to a list of lists, each inner list being parameter [description, value, label]

    with open(weatherfile, 'w') as fp:
        json.dump(weather_dict, fp)


def weathertime(weatherfile, timestring):
    "Return the list of lists of weather parameters for a given hour"

    # this function can be used if required to print weather parameters for a given hour
    # timestring is needed in a format like 2021-06-13T12:00Z, for example
    # thistime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:00Z")
    # result = weathertime("weather.json", thistime)
    # print(result)

    with open(weatherfile, 'r') as fp:
        weather_dict = json.load(fp)
    if timestring not in weather_dict:
        return
    return weather_dict[timestring]


if __name__ == "__main__":

    # SET THE CORRECT LONGITUDE, LATITUDE AND MET OFFICE KEYS IN THIS FUNCTION CALL

    # Create weather.json file of weather data

    weatherfile = join(expanduser("~"), "www", "astrodata", "weather.json")

    get_weather(weatherfile=weatherfile,
                longitude=-2.1544,
                latitude=53.7111,
                met_client_id="",
                met_client_secret="")



