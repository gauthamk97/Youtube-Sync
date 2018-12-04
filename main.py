from flask import Flask, url_for, render_template, jsonify, make_response, request, session, redirect
from flask_socketio import SocketIO, join_room, leave_room, close_room, rooms
from flaskext.mysql import MySQL
from pymysql.err import IntegrityError

app = Flask(__name__)

app.config['SECRET_KEY'] = 'thiscanbeanythinglol'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'idk'
app.config['MYSQL_DATABASE_DB'] = 'youtube_sync'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL(app)
socketIO = SocketIO(app)

@app.route('/')
def homePage():
    return render_template('index.html')

@app.route('/login')
def login():
    username = request.args.get('username')
    if username is None:
        return make_response(jsonify(
            response="Missing username parameter"
        ), 401)
    else:
        session['username'] = username
        return make_response(jsonify(
            response="Session successfully created"
        ), 200)

@app.route('/logout')
def logout():
    # Clear session if it exists
    session.pop('username', None)
    if 'username' not in session:
        return redirect(url_for('homePage'))

@app.route('/room/add')
def addNewRoom():
    # Session Check
    if 'username' not in session:
        return redirect(url_for('homePage'))

    conn = mysql.connect()
    cursor = conn.cursor()
    videoID = request.args.get('videoID')

    if videoID is None:
        return make_response(jsonify(
            response="Parameters missing",
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
        ),500)

    return make_response(jsonify(
        response="Room successfully created",
        roomID=roomID,
    ), 200)

@app.route('/room/check')
def checkIfRoomExists():
    # Session Check
    if 'username' not in session:
        return redirect(url_for('homePage'))

    conn = mysql.connect()
    cursor = conn.cursor()
    roomID = request.args.get('roomID')

    if roomID is None:
        return make_response(jsonify(
            response="Parameters missing",
        ),401)

    cursor.execute("SELECT * FROM open_rooms WHERE RoomID='{}'".format(roomID))
    data = cursor.fetchone()

    if bool(data):
        return make_response(jsonify(
            response="Room exists",
        ), 200)
    else:
        return make_response(jsonify(
            response="Room doesn't exist",
        ), 500)

@app.route('/watch/<roomID>')
def watchPage(roomID):
    # Session Check
    if 'username' not in session:
        return redirect(url_for('homePage'))
    
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT videoID FROM open_rooms WHERE roomID={}".format(roomID))
    data = cursor.fetchone()
    videoID = data[0]
    return render_template('watch.html', videoID = videoID, roomID = roomID, username = session['username'])

@socketIO.on('connect')
def connection():
    print("Received connection : {}".format(request.sid))

@socketIO.on('join')
def joinRoom(data):
    print('Received for join : '+ str(data))
    room = data['room']
    newUser = session['username']
    join_room(room)
    socketIO.emit('memberAdd', newUser, room=room)

@socketIO.on('leave')
def leaveRoom(data):
    print('Received for leave : '+ str(data))
    room = data['room']
    leavingUser = session['username']
    leave_room(room)
    socketIO.emit('memberLeave', leavingUser, room = room)

@socketIO.on('message')
def receivedMessage(data):
    print("Received message : {}".format(data))
    username = session['username']
    msg = data['message']
    room = data['room']
    socketIO.emit(
        'message',
        {'username': username,'message': msg},
        room = room,
        include_self = False
    )

# Still to implementing closing of rooms
# Should also remove entry from database when a room is closed
def closeRoom(room):
    close_room(room)

@socketIO.on('disconnect')
def test_disconnect():
    forceClientLeaveAllRooms()
    print('Client Disconnected : ', request.sid)

@socketIO.on('leaveAllRooms')
def forceClientLeaveAllRooms():
    for room in rooms(request.sid):
        print('{} leaving room {}'.format(request.sid, room))
        leave_room(room, sid=request.sid)
        leavingUser = session['username']
        socketIO.emit('memberLeave', leavingUser, room = room)

# This seems to be pointless, it works without this anyways
# if __name__ == '__main__':
#     socketIO.run(app)