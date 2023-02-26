# REMSCOPE

This consists of a web application, generally installed on a Virtual Private Server (VPS), available on the internet.  It runs a robotic web service. At the observatory, a linux device, typically a raspberry py, runs indi software to interface with a telescope, and communicates by ssh tunnel to the VPS.

The rest of this document describes the VPS build.


## Server build documentation

This document describes how the user can run script files, which pull in and run the remscope software.

Assuming you have rented a Linux VPS server, connect to it over SSH, or via KVM console.

The following assumes the server is a debian/ubuntu based server, and the username of the logged in user is ubuntu, if the username is different, ensure the user where the build software will be installed has sudo capability, and the ssh call below should have the username set rather than ubuntu.  Three directories will be created in the users home directory; remscope, www and rsenv - so files or directories with these names should not exist, or there will be name conflicts as the directories are created.

So to log in, either use putty, or if coming from a Linux laptop/desktop:

**ssh ubuntu@ip-address**

Replace ip-address with the ip address of your VPS. You will be asked for the password. If this is the first time of connection you may get warnings.


## Update the VPS

Type the following two commands to update the VPS:

**sudo apt-get update**

**sudo apt-get upgrade**

You may get asked for your password to confirm sudo permissions. Reboot the server if the upgrade requests it.

**sudo reboot**


## Optional - copy SSH key

If you are using a Linux laptop to call the VPS, and you have an ssh key, you could install your key in the VPS. On your laptop you would type:

**ssh-copy-id ubuntu@ip-address**

This will ask for the password and will pass your key to the VPS. So now login to the VPS from your laptop:

**ssh ubuntu@ip-address**

and in future you will no longer need to put in your password.


## Load software

Having logged in to the VPS, check you are in the users home directory:

**cd ~**

Load the remscope code from the git repository by typing:

**git clone https://github.com/bernie-skipole/remscope.git**

This should create the directory remscope, and pulls in code from github. You can check the directory has been created using the ls command:

**ls**

A good deal of further software is required - some packages need root permissions to install. The remscope directory contains script files which do the installation, and the rest of this document describes how they are run. Change into the remscope directory, and list it to view the contents:

**cd remscope**

**ls**

The first script to run is buildserver, this requires root permission, which is obtained by typing:

**sudo bash**

This may ask for your password.

Then run the script buildserver to install software from repositories, the source command runs the script file as if each line of the script was being typed in:

**source buildserver**

This may take some time, you will see output printed as packages are installed. When this is done your normal prompt will be shown again.

Your VPS should now be running an NGINX web server and a redis server, which acts as a database for the remscope application. Check the redis server is running with:

**redis-cli ping PONG**

You should get PONG output.

From the browser of your laptop, call the VPS ip address and you should get the default NGINX page.


## Load python modules

Still in the remscope directory of the VPS, but no longer with root permissions, as the buildserver script should have dropped root, run the Python program loadpymodules.py which installs a load of Python astronomy modules.  This will automaticall create another directory rsenv in the ubuntu home directory, where the modules will be placed, and will display various messages as the modules are installed. It will take some time, so wait for the normal prompt which will appear when all is done. To run the program type:

**python3 loadpymodules.py**


## Copy star database files

The next script creates directory www which is the actual working directory running the application.

Still in the remscope directory, run the script copytowww to create directory www and which copies required files, and also downloads star and planet data. It will take some time, so again wait for the normal prompt which will appear when all is done.

**source copytowww**


## Met office data

The file ~/www/astrodata/metoffice.py needs to be edited with the client id and key for the met office, these values are not available in these scripts downloaded from github, since they are private.  If you do not have these keys, then miss this section out, it can be done later.

To get keys, register the application with the met office Global spot data service and get a client id, and client secret api keys. You will also  need the longitude and latitude where the weather data is to be calculated for. You should then edit metoffice.py:

**cd ~/www/astrodata**

**nano metoffice.py**

This opens an editor, insert the correct values, and save the result. The program metoffice.py will be automatically run daily to download a file weather.json, you can also run it manually to check that weather.json is created:

**python3 metoffice.py**


## backups

The python script ~/www/astrodata/maindb/backup.py is automatically run weekly, it creates an encrypted database backup file and saves the file to the backups directory.

To test backup.py, call:

**cd ~/www/astrodata/maindb**

**python3 backup.py**

and a backup file will be created in ~/www/astrodata/served/backups.

An encryption key will be created in ~/www/astrodata/maindb/keyfile the first time backup.py is run. A copy of the contents of this file should be kept elsewhere, as it must be available to decrypt and restore the backup if necessary. The keyfile can be listed with:

**less keyfile**

copy the contents with cut and paste, and use q to quit the less command.


## start services

The script file installservices in the remscope directory loads the system services which run the web application. These require root permission to install, so run the following:

**cd ~/remscope**

**sudo bash**

**source installservices**

At this point, calling the server ip address with your browser should show the remscope web pages.

You should immdiately change the admin password. Log in with user admin, password password, pin 1234 and, under the section Your Settings, change the password and pin.

Under web settings in the admin section you can change the home page title and image.


## create crontab

Call the script makecrontab which copies the cronentries file into crontab: 

**source makecrontab**

And check entries have been loaded by listing the crontab file:

**crontab -l**

If required, crontab can be further edited with:

**crontab -e**

The cron entries create re-occuring jobs which maintain the system, these are:

make_planets.py is run at 10:30 each day, which populates planet.db with planetary positions

IERS_A.py is run at 9:00 every Saturday, It downloads the IERS bulletin A for Astroplan earth location.

clientrequests.py is run at 10:15 each day, which requests dome door closure, in case it has been accidently left open. Note that the global variables DOOR_NAME and TELESCOPE_NAME should be edited with the names used by the indi driver for these devices. If this automatic function is not required (as the scope is being developed), remove the line from the cron job.

metoffice.py is run at 9:30 and 16:30 each day, and calls a met office api to obtain weather data which it sets into file weather.json.

clearguests.py clears expired guests from the database every mid day, and mid day + 1 hour, cron works on local time, so mid day, and mid day + 1 should get 12 utc between them.

backup.py gets a dump of the main database, 2:30 afternoon every saturday, compresses and encrypts it, and saves the file where it can be downloaded by admin users.


## Getting certificate from letsencrypt

Follow instructions from https://certbot.eff.org/lets-encrypt


## Upgrade during development

If changes are made to the software on the github site, and these are to be applied to the running system, the following can be done - however this will briefly stop the site working, so should be done in daylight hours.

**cd ~/remscope**

**sudo systemctl stop acremscope**

**sudo systemctl stop indidrivers**

**source upgradefromgit**

**sudo systemctl start indidrivers**

**sudo systemctl start acremscope**


## Restore user database from backup file

Only a system administrator can restore the database, it cannot be done from the web pages.  You should stop the service:

**sudo systemctl stop acremscope**

The backup file should be in directory ~/www/astrodata/served/backups, or if you have a backup file held externally, it should be placed there.

The restore program will not restore if a running database is in existence, check with:

**cd ~/www/astrodata/maindb**

**ls**

If the list of contents shows the file main.db, then remove it with:

**rm main.db**

Ensure this directory list also includes the file keyfile - this contains the encryption key to unlock the backup. If the backup was created with a different keyfile, then the correct keyfile has to replace this file - or the file edited to contain the correct encryption string.

Then restore the backup file by running restore.py with the path to the backup file, set backupfilename to the correct name:

**python3 restore.py ~/www/astrodata/served/backups/backupfilename**

and finally re-start the service

**sudo systemctl start acremscope**

