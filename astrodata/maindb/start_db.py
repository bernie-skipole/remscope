"""
This script creates the database of users, and session slots
"""

import os, sqlite3, hashlib



# This is the default admin username
_USERNAME = "admin"
# This is the default  admin password
_PASSWORD = "password"
# This is the default  admin PIN
_PIN = "1234"

_MAIL_SERVER = 'smtp.googlemail.com'

_NO_REPLY = 'no_reply@skipole.co.uk'


def hash_password(project, user_id, password):
    "Return hashed password, as a string, on failure return None"
    seed_password = project + str(user_id) +  password
    hashed_password = hashlib.sha512(   seed_password.encode('utf-8')  ).digest().hex()
    return hashed_password


def hash_pin(pin, seed):
    "Return hashed pin, as a string, on failure return None"
    seed_pin = seed +  pin
    hashed_pin = hashlib.sha512(   seed_pin.encode('utf-8')  ).digest().hex()
    return hashed_pin

def set_pin(project, user_id, new_pin, con):
    "Return True on success, False on failure, this updates an existing admin, does not commit"

    # The seed for each hash will consist of project + user_id + pair numbers
    part_seed = project + str(user_id)
    pin1_2 = hash_pin(new_pin[0] + new_pin[1], seed=part_seed+'1')
    pin1_3 = hash_pin(new_pin[0] + new_pin[2], seed=part_seed+'2')
    pin1_4 = hash_pin(new_pin[0] + new_pin[3], seed=part_seed+'3')
    pin2_3 = hash_pin(new_pin[1] + new_pin[2], seed=part_seed+'4')
    pin2_4 = hash_pin(new_pin[1] + new_pin[3], seed=part_seed+'5')
    pin3_4 = hash_pin(new_pin[2] + new_pin[3], seed=part_seed+'6')
    try:
        con.execute("insert or replace into admins (user_id, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4) values (?, ?, ?, ?, ?, ?, ?)", (user_id, pin1_2, pin1_3, pin1_4, pin2_3, pin2_4, pin3_4))
    except:
        return False
    return True




def start_database(project):
    """Must be called first, before any other database operation to create the database"""
 
    # create a database main.db in the directory where this script is located
    database_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.db')

    # create the database
    try:
        con = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        con.execute("PRAGMA foreign_keys = 1")
    except:
        raise ServerError(message="Failed database connection.")
    try:

        # make table of users
        con.execute("create table users (USER_ID INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password BLOB, role TEXT, email TEXT, member TEXT, guests INTEGER)")

        con.execute("create table guests (USER_ID INTEGER PRIMARY KEY, sponsor_id INTEGER, exp_date TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)")

        # make table for admins, with pins
        con.execute("CREATE TABLE admins (user_id INTEGER PRIMARY KEY, pin1_2 BLOB, pin1_3 BLOB, pin1_4 BLOB, pin2_3 BLOB, pin2_4 BLOB, pin3_4 BLOB, FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE)")

        # Make a table for server settings
        con.execute("CREATE TABLE serversettings (server_id TEXT PRIMARY KEY, emailuser TEXT, emailpassword TEXT, emailserver TEXT, no_reply TEXT, starttls INTEGER, sessions INTEGER)")

        # create a table of variables
        con.execute("CREATE TABLE variabletext (variable_name TEXT PRIMARY KEY, variable_text TEXT)")

        # create table of status message
        con.execute("CREATE TABLE messages (mess_id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, time TIMESTAMP, username TEXT)")


        # create table of slots
        con.execute("CREATE TABLE slots (starttime TIMESTAMP PRIMARY KEY, status INTEGER, user_id INTEGER)")

        # Create trigger to maintain only 10 messages
        n_messages = """CREATE TRIGGER n_messages_only AFTER INSERT ON messages
   BEGIN
     DELETE FROM messages WHERE mess_id <= (SELECT mess_id FROM messages ORDER BY mess_id DESC LIMIT 1 OFFSET 10);
   END;"""
        con.execute(n_messages)

        # Create trigger to maintain only 100 slots
        n_slots = """CREATE TRIGGER n_slots_only AFTER INSERT ON slots
   BEGIN
     DELETE FROM slots WHERE starttime <= (SELECT starttime FROM slots ORDER BY starttime DESC LIMIT 1 OFFSET 100);
   END;"""
        con.execute(n_slots)

        # create database contents by inserting initial default values
        # make admin user password, role is 'ADMIN', user_id is 1
        hashed_password = hash_password(project, 1, _PASSWORD)

        con.execute("insert into users (USER_ID, username, password, role, email, member, guests) values (?, ?, ?, ?, ?, ?, ?)", (None, _USERNAME, hashed_password,  'ADMIN', None, None, 0))

        # set admin pin, with user_id 1
        set_pin(project, 1, _PIN, con)

        # set email server settings
        con.execute("INSERT INTO serversettings (server_id,  emailuser, emailpassword, emailserver, no_reply, starttls, sessions) VALUES (?, ?, ?, ?, ?, ?, ?)", ('1', None, None, _MAIL_SERVER, _NO_REPLY, 1, 1))


        con.execute("INSERT INTO variabletext (variable_name, variable_text) values (?, ?)", ('org_name', 'The Astronomy Centre'))

        con.execute("INSERT INTO variabletext (variable_name, variable_text) values (?, ?)", ('header_text', 'Astronomy Centre : REMSCOPE'))

        con.execute("INSERT INTO variabletext (variable_name, variable_text) values (?, ?)", ('home_text', 'The Astronomy Centre robotic telescope.'))

        con.commit()
    finally:
        con.close()


if __name__ == "__main__":

    start_database("remscope")

