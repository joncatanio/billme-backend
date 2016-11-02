# File: app.py
# Author: Jon Catanio
# Description: Main Flask file.

from flask import Flask

app = Flask(__name__)

@app.route("/")
def main():
   return {"BillMe"}, 200

if __name__ == "__main__":
   app.debug = True
   app.run()
