import psycopg2
import os
from urllib.parse import urlparse
import json
import config
import functools
import random

# This might come in handy later:
#   SELECT u.username, STRING_AGG(r.role, ',')
#   FROM users u
#   LEFT JOIN roles r ON (u.userid = r.userid)
#   WHERE u.userid=1;

# Error rollback everywhere
# TODO: logging

DATABASE_URL = os.environ["DATABASE_URL"]

result = urlparse(DATABASE_URL)
POSTGRES_USER = result.username
POSTGRES_PW = result.password
POSTGRES_DB = result.path[1:]
POSTGRES_PORT = result.port
POSTGRES_HOST = result.hostname

def openConn():
    return psycopg2.connect("dbname='%s' user='%s' host='%s' port='%s' password='%s'" %
        (POSTGRES_DB, POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_PW))

CONNECTION = openConn()

def getConn():
    global CONNECTION
    if CONNECTION.closed:
        CONNECTION = openConn()
    return CONNECTION

def ErrorRollback(func):
    @functools.wraps(func)
    def wrapper(*a, **kw):
        try:
            return func(*a, **kw)
        except:
            print("ROLLING BACK")
            getConn().rollback()
            raise    
    return wrapper

def toUserJson(record):
    return {
        "userid": record[0],
        "username": record[1],
        "displayname": record[2],
        "email": record[3],
        "password_hash": record[4],
        "setup_state": record[5],
        "ts": record[6]
    }

@ErrorRollback
def getConfirmedUserByUserid(userid):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE userid=%s AND setup_state='EMAIL_CONFIRMED'""", (userid,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

@ErrorRollback
def getConfirmedUsersByUserids(userids):
    results = []
    for userid in userids:
        result = getConfirmedUserByUserid(userid)
        if result:
            results.append(result)
        else:
            pass # TODO: raise exception
    return results

# TODO: get roles too
@ErrorRollback
def getConfirmedUserByUsername(username):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE username=%s AND setup_state='EMAIL_CONFIRMED'""", (username,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

@ErrorRollback
def getConfirmedUserByUsernameEmail(username, email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE username=%s AND email=%s setup_state='EMAIL_CONFIRMED'""", (username, email))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

class ShouldBeImpossible(Exception):
   pass

class MultipleConfirmedAccounts(Exception):
    pass

# IMPORTANT NOTE: the roles field will not exist within results
@ErrorRollback
def getAllUsersForAnySetupStateByEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE email=%s""", (email,))
    results = c.fetchall()
    c.close()
    conn.commit()

    if not results:
        return []

    results = [toUserJson(record) for record in results]

    if len(results) == 0:
        raise ShouldBeImpossible

    numConfirmed = 0
    for record in results:
        if record["setup_state"] == "EMAIL_CONFIRMED":
            numConfirmed += 1

    if numConfirmed > 1:
        raise MultipleConfirmedAccounts

    return results

@ErrorRollback
def createUnconfirmedAccount(username, displayname, email, password_hash):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO users
        (username, displayname, email, password_hash, setup_state)
        VALUES (%s, %s, %s, %s, 'CONFIRMATION_EMAIL_SENT') """, (username, displayname, email, password_hash))

    c.execute("SELECT MAX(userid) FROM users")
    result = c.fetchone()
    useridInt = result[0]
    c.close()
    conn.commit()

    # NOTE: userids are always of type of string, even though they just hold a number
    # This is convenient because SESSION["userid"] will always be a string
    return str(useridInt)

class UpdatePasswordByUsernameEmailError(Exception):
    pass

@ErrorRollback
def updateUnconfirmedPasswordByUsernameEmail(username, email, password_hash):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET password_hash=%s
        WHERE username=%s and email=%s;""", (password_hash, username, email))
    rowcount  = c.rowcount
    c.close()
    if rowcount == 1:
        conn.commit()
    else:
        conn.rollback()
        raise UpdatePasswordByUsernameEmailError

