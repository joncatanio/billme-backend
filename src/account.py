# File: account.py
# Author: Jon Catanio
# Description: Endpoints related to user accounts, get user data to change.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
from user_tokens import validateToken
import json
import base64
import datetime
from flask import Blueprint, request

account_api = Blueprint('account_api', __name__)

@account_api.route('/account/')
def getAccountInfo():
   data = {}
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            id, username, email, name, profilePic
         FROM
            Tokens AS T
            INNER JOIN Users AS U ON T.user = U.id
         WHERE
            token = %s
         """, [request.headers['Authorization']])
      row = cur.fetchone()
      if row == None:
         response['message'] = 'Internal Server Error'
         return json.dumps(response), 500

      data['id'] = row[0]
      data['username'] = row[1]
      data['email'] = row[2]
      data['name'] = row[3]

      img = open(row[4], 'r').read()
      data['profilePic'] = img.encode('base64')

   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(data), 200

@account_api.route('/account/update/', methods = ['POST'])
def updateAccountInfo():
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      req = request.get_json(True, True, False)
      if req == None:
         return json.dumps(response), 500

      cur.execute("""
         SELECT user FROM Tokens WHERE token = %s
         """, [request.headers['Authorization']])
      user = cur.fetchall()
      userId = user[0]

      # Get the image path from the db if it is the default, replace the path.
      cur.execute("""
         SELECT profilePic
         FROM Users
         Where id = %s
         """, [userId])
      row = cur.fetchone()
      imgPath = row[0]
      if imgPath == '../img/user/default-user-img.png':
         imgPath = '../img/user/' + str(datetime.datetime.now().isoformat())
         
      img = open(imgPath, 'w')
      img.write(base64.b64decode(req['userImg']))
      img.close()

      cur.execute("""
         UPDATE Users
         SET
            username = %s,
            email = %s,
            name = %s,
            profilePic = %s
         WHERE id = %s
         """, [req['username'], req['email'],
               req['name'], imgPath, userId])
      db.commit()

   except IntegrityError:
      response['message'] = 'Username/Email already taken'
      return json.dumps(response), 500
   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(response), 200
