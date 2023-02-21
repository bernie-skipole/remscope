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

so now login tot he VPS from your laptop

ssh ubuntu@<ip address of VPS>

## Load software

load the remscope software from the git repository:

git clone git@github.com:bernie-skipole/remscope.git

This should create the directory remscope, change into that directory

cd remscope

Gain root permissions with:

sudo bash

This may ask for your password

Then run a script to install software

source buildserver

When this is done, run a python program to install Python modules

python3 loadpymodules.py








