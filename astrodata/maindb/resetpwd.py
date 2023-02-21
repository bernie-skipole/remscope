"""Run to set a new password and pin for the admin user"""


import os, sqlite3, hashlib


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


if __name__ == "__main__":

    password = input(f"Input a new password for user admin:")

    new_pin = input("Input a new pin:")

    database_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.db')
    con = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    con.execute("PRAGMA foreign_keys = 1")
    try:
        pwd = hash_password("remscope", 1, password)
        con.execute("update users set password = ? where user_id = 1", (pwd,))
        set_pin("remscope", 1, new_pin, con)
        con.commit()
    finally:
        con.close()

    print("password and pin have been set for the admin user")

