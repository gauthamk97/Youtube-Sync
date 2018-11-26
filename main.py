from flask import Flask, url_for, render_template, jsonify, make_response, request
from flask_socketio import SocketIO
from flaskext.mysql import MySQL
from pymysql.err import IntegrityError

app = Flask(__name__)
socketIO = SocketIO(app)

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'idk'
app.config['MYSQL_DATABASE_DB'] = 'youtube_sync'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql = MySQL(app)

@app.route('/')
def loginPage():
    return render_template('index.html')

@app.route('/watch/<roomID>')
def watchPage(roomID):
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT videoID FROM open_rooms WHERE roomID={}".format(roomID))
    data = cursor.fetchone()
    videoID = data[0]
    return render_template('watch.html', videoID = videoID)

@app.route('/room/check')
def checkIfRoomExists():
    conn = mysql.connect()
    cursor = conn.cursor()
    roomID = request.args.get('roomID')

    if roomID is None:
        return make_response(jsonify(
            response="Parameters missing",
            status=401
        ),401)

    cursor.execute("SELECT * FROM open_rooms WHERE RoomID='{}'".format(roomID))
    data = cursor.fetchone()

    if bool(data):
        return make_response(jsonify(
            response="Room exists",
            status=200
        ), 200)
    else:
        return make_response(jsonify(
            response="Room doesn't exist",
            status=500
        ), 500)

@app.route('/room/add')
def addNewRoom():
    conn = mysql.connect()
    cursor = conn.cursor()
    videoID = request.args.get('videoID')

    if videoID is None:
        return make_response(jsonify(
            response="Parameters missing",
            status=401
        ),401)

    cursor.execute("SELECT MAX(roomID) FROM open_rooms")
    data = cursor.fetchall()
    maxValue = data[0][0]

    if not bool(maxValue):
        # No rooms exist
        roomID = 1000
    else:
        roomID = int(maxValue)+1

    try:
        cursor.execute("INSERT INTO open_rooms VALUES ('{}', '{}');".format(roomID, videoID))
        conn.commit()
    except IntegrityError:
        # Should never happen since roomID = max(old room IDs)+1
        return make_response(jsonify(
            response="Room already exists",
            status=500
        ),500)

    return jsonify(
        response="Room successfully created",
        roomID=roomID,
        status=200
    )

@socketIO.on('my event')
def receivedMessage(json, methods=['POST', 'GET']):
    print(json)
    socketIO.emit('Receieved message')