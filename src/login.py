# File: login.py
# Author: Jon Catanio
# Description: Endpoints for user login.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
import json
import bcrypt
from account_verification import getPassword
from user_tokens import purgeToken, addToken, generateToken
from flask import Blueprint, request

login_api = Blueprint('login_api', __name__)

@login_api.route("/login", methods = ['POST'])
def login():
   data = {}
   response = {}

   try:
      hashedpw = getPassword(request.form['username'])
      if hashedpw is None:
         response['message'] = 'Invalid username.'
         return json.dumps(response), 403
      hashedpw = hashedpw.encode('utf-8')

      # TODO verify this, and make sure addToken() doesn't fail.
      if hashedpw == bcrypt.hashpw(request.form['password'].encode('utf-8'), hashedpw):
         token = generateToken()
         purgeToken(request.form['username'])
         addToken(request.form['username'], token)
         db.commit()

         data['token'] = token
      else:
         response['message'] = 'Invalid password.'
         return json.dumps(response), 403
   except IntegrityError:
      response['message'] = 'Duplicate token.'
      return json.dumps(), 500
   except MySQLError:
      response['message'] = 'Internal Server Error.'
      return json.dumps(response), 500

   return json.dumps(data) 
