# File: groups.py
# Author: Jon Catanio
# Description: Endpoints related to groups, create groups, get user groups, add member to group.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
from user_tokens import validateToken
import json
import base64
import datetime
from flask import Blueprint, request

groups_api = Blueprint('groups_api', __name__)

@groups_api.route("/groups/")
def getUserGroups():
   data = []
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            G.id,
            G.name,
            G.img
         FROM
            Tokens AS T
            INNER JOIN GroupMembers AS GB ON GB.userId = T.user
            INNER JOIN Groups AS G ON GB.groupId = G.id
         WHERE
            token = %s
            AND G.deleted <> 1
      """, [request.headers['Authorization']])

      rows = cur.fetchall()
      if not rows:
         return json.dumps(response), 204

      for row in rows:
         obj = {}
         obj['groupId'] = row[0]
         obj['groupName'] = row[1]
         img = open(row[2], 'r').read()
         obj['groupImg'] = img.encode('base64')

         cur.execute("""
            SELECT SUM(totalAmt)
            FROM Bills
            WHERE groupId = %s
            """, [obj['groupId']])
         col = cur.fetchone()
         obj['amtOwedAsGroup'] = str(col[0])

         data.append(obj)
   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(data), 200

@groups_api.route("/group/<int:groupId>/")
def getUserGroup(groupId):
   obj = {}
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            G.id,
            G.name,
            G.img
         FROM
            Tokens AS T
            INNER JOIN GroupMembers AS GB ON GB.userId = T.user
            INNER JOIN Groups AS G ON GB.groupId = G.id
         WHERE
            token = %s
            AND G.id = %s
            AND G.deleted <> 1
         """, [request.headers['Authorization'], groupId])

      rows = cur.fetchall()
      if not rows:
         return json.dumps(response), 204

      for row in rows:
         obj['groupId'] = row[0]
         obj['groupName'] = row[1]
         img = open(row[2], 'r').read()
         obj['groupImg'] = img.encode('base64')

         cur.execute("""
            SELECT SUM(totalAmt)
            FROM Bills
            WHERE groupId = %s
            """, [obj['groupId']])
         col = cur.fetchone()
         obj['amtOwedAsGroup'] = str(col[0])

         members = []
         cur.execute("""
            SELECT
               U.id,
               U.username,
               U.name,
               U.profilePic,
               U.email
            FROM
               Users AS U
               INNER JOIN GroupMembers AS GB ON U.id = GB.userId
            WHERE
               groupId = %s
            """, [obj['groupId']])
         mems = cur.fetchall()
         for mem in mems:
            mObj = {}
            mObj['userId'] = mem[0]
            mObj['username'] = mem[1]
            mObj['name'] = mem[2]

            mImg = open(mem[3], 'r').read()
            mObj['profilePic'] = mImg.encode('base64')

            mObj['email'] = mem[4]
            members.append(mObj)

         obj['members'] = members

   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(obj), 200

@groups_api.route('/groups/add/', methods = ['POST'])
def addGroup():
   response = {}
   groupId = None

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

      # TODO remove this when we figure out images.
      imgPath = "../img/group/default-group-img.png"
      if req['groupImg'] != '':
         imgPath = '../img/group/' + str(datetime.datetime.now().isoformat())
         f = open(imgPath, 'w')
         f.write(base64.b64decode(req['groupImg']))
         f.close()

      cur.execute("""
         INSERT INTO Groups VALUES
            (NULL, %s, NOW(), %s, 0)
         """, [req['groupName'], imgPath])
      groupId = cur.lastrowid

      cur.execute("""
         INSERT INTO GroupMembers VALUES
            (%s, %s, 0)
         """, [userId, groupId])
      db.commit()
   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   response['groupId'] = groupId
   return json.dumps(response), 200

@groups_api.route('/groups/addMember/', methods = ['POST'])
def addMemberToGroup():
   response = {}
   groupId = None

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      req = request.get_json(True, True, False)
      if req == None:
         return json.dumps(response), 500

      # Check if token is actually in group and should be able to add.
      cur.execute("""
         SELECT *
         FROM
            Tokens AS T
            INNER JOIN GroupMembers AS GM ON T.user = GM.userId
         WHERE
            GM.groupId = %s
            AND token = %s
         """, [req['groupId'], request.headers['Authorization']])
      rows = cur.fetchone()
      if rows == None:
         return json.dumps(response), 403

      username = ''
      email = ''
      if 'username' in req:
         username = req['username']
      if 'email' in req:
         email = req['email']

      cur.execute("""
         SELECT id
         FROM Users
         WHERE
            username = %s
            OR email = %s
         """, [username, email])

      row = cur.fetchone()
      if row == None:
         return json.dumps(response), 204
      userId = row[0]

      # check if user is already in group
      cur.execute("""
         SELECT COUNT(*)
         FROM GroupMembers
         WHERE
            userId = %s
            AND groupId = %s
         """, [userId, req['groupId']])

      row = cur.fetchone()
      if row == None:
         return json.dumps(response), 500
      if row[0] == 0:
         cur.execute("""
            INSERT INTO GroupMembers VALUES
               (%s, %s, 0)
            """, [userId, req['groupId']])
         db.commit()
      else:
         print('member already present in group');
   except MySQLError:
      response['message'] = 'Internal Server Error'
      db.rollback()
      return json.dumps(response), 500

   response['success'] = True
   return json.dumps(response), 200
