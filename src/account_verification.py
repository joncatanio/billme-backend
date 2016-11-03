# File: account_verification.py
# Author: Jon Catanio
# Description: Utility functions for account verification and validation.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError

# Get the password for <username>.
def getPassword(username):
   try:
      cur.execute("""\
         SELECT password
         FROM Users
         WHERE username = %s""", (username,)
      )
      db.commit()
   except MySQLError:
      raise

   pw = cur.fetchone()
   if pw is None:
      return None

   cur.fetchall()
   return pw[0]

# Get the password for the user with token: <token>
def getPasswordT(token):
   try:
      cur.execute("""\
         SELECT password
         FROM
            Users AS U
            INNER JOIN Tokens AS T ON U.id = T.user
         WHERE token = %s""", (token,)
      )
      db.commit()
   except MySQLError:
      raise

   pw = cur.fetchone()
   if pw is None:
      return None

   cur.fetchall()
   return pw[0]
