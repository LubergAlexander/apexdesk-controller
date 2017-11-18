from flask import Flask
from apexdesk import ApexDesk
from threading import Thread

app = Flask(__name__)
desk = ApexDesk()


@app.route('/A')
def A():
  desk.preset_a()
  return "Changed preset to A"


@app.route('/B')
def B():
  desk.preset_b()
  return "Changed preset to B"


@app.route('/height')
def height():
  return desk.desk_height


if __name__ == '__main__':
  flask = Thread(target=app.run, args=('0.0.0.0', 80))
  flask.start()
  desk.start()
