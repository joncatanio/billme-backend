# File: app.py
# Author: Jon Catanio
# Description: Main Flask file.

from flask import Flask

# Import blueprints
from register import register_api
from login import login_api
from bills import bills_api
from groups import groups_api
from account import account_api

app = Flask(__name__)

# Register blueprints
app.register_blueprint(register_api)
app.register_blueprint(login_api)
app.register_blueprint(bills_api)
app.register_blueprint(groups_api)
app.register_blueprint(account_api)

@app.route("/")
def main():
   return "BillMe", 200

if __name__ == "__main__":
   app.debug = True
   app.run()
