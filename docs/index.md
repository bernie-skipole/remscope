# REMSCOPE

This consists of a web application, generally installed on a Virtual Private Server (VPS), available on the internet.  It runs a robotic web service. At the observatory, a linux device, typically a raspberry py, runs indi software to interface with a telescope, and communicates by ssh tunnel to the VPS.

The rest of this document describes the VPS build.


## Server build documentation

Assuming you have rented a Linux VPS server, connect to it over SSH, or via KVM console.

The following assumes the server is an Ubuntu server, and the username of the logged in user is ubuntu, if the username is different several of the build scripts described here may not work - so you will have to create a user called ubuntu with sudo capability.

So to log in, either use putty, or if coming from a Linux laptop/desktop:

ssh ubuntu@ip-address

and you will be asked for the password. If this is the first time you may get warnings.


## Update the VPS

Type the following two commands to update the VPS:

sudo apt-get update

sudo apt-get upgrade

and reboot if the upgrade requests it


## Optional - copy SSH key

If you are using a Linux laptop to call the VPS, and you have an ssh key, you could install your key in the VPS. From your laptop you would type:

ssh-copy-id ubuntu@ip-address

This will ask for the password and will pass your key to the VPS. So now login to the VPS from your laptop:

ssh ubuntu@ip-address

and in future you will no longer need to put in your password.


## Load software

Having logged in to the VPS as user ubuntu, load the remscope code from the git repository by typing:

git clone https://github.com/bernie-skipole/remscope.git

This should create the directory remscope, and pulls in code from github. You can check the directory has been created using the ls command:

ls

A good deal of further software is required - some packages need root permissions to install. The remscope directory contains script files which do the installation, and the rest of this document describes how they are run. Change into the remscope directory, and list it to view the contents:

cd remscope

ls

The first script to run is buildserver, this requires root permission, which is obtained by typing:

sudo bash

This may ask for your password.

Then run the script buildserver to install software from the ubuntu repositories, the source command runs the script file as if each line of the script was being typed in:

source buildserver

This may take some time, you will see output printed as packages are installed. When this is done your normal prompt will be shown again.

Your VPS should now be running an NGINX web server and a redis server, which acts as a database for the remscope application. Check the redis server is running with:

redis-cli ping PONG

You should get PONG output.

From the browser of your laptop, call the VPS ip address and you should get the default NGINX page.

## Load python modules

Still in the remscope directory of the VPS, but no longer with root permissions, as the buildserver script should have dropped root, run the Python program loadpymodules.py which installs a load of Python astronomy modules.  This will automaticall create another directory rsenv in the ubuntu home directory, where the modules will be placed, and will display various messages as the modules are installed. Wait for the normal prompt before continuing. To run the program type:

python3 loadpymodules.py


## Copy star database files

A new directory www will be created which is the actual working directory running the application.

Still in the remscope directory, run the script copytowww to create directory www and which copies required files, and also downloads star and planet data. It will take some time, so again wait for the normal prompt which will appear when all is done.

source copytowww


## Met office data

The file www/astrodata/metoffice.py need to be edited with the client id and key for the met office, these values are not available in these scripts downloaded from github, since they are private.  If you do not have these keys, then miss this section out, it can be done later.

To get keys, register the application with the met office Global spot data service and get a client id, and client secret api keys. You will also  need the longitude and latitude where the weather data is to be calculated for: 

cd ~/www/astrodata

nano metoffice.py

This opens an editor, insert the correct values, and save the result. The program metoffice.py will be automatically run daily to download a file weather.json, you can also run it manually to check that weather.json is created:

python3 metoffice.py


## backups

The python script backup.py is automatically run weekly, it creates a database backup file and saves the file to the backups directory. A backup has been created using default keys, but these are publicly available on the git repository.

The file www/astrodata/maindb/backup.py should be inspected, and a new encryption key should be created, and recorded. If a new encryption key is created, it should also be set into restore.py

To test backup.py, call:

cd ~/www/astrodata/maindb

python3 backup.py

and a backup file will be created in ~/www/astrodata/served/backups


## start services

The script file installservices in the remscope directory loads the system services which run the web application. These require root permission to install, so run the following:

cd ~/remscope

sudo bash

source installservices

At this point, calling the server with you browser should show the remscope web pages.

You should immdiately change the admin password. Log in with user admin, password password, pin 1234 and, under the section Your Settings, change the password and pin.

Under web settings in the admin section you can change the home page title and image.


## create crontab

Call the script makecrontab which copies the cronentries file into crontab: 

source makecrontab

And to see if these entries have been loaded by listing the crontab file:

crontab -l

If required, crontab can be further edited with:

crontab -e

The cron entries create re-occuring jobs which maintain the system, these are:

make_planets.py is run at 10:30 each day, which populates planet.db with planetary positions

IERS_A.py is run at 9:00 every Saturday, It downloads the IERS bulletin A for Astroplan earth location.

clientrequests.py is run at 10:15 each day, which requests dome door closure, in case it has been accidently left open. Note that the global variables DOOR_NAME and TELESCOPE_NAME should be edited with the names used by the indi driver for these devices. If this automatic function is not required (as the scope is being developed), remove the line from the cron job.

metoffice.py is run at 9:30 and 16:30 each day, and calls a met office api to obtain weather data which it sets into file weather.json.

clearguests.py clears expired guests from the database every mid day, and mid day + 1, cron works on local time, so mid day, and mid day + 1 should get 12 utc between them.

backup.py gets a dump of the main sqlite database, 2:30 afternoon every saturday, compresses and encrypts it, and saves the file where it can be downloaded by admin users.




