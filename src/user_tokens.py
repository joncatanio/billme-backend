# File: user_tokens.py
# Author: Jon Catanio
# Description: Token related helper functions.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
import random

# Purge the preexisting token for <username>. 
# purgeToken and addToken are committed together.
def purgeToken(username):
   try:
      cur.execute("""\
         UPDATE Tokens
         SET revoked = 1
         WHERE
            revoked = 0
            AND user = (
                  SELECT id
                  FROM Users
                  WHERE username = %s
               )""", (username,)
      )
   except MySQLError:
      raise

# TODO if there is a duplicate token generate until a valid one is found.
# Add a token for <username>. 
def addToken(username, token):
   try:
      cur.execute("""\
         INSERT INTO Tokens (
            user,
            token,
            expire,
            revoked
         )
         SELECT
            id,
            %s,
            NOW() + INTERVAL 15 DAY,
            0
         FROM Users
         WHERE username = %s""", (token, username,)
      )
   except IntegrityError:
      raise
   except MySQLError:
      raise

# Validates a token. Returns true if token is valid and false otherwise.
def validateToken(token):
   try:
      cur.execute("""\
         SELECT
            revoked,
            TIMESTAMPDIFF(SECOND, NOW(), expire)
         FROM Tokens
         WHERE token = %s""", (token,)
      )
      db.commit()
   except MySQLError:
      raise

   row = cur.fetchone()
   if row is None or row[0] == 1 or row[1] <= 0:
      return False

   cur.fetchall()
   return True

# Generates a random token represented as a 64 character hexidecimal string. 
def generateToken():
   return '%064x' % random.randrange(16**64)
