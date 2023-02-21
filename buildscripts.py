# to create a virtual env and load packages from requirements.txt


from venv import create
from os.path import join, expanduser
from subprocess import run
from os.path import abspath

resenvdir = join(expanduser("~"), "rsenv")
create(dir, with_pip=True)

# where requirements.txt is in same directory as this script
run(["bin/pip", "install", "-r", abspath("requirements.txt")], cwd=resenvdir)
