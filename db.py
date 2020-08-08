import psycopg2
import os
from urllib.parse import urlparse
import json
import config
import functools
import random

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
        "ts": record[6],
    }

@ErrorRollback
def getConfirmedUserByUserid(userid):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE userid=%s AND setup_state='EMAIL_CONFIRMED'""", (userid,))
    result = c.fetchone()
    c.close()
    conn.commit()

    # TODO: raise exception
    if not result:
        return None

    return toUserJson(result)

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
    c.close()
    conn.commit()

    if not result:
        return None

    return toUserJson(result)

@ErrorRollback
def getConfirmedUserByUsernameEmail(username, email):
    conn = getConn()
    c = conn.cursor()
    c.execute("""
        SELECT userid, username, displayname, email, password_hash, setup_state, ts
        FROM users WHERE username=%s AND email=%s setup_state='EMAIL_CONFIRMED'""", (username, email))
    result = c.fetchone()
    c.close()
    conn.commit()

    if not result:
        return None

    return toUserJson(result)

class ShouldBeImpossible(Exception):
   pass

class MultipleConfirmedAccounts(Exception):
    pass

# TODO: get roles too
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
    c.close()
    conn.commit()

    if not result:
        return None

    return toUserJson(result)

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
