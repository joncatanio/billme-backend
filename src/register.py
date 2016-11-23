# File: register.py
# Author: Jon Catanio
# Description: Handles user registration and the email token verification.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
from user_tokens import addToken, generateToken
import bcrypt
import json
from flask import Blueprint, request

register_api = Blueprint('register_api', __name__)

@register_api.route("/register", methods = ['POST'])
def register():
   response = {}
   hashedpw = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
   # TODO change this to a valid image.
   # get image from request.files as part of multiformdata.
   imgPath = "../img/user/default-user-img.png"

   try:
      cur.execute("""\
         INSERT INTO Users VALUES
            (NULL, %s, %s, %s, %s, NOW(), %s, 0)""",
         [request.form['username'], request.form['email'], request.form['name'],
          imgPath, hashedpw]
      );
   except IntegrityError:
      response['message'] = 'Username or email already taken.'
      return json.dumps(response), 400
   except MySQLError:
      response['message'] = 'Internal Server Error.'
      return json.dumps(response), 500

   try:
      token = generateToken()
      addToken(request.form['username'], token)
      response['token'] = token
   except IntegrityError:
      response['message'] = 'Duplicate token.'
      return json.dumps(response), 500
   except MySQLError:
      response['message'] = 'Internal Server Error.'
      return json.dumps(response), 500
      
   # Commit Users and Tokens table updates.
   db.commit()

   return json.dumps(response), 200
