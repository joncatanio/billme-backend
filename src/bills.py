# File: bills.py
# Author: Jon Catanio
# Description: Endpoints related to bills, getting all user bills or adding a
#              new bill.

from billme_db import db, cur
from _mysql_exceptions import MySQLError, IntegrityError
from user_tokens import validateToken
import json
from flask import Blueprint, request

bills_api = Blueprint('bills_api', __name__)

def getUserBills(current):
   data = []
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            billId,
            paid,
            pending,
            B.name,
            totalAmt,
            U.username,
            U.name,
            dueDate,
            G.name
         FROM
            Tokens AS T
            INNER JOIN UserBills AS UB ON T.user = UB.userId
            INNER JOIN Bills AS B ON UB.billId = B.id
            INNER JOIN Users AS U ON B.owner = U.id
            INNER JOIN Groups AS G ON B.groupId = G.id
         WHERE
            T.token = %s
            AND B.deleted <> 1
            AND B.complete <> %s
         ORDER BY
            dueDate ASC
         """, [request.headers['Authorization'], str(current)])
   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   rows = cur.fetchall()
   if not rows:
      return json.dumps(response), 204

   for row in rows:
      obj = {}
      obj['billId'] = row[0]
      obj['paid'] = row[1]
      obj['pending'] = row[2]
      obj['billName'] = row[3]
      obj['totalAmt'] = str(row[4])
      obj['ownerUsername'] = row[5]
      obj['ownerName'] = row[6]
      obj['dueDate'] = row[7].isoformat()
      obj['groupName'] = row[8]

      try:
         cur.execute("""
            SELECT COUNT(*)
            FROM UserBills
            WHERE billId = %s""", [obj['billId']])
      except MySQLError:
         response['message'] = 'Internal Server Error'
         return json.dumps(response), 500

      col = cur.fetchone()
      obj['numPayers'] = col[0]
      data.append(obj)

   return json.dumps(data), 200

@bills_api.route('/bills/')
def getBills():
   return getUserBills(1)

@bills_api.route('/bills/history/')
def getBillsHistory():
   return getUserBills(0)

@bills_api.route('/bills/pending/')
def getBillsPending():
   response = {}
   data = []

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            U.username,
            U.email,
            U.name,
            U.id,
            U.profilePic,
            B.id,
            B.name,
            G.id,
            G.name
         FROM
            UserBills AS UB
            INNER JOIN Bills AS B ON B.id = UB.billId
            INNER JOIN Users AS U ON U.id = UB.userId
            INNER JOIN Groups AS G ON B.groupId = G.id
         WHERE
            B.owner = (
               SELECT user
               FROM Tokens
               WHERE token = %s
            ) AND
            UB.pending = 1
         """, [request.headers['Authorization']])

      rows = cur.fetchall()
      if not rows:
         return json.dumps(response), 204

      for row in rows:
         obj = {}
         obj['username'] = row[0]
         obj['email'] = row[1]
         obj['userFullname'] = row[2]
         obj['userId'] = row[3]
         img = open(row[4], 'r').read()
         obj['profilePic'] = img.encode('base64')
         obj['billId'] = row[5]
         obj['billName'] = row[6]
         obj['groupId'] = row[7]
         obj['groupName'] = row[8]
         data.append(obj)

   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(data), 200

@bills_api.route('/bill/<int:billId>/')
def getBill(billId):
   data = {}
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      cur.execute("""
         SELECT
            B.name,
            B.totalAmt,
            B.dueDate,
            B.complete,
            U.name,
            U.username,
            U.id,
            G.name
         FROM
            Tokens AS T
            INNER JOIN UserBills AS UB ON UB.userId = T.user
            INNER JOIN Bills AS B ON B.id = UB.billId
            INNER JOIN Users AS U ON B.owner = U.id
            INNER JOIN Groups AS G ON B.groupId = G.id
         WHERE
            billId = %s
            AND token = %s
         """, [billId, request.headers['Authorization']])

      rows = cur.fetchall()
      if not rows:
         return json.dumps(response), 204

      # Should only be one row
      for row in rows:
         data = {}
         data['billName'] = row[0]
         data['totalAmt'] = str(row[1])
         data['dueDate'] = row[2].isoformat()
         data['complete'] = row[3]
         data['ownerName'] = row[4]
         data['ownerUsername'] = row[5]
         data['ownerId'] = row[6]
         data['groupName'] = row[7]

         # Add each individual payer and information about them
         payers = []
         cur.execute("""
            SELECT
               id,
               username,
               email,
               name,
               profilePic,
               paid,
               pending
            FROM
               UserBills AS UB
               INNER JOIN Users AS U ON UB.userId = U.id
            WHERE
               billId = %s
            """, [billId])
         users = cur.fetchall()
         if not users:
            response['message'] = 'Internal Server Error'
            json.dumps(response), 500

         for user in users:
            uObj = {}
            uObj['userId'] = user[0]
            uObj['username'] = user[1]
            uObj['email'] = user[2]
            uObj['name'] = user[3]
            img = open(user[4], 'r').read()
            uObj['profilePic'] = img.encode('base64')
            uObj['paid'] = user[5]
            uObj['pending'] = user[6]
            if data['ownerId'] == uObj['userId']:
               uObj['owner'] = 1
            else:
               uObj['owner'] = 0
            payers.append(uObj)

         data['payers'] = payers
   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   return json.dumps(data), 200