@ErrorRollback
def updateConfirmedPasswordByUsernameEmail(email, password_hash):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET password_hash=%s
        WHERE setup_state='EMAIL_CONFIRMED' and email=%s;""", (password_hash, email))
    rowcount  = c.rowcount
    c.close()
    if rowcount == 1:
        conn.commit()
    else:
        conn.rollback()
        raise UpdatePasswordByUsernameEmailError

# IMPORTNANT NOTE: the returned user dict will not have a role field
@ErrorRollback
def getUnconfirmedUserByUsernameEmail(username, email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE username=%s and email=%s""", (username, email,))
    result = c.fetchone()
    c.close()
    conn.commit()

    if not result:
        return None
    else:
        return toUserJson(result)



class ConfirmUsernameEmailErrorRowCountNotOne(Exception):
    pass

@ErrorRollback
def confirmUsernameEmail(username, email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        UPDATE users
        SET setup_state='EMAIL_CONFIRMED'
        WHERE username=%s AND email=%s;""", (username, email,))
    rowcount = c.rowcount
    if rowcount != 1:
        c.close()
        conn.rollback()
        raise ConfirmUsernameEmailErrorRowCountNotOne

    c.execute("""
        UPDATE users
        SET setup_state='RETIRED'
        where email=%s AND setup_state != 'EMAIL_CONFIRMED';
        """, (email, ))

    c.close()
    conn.commit()

@ErrorRollback
def getConfirmedUserByEmail(email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE email=%s AND setup_state='EMAIL_CONFIRMED'""", (email,))
    result = c.fetchone()
    
    # TODO: raise exception?
    if not result:
        c.close()
        conn.commit()
        return None

    user = toUserJson(result)

    c.execute("""
        SELECT role FROM roles WHERE userid=%s""", (user["userid"],))
    user["roles"] = [r[0] for r in c.fetchall()]

    c.close()
    conn.commit()

    return user

@ErrorRollback
def getConfirmedUserByUsernameOrEmail(usernameOrEmail):
    user = getConfirmedUserByUsername(usernameOrEmail)
    if user:
        return user
    user = getConfirmedUserByEmail(usernameOrEmail)
    return user

@ErrorRollback
def markTokenUsed(token):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO usedtokens
        (token)
        VALUES (%s) """, (token,))
    c.close()
    conn.commit()

@ErrorRollback
def hasTokenBeenUsed(token):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT usedtokenid
        FROM usedtokens where token=%s""", (token,))
    result = c.fetchone()
    c.close()
    conn.commit()

    if result:
        return True
    else:
        return False

def toPageJson(record):
    return {
        "contributoruserid": record[0],
        "pagename": record[1],
        "revision": record[2],
        "content": record[3],
        "ts": record[4]
    }



# Get the most recent page
@ErrorRollback
def getPage(pagename, revision=None):
    conn = getConn()
    c = conn.cursor()
    if revision == None:
        c.execute("""
            SELECT contributoruserid, pagename, revision, content, ts
            FROM pages
            WHERE pagename=%s
            ORDER BY pageid DESC
            LIMIT  1""", (pagename,))
        result = c.fetchone()
        c.close()
        conn.commit()

        if not result:
            return None

        return toPageJson(result)

    else:
        c.execute("""
            SELECT contributoruserid, pagename, revision, content, ts
            FROM pages
            WHERE pagename=%s AND revision=%s
            ORDER BY pageid DESC
            LIMIT  1""", (pagename, revision))
        result = c.fetchone()
        c.close()
        conn.commit()

        if not result:
            return False 

        return toPageJson(result)

def toPagePermissionsJson(record):
    return {
        "pagename": record[0],
        "owneruserid": record[1],
        "allowcomments": record[2],
        "allowedits": record[3],
        "ts": record[4]
    }

# Get the permissions for a page
@ErrorRollback
def getPagePermissions(pagename):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT pagename, owneruserid, allowcomments, allowedits, ts
        FROM pagepermissions
        WHERE pagename=%s""", (pagename,))
    result = c.fetchone()
    c.close()
    conn.commit()

    if not result:
        return None

    return toPagePermissionsJson(result)

@ErrorRollback
def getOwner(pagename):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT owneruserid
        FROM pagepermissions
        WHERE pagename=%s""", (pagename,))
    result = c.fetchone()

    if not result:
        c.close()
        conn.commit()
        return None

    userid = result[0]

    c.execute("""
        SELECT username
        FROM users WHERE userid=%s AND setup_state='EMAIL_CONFIRMED'""", (userid,))
    result = c.fetchone()

    if not result:
        c.close()
        conn.commit()
        return None

    username = result[0]
    
    return {
        "userid": userid,
        "username": username
    }   

