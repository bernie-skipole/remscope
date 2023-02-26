"""Creates encrypted backup file of the database"""

# This is typically run with a cron entry

# 30 14 * * 6 /usr/bin/python3 ~/www/astrodata/maindb/backup.py >/dev/null 2>&1
#
# ie 2:30 afternoon every saturday



import sys, os, sqlite3, bz2, datetime, pathlib, base64

from cryptography.fernet import Fernet


# Backups will be saved in ~/www/astrodata/served/backups
# this calculates it relative to the position of this file

astrodata_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

this_directory = os.path.dirname(os.path.realpath(__file__))

served_directory = os.path.join(astrodata_directory, 'served')

backups_directory = os.path.join(served_directory, 'backups')

database_file = os.path.join(this_directory, 'main.db')


def check_backups_dir():
    "If necessary, creates the backups directory"
    if not os.path.isdir(served_directory):
        print(f"The directory {served_directory} does not exist, please create it")
        sys.exit(1)
    if not os.path.isdir(backups_directory):
        print(f"Creating directory {backups_directory}")
        os.mkdir(backups_directory)


def dump_database():
    "Returns a string being a dump of the sql database"
    try:
        con = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 1")
        sql_list = list(con.iterdump())
    except:
        return
    finally:
        con.close()
    if not sql_list:
        return
    return "\n".join(sql_list)


def compress(data):
    "Returns the data string as a bz2 compressed binary string"
    return bz2.compress(data.encode('utf-8'))


def encrypt(bdata):
    "Encrypt the binary data"
    # the key is held in keyfile, b64 encoded
    keyfile = os.path.join(this_directory, 'keyfile')
    if os.path.isfile(keyfile):
        # read key from file
        with open(keyfile, 'r') as k:
            keydata = k.read()
            key = base64.b64decode(keydata)
    else:
        # generate a new key, and save it
        key = Fernet.generate_key()
        with open(keyfile, 'w') as k:
            keydata = base64.b64encode(key)
            k.write(keydata.decode('ascii'))
    f = Fernet(key)
    return f.encrypt(bdata)


def savedata(edata):
    "Saves the binary data to a file in the backups directory. The filename will be composed of datetime string"
    check_backups_dir()
    destinationfile = os.path.join(backups_directory, datetime.datetime.now().strftime("%Y%m%d%H%M.backup"))
    with open(destinationfile, 'wb') as f:
        f.write(edata)

def limitfiles():
    "Deletes old backup files, leaving just latest five in the backup directory"
    if not os.path.isdir(backups_directory):
        return
    destination = pathlib.Path(backups_directory)
    serverfiles = [f.name for f in destination.iterdir() if f.is_file()]
    if len(serverfiles) <= 5:
        return
    # delete the last one
    serverfiles.sort(reverse=True)
    oldest_file = destination / serverfiles[-1]
    oldest_file.unlink()


if __name__ == "__main__":
    data = dump_database()
    if data is None:
        print("Failed to backup the database")
        sys.exit(1)
    compressed_data = compress(data)
    encrypted_data = encrypt(compressed_data)
    savedata(encrypted_data)
    limitfiles()
    sys.exit(0)