@bills_api.route('/bills/add/', methods = ['POST'])
def addBill():
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

      cur.execute("""
         INSERT INTO Bills VALUES
            (NULL, %s, %s, %s, %s, %s, 0, NOW(), 0)
         """, [req['billName'], req['totalAmt'], userId, req['groupId'],
         req['dueDate']])
      billId = cur.lastrowid

      payers = []
      for payer in req['includedMembers']:
         payers.append((payer, billId, 0, 0))

      cur.executemany("""
         INSERT INTO UserBills (userId, billId, paid, pending)
         VALUES (%s, %s, %s, %s)""", payers)
      db.commit()

   except MySQLError:
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500

   response['billId'] = billId
   return json.dumps(response), 200

@bills_api.route('/bills/delete/<int:billId>/')
def deleteBill(billId):
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      # Check if bill exists and the owner is the requester
      cur.execute("""
         SELECT COUNT(*)
         FROM Bills
         WHERE
            owner = (
               SELECT user
               FROM Tokens
               WHERE token = %s
            ) AND
            id = %s
            AND deleted <> 1
            AND complete <> 1
         """, [request.headers['Authorization'], billId])

      row = cur.fetchone()
      if row[0] == 0:
         return json.dumps(response), 403

      # Make sure there are no payments or pending payments
      cur.execute("""
         SELECT COUNT(*)
         FROM
            Bills AS B
            INNER JOIN UserBills AS UB ON UB.billId = B.id
         WHERE
            B.id = %s
            AND (
               UB.paid = 1
               OR UB.pending = 1
            )
         """, [billId])

      row = cur.fetchone()
      if row[0] > 0:
         return json.dumps(response), 403

      # If everything checks out delete the bill
      cur.execute("""
         UPDATE Bills SET
            deleted = 1
         WHERE id = %s
         """, [billId])
      db.commit()

   except MySQLError:
      db.rollback()
      response['message'] = 'Internal Server Error'
      return json.dumps(response), 500
   return json.dumps(response), 200

@bills_api.route('/bills/pay/<int:billId>/')
def payBill(billId):
   response = {}

   try:
      if validateToken(request.headers['Authorization']) == False:
         response['message'] = "Invalid/expired token."
         return json.dumps(response), 403

      # Check if it is the bill owner who is paying.
      cur.execute("""
         SELECT (
            SELECT id
            FROM
               Users AS U
               INNER JOIN Tokens AS T ON T.user = U.id
            WHERE
               token = %s
         ) = (
            SELECT owner
            FROM Bills
            WHERE id = %s
         )
         """, [request.headers['Authorization'], billId])
      row = cur.fetchone()
      if row[0] == 0:
         cur.execute("""
            UPDATE UserBills
            SET pending = 1
            WHERE
               billId = %s
               AND userId = (
                  SELECT user FROM Tokens WHERE token = %s
               )
            """, [billId, request.headers['Authorization']])
         response['status'] = 'Pending'
      else:
         cur.execute("""
            UPDATE UserBills
            SET paid = 1
            WHERE
               billId = %s
               AND userId = (
                  SELECT user FROM Tokens WHERE token = %s
               )
            """, [billId, request.headers['Authorization']])
         response['status'] = 'Paid'

         cur.execute("""
            SELECT
               COUNT(*)
            FROM
               UserBills
            WHERE
               billId = %s
               AND paid = 0
            """, [req['billId']])

         row = cur.fetchone()
         if row[0] == 0:
            # The bill is complete
            cur.execute("""
               UPDATE Bills
               SET complete = 1
               WHERE id = %s
               """, [req['billId']])

      db.commit()
   except MySQLError:
      response['message'] = 'Internal Server Error'
      db.rollback()
      return json.dumps(response), 500
   return json.dumps(response), 200

@bills_api.route('/bills/accept/', methods = ['POST'])
def acceptPayment():
   response = {}

   if validateToken(request.headers['Authorization']) == False:
      response['message'] = "Invalid/expired token."
      return json.dumps(response), 403

   req = request.get_json(True, True, False)
   if req == None:
      return json.dumps({}), 400

   try:
      # Validate the owner of the bill
      cur.execute("""
         SELECT (
            SELECT id
            FROM
               Users AS U
               INNER JOIN Tokens AS T ON T.user = U.id
            WHERE
               token = %s
         ) = (
            SELECT owner
            FROM Bills
            WHERE id = %s
         )
         """, [request.headers['Authorization'], req['billId']])
      row = cur.fetchone()
      if row[0] == 0:
         response['message'] = "Not permitted to accept bill"
         return json.dumps(response), 403

      # Set paid bit for the user.
      cur.execute("""
         UPDATE UserBills SET
            paid = 1,
            pending = 0
         WHERE
            billId = %s
            AND userId = %s
         """, [req['billId'], req['userId']])
      db.commit()

      cur.execute("""
         SELECT
            COUNT(*)
         FROM
            UserBills
         WHERE
            billId = %s
            AND paid = 0
         """, [req['billId']])

      row = cur.fetchone()
      if row[0] == 0:
         # The bill is complete
         cur.execute("""
            UPDATE Bills
            SET complete = 1
            WHERE id = %s
            """, [req['billId']])
         db.commit()
   except MySQLError:
      response['message'] = 'Internal Server Error'
      db.rollback()
      return json.dumps(response), 500
   return json.dumps(response), 200