@ErrorRollback
def savePermissions(pagename, allowEdits):
    conn = getConn()
    c = conn.cursor()

    if allowEdits:
        allowEditsDigit = 1
    else:
        allowEditsDigit = 0

    c.execute("""
        UPDATE pagepermissions
        SET allowedits=%s
        WHERE pagename=%s
        """, (allowEditsDigit, pagename))

    c.close()
    conn.commit()

@ErrorRollback
def searchForMatchingPageNames(searchTerm):
    conn = getConn()
    c = conn.cursor()

    # Is doing   "%" +   a good idea?
    searchTerm = "%" + searchTerm.lower() + "%"

    c.execute("""
        SELECT p.pagename, p.revision
        FROM pages p
        INNER JOIN (
            SELECT MAX(revision) AS maxrevision, pagename AS maxpagename
            FROM pages
            GROUP BY pagename
        ) pp ON p.revision = pp.maxrevision AND p.pagename = pp.maxpagename
        WHERE LOWER(p.content) LIKE %s
    """, (searchTerm,))

    results = c.fetchall()
    if results == None:
        results = []

    results = [record[0] for record in results]

    c.close()
    conn.commit()

    return results



@ErrorRollback
def savePage(contributoruserid, pagename, content):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        SELECT revision
        FROM pages
        WHERE pagename=%s
        ORDER BY pageid DESC
        LIMIT  1""", (pagename,))
    result = c.fetchone()

    if not result:
        revision = 1

        c.execute("""
            INSERT INTO pagepermissions (pagename, owneruserid, allowcomments, allowedits)
            VALUES (%s, %s, 1, 1)
            """, (pagename, contributoruserid))

    else:
        revision = result[0] + 1

    c.execute("""
        INSERT INTO pages
        (contributoruserid, pagename, revision, content)
        VALUES (%s, %s, %s, %s) """, (contributoruserid, pagename, revision, content))

    c.close()
    conn.commit()

    return revision

# Optimization idea: run getExistingPagenames upon edit and store results:
# slower writes / faster reads?
@ErrorRollback
def getExistingPagenames(pagenames):
    if len(pagenames) == 0:
        return []

    conn = getConn()
    c = conn.cursor()

    # Limit to 500 to avoid slamming database
    trimmedPagenames = pagenames[:500]

    # I don't know how performant this is
    c.execute("""SELECT pagename FROM pages WHERE pagename IN %s AND revision=1""", (tuple(trimmedPagenames),))

    results = c.fetchall()
    c.close()
    conn.commit()

    if not results:
        return []

    results = [r[0] for r in results]

    return results

def historyRecordToJson(h):
    username = h[0]
    if username == None:
        username = "Anonymous"
    return {
        "username": username,
        "userid": h[1],
        "revision": h[2],
        "ts": h[3]
    }

@ErrorRollback
def getHistory(pagename):

    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT u.username, p.contributoruserid, p.revision, p.ts
        FROM pages p
        LEFT JOIN users u
        ON u.userid=p.contributoruserid
        WHERE p.pagename=%s
        ORDER BY p.pageid DESC""", (pagename,))
    result = c.fetchall()
    c.close()
    conn.commit()

    if not result:
        return []

    history = [historyRecordToJson(h) for h in result]

    #print(json.dumps(history, indent=4, sort_keys=True))
    return history

@ErrorRollback
def isCaptchaAlreadyUsed(c_text):
    # milliseconds in a day == 86400000
    # Begin by cleaning up captcha table
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        DELETE FROM captchas WHERE ts + 86400000 < CAST((extract(epoch from now()) * 1000) as BIGINT) 
        """)

    # Then, look for the captcha
    c.execute("""
        SELECT ctext FROM captchas WHERE ctext=%s
        """, (c_text,))
    found = c.fetchone() is not None
    c.close()
    conn.commit()

    return found

@ErrorRollback
def markCaptchaAsUsed(c_text):
    conn = getConn()
    c = conn.cursor()

    c.execute("""
        INSERT INTO captchas
        (ctext)
        VALUES (%s) """, (c_text,))
    c.close()
    conn.commit()
