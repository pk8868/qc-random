from ast import parse
from logging import exception
from flask import *
import qcrandom
import os

app = Flask(__name__)


@app.route("/", methods=['GET'])
def home():
    return render_template("index.html", result="")

@app.route('/', methods=['POST'])
def GenerateRandomNumber():
    left = int(request.form['left'])
    right = int(request.form['right'])
    try:
        request.form['intiger']
        randnumber=int(qcrandom.QCRandom(left,right))
    except Exception:
        randnumber=qcrandom.QCRandom(left,right)
    return render_template("result.html", number=randnumber)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
