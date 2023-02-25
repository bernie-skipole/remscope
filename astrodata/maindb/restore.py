"Run to restore a backup file"

import os, sys, sqlite3, bz2, base64

from cryptography.fernet import Fernet

astrodata_directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

this_directory = os.path.dirname(os.path.realpath(__file__))

served_directory = os.path.join(astrodata_directory, 'served')

backups_directory = os.path.join(served_directory, 'backups')

database_file = os.path.join(this_directory, 'main.db')


def readfile(filepath):
    "Returns the binary data from the file"
    if not os.path.isfile(filepath):
        return
    with open(filepath, 'rb') as f:
        bdata = f.read()
    return bdata


def decrypt(bdata):
    "Decrypt the binary data, returns the unencrypted data, or None on failure"
    keyfile = os.path.join(this_directory, 'keyfile')
    if not os.path.isfile(keyfile):
        return
    # read key from file
    with open(keyfile, 'r') as k:
        keydata = k.read()
        key = base64.b64decode(keydata)
    f = Fernet(key)
    return f.decrypt(bdata)

def uncompress(compressed_data):
    "Uncompresses the data and returns a string"
    return bz2.decompress(compressed_data).decode("utf-8")


def restoredatabase(sql_script):
    "Restore database"
    try:
        con = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 0")
        cur = con.cursor()
        cur.executescript(sql_script)
    except:
        return False
    finally:
        con.close()
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error:usage should be restore.py <path to backup file>")
        sys.exit(1)
    if os.path.isfile(database_file):
        print(f"Error:The database file {database_file} already exists.")
        print("Delete or rename it before this program creates a new file.")
        sys.exit(1)
    filepath = os.path.abspath(os.path.expanduser(sys.argv[1]))
    bdata = readfile(filepath)
    if bdata is None:
        print("Error:The backup file not found.")
        sys.exit(1)
    compressed_data = decrypt(bdata)
    if compressed_data is None:
        print("Error:The encryption key file not found.")
        sys.exit(1)
    sql_script = uncompress(compressed_data)
    if restoredatabase(sql_script):
        print("Database restored")
    else:
        print("Failed to restore the database")

