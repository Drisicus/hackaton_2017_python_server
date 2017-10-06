from flask import Flask, render_template
from flask import request
from flask_socketio import SocketIO

import time
import json

import socket
import errno


app = Flask(__name__)
# check to remove
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

if __name__ == '__main__':
    socketio.run(app)



@app.after_request
def after_request(response):
 response.headers.add('Access-Control-Allow-Origin', '*')
 response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
 response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
 return response

available_rooms = 1
fitting_rooms = {1:"busy", 2:"busy", 3:"busy"}
users = []

leaving_user = ""
leaving_room = ""


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/status")
def function():
	response = app.response_class(
        response=buildJson(),
        status=200,
        mimetype='application/json'
    )

	return response


@app.route("/checkstatus")
def function2():
	def eventStream():
		string1 = str(fitting_rooms)
		while True:
			if string1 != str(fitting_rooms):
				#print("----------------------changed")
				string1 = str(fitting_rooms)
				# string data: xxx and final \n\n required
				data_message = "data: " + str(buildJson()) + "\n\n"
				return data_message

	response = app.response_class(
        response=eventStream(),
        status=200,
        mimetype='text/event-stream'
    )
	return response


def buildJson():
	response = []
	for key,val in fitting_rooms.items():
		response.append({"id":key,"status":val})
	return json.dumps(response)

@app.route("/request")
def getRequest():
	global available_rooms
	global fitting_rooms
	global users

	userId = request.args.get("userid")
	print("##\nGetting request from: " + str(userId) + "\n##")
	
	if not userId: 
		return "Error: no userid introduced"

	if available_rooms > 0:
		for room in fitting_rooms:
			if fitting_rooms[room] == "free":
				fitting_rooms[room] = "waiting"
				available_rooms -= 1
				print("##\nuser located in room: " + str(room) + "\n##")
				return str(room)
	
	# add user and ip
	users_ip = {}
	users_ip[userId] = request.remote_addr
	users.append(users_ip)
	return str("0")



@app.route("/enter")
def enter():
	global fitting_rooms
	roomId = request.args.get("roomid")

	if not roomId:
		return "Error: no roomid introduced"

	if fitting_rooms[int(roomId)] == "waiting":
		fitting_rooms[int(roomId)] = "busy"
	else:
		print("##\nError: room " + str(roomId) + " not in waiting status\n##")
		return "Error: room " + str(roomId) + " not in waiting status"

	return "user has enter"


@app.route("/leave")
def leaveRoom():
	global available_rooms
	global fitting_rooms
	global users
	global leaving_user
	global leaving_room

	roomId = request.args.get("roomid")
	
	if not roomId or int(roomId) not in fitting_rooms.keys():
		return "Error: no roomid introduced"

	# no waiting users
	if not users:
		fitting_rooms[int(roomId)] = "free"
		available_rooms += 1
		print("##\nNo users waiting, room " + str(roomId) + " available\n##")
	else:
		user = next(iter(users or []), None)
		del users[0]

		fitting_rooms[int(roomId)] = "waiting"
		

		for key, value in user.items():

			print("##\nUser " + str(key) + " sent to room " + str(roomId) + "\n##")

			leaving_user = key
			leaving_room = str(roomId)

			print(leaving_user + " " + leaving_room)
			
			if key == "aparatito":
				socketToUsers = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				port = 6666

				try:
					socketToUsers.connect((value,port)) 
					socketToUsers.send(roomId.encode())
					socketToUsers.close()
				except socket.error,v:
					#errorcode = v[0]
	    			#if errorcode == errno.ECONNREFUSED:
					print "Connection Refused"
					#return "Connection Refused"
			
			
	return "leave ok"

@app.route("/queue")
def displayQueue():
	return str(users)

@app.route("/checkfree")
def checkfree():
	def eventStream():
		string1 = leaving_user
		while True:
			if string1 != leaving_user:
				string1 = leaving_user

				json_info = json.dumps({"user":leaving_user,"room":leaving_room})
				data_message = "data: " + json_info + "\n\n"
				return data_message

	response = app.response_class(
        response=eventStream(),
        status=200,
        mimetype='text/event-stream'
    )
	return response
