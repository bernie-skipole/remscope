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

so now the following works from laptop

ssh <ip address of VPS>

## Remove password login and root login via ssh

On the VPS gain root permissions with the following:

sudo bash

Then edit the file /etc/ssh/sshd_config using the nano text editor:

nano /etc/ssh/sshd_config

Set the line:

PasswordAuthentication yes

to

PasswordAuthentication no

Set the line:

PermitRootLogin yes

to

PermitRootLogin no

Save the new file, and restart ssh with the command:

systemctl restart ssh.service

This will lose your connection.

## get remscope software from git

Login to the server again

ssh <ip address of VPS>

load the remscope software from the git repository:

git clone git@github.com:bernie-skipole/remscope.git

This should create the directory remscope, change into that directory

cd remscope

Gain root permissions with:

sudo bash

This may ask for your password

Then run a script to install software

source buildserver








