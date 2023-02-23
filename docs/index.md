# Server build documentation


## Update the VPS

From the ovh kvm console, log in as ubuntu and type the following two commands to update the system:

sudo apt-get update

sudo apt-get upgrade

and reboot if the upgrade requests it


## From linux laptop, and any other PC you want, copy SSH keys

From laptop, desktop etc.,

ssh-copy-id ubuntu@<ip address of VPS>

This will ask for the ubuntu password

so now login to the VPS from your laptop

ssh ubuntu@<ip address of VPS>

## Load software

load the remscope software from the git repository:

git clone https://github.com/bernie-skipole/remscope.git

This should create the directory remscope, change into that directory

cd remscope

Gain root permissions with:

sudo bash

This may ask for your password

Then run a script to install software

source buildserver

When this is done, check a redis server is running with:

redis-cli ping PONG

You should get PONG output.

A nginx web server should be running, from your browser call the VPS ip address and you should get the default nginx page.

## Load python modules

Still in the remscope directory of the VPS, but not with root permissions, as the buildserver script should have dropped root, run a python program to install Python modules, this will create another directory, rsenv in the ubuntu home directory:

python3 loadpymodules.py

## Copy star database files

The directory ~/www will be the actual working directory running the application, wherease ~/remscope will remain a git repository.

Run the following script to create directory ~/www which is a copy of ~/remscope, but without the hidden git files, and it also downloads the star and planet databases.

source copytowww


## Met office data

The file ~/www/astrodata/metoffice.py need to be edited with the correct id and key for the met office, these values are not available in these scripts downloaded from github, since they are private.  Once inserted, run

python3 metoffice.py

which will create weather.json


## backups

The python script backup.py is normally run by a cron job, it creates a database backup file and saves the file to the backups directory. A backup has been created using default keys, but these are publicly available on the git repository.

~/www/astrodata/maindb/backup.py should be inspected, and a new encryption key should be created, and recorded, when the system is installed.

If a new encryption key is created, it should also be set into restore.py

To test backup.py, call:

python3 /home/ubuntu/www/astrodata/maindb/backup.py

and a backup file will be created in ~/www/astrodata/served/backups


## start services

cd ~/remscope

sudo bash

source installservices












