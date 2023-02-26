
# Clears out expired guests

# This is typically run with a cron entry

# 0 12,13 * * * /usr/bin/python3 ~/www/astrodata/maindb/clearguests.py >/dev/null 2>&1

# run every mid day, and mid day + 1 hour
# cron works on local time, so mid day, and mid day + 1 should get 12 utc between them


import sys, os, sqlite3

from datetime import datetime

now = datetime.utcnow()

# ensure time is utc 12:00
if now.hour != 12:
    sys.exit(0)


message = "Clearing expired guests"

con = None
try:
    database_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'main.db')
    con = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
    con.execute("PRAGMA foreign_keys = 1")
    cur = con.cursor()
    cur.execute("select user_id from guests where exp_date < ?", (now,))
    guests = cur.fetchall()
    if guests:
        for guest in guests:
            user_id = guest[0]
            cur.execute("delete from slots where user_id = ?", (user_id,))
            cur.execute("delete from users where user_id = ?", (user_id,))
        con.commit()
        message = "deleted expired guests"
    else:
        message = "check made for expired guests - none found"
except Exception:
    message = "check for expired guests has failed"
finally:
    if con:
        con.close()

print(message)

sys.exit(0)

