# stores indi data to redis

from os.path import join, expanduser

from indi_mr import mqtt_server, redis_server

from indi_mr import mqtttoredis
# from indi_mr import driverstoredis

# define the hosts/ports where servers are listenning, these functions return named tuples.

mqtt_host = mqtt_server(host='localhost', port=1883)
redis_host = redis_server(host='localhost', port=6379)

blobfolder = join(expanduser("~"), "remscope", "astrodata", "served")

# blocking call which runs the service, communicating between the drivers and redis
# driverstoredis(["indi_simulator_telescope", "indi_simulator_ccd"], redis_host, blob_folder=blobfolder)

# blocking call which runs the service, communicating between mqtt and redis
mqtttoredis('indi_remscope', mqtt_host, redis_host, blob_folder=blobfolder)

