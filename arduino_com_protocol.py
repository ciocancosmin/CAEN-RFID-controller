import serial
import time
import os
import pymysql

def create_serial(usb_port,usb_baudrate):
	serial_object = serial.Serial(
			port=usb_port,
			baudrate=usb_baudrate,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=0.2
		)

	return serial_object

def arduino_send_command(arduino_controller,command):
	command = command.encode()
	arduino_controller.write( command )

def parse_card(input_string):
	if(input_string[:3] == "ID:"):
		target_string_split = input_string.split(":")
		os.environ['id_card'] = target_string_split[1].strip()
		os.environ['timer_time'] = str( time.time() )
		return 1
	else:
		return 0

def automatic_id_card_reset(reset_time):
	arduino_read_var = int( os.environ['arduino_read'] )
	while arduino_read_var:
		if( time.time() - float( os.environ['timer_time'] ) > reset_time ):
			os.environ['id_card'] = "not_defined"
			os.environ['timer_time'] = str( time.time() )
		arduino_read_var = int( os.environ['arduino_read'] )

def print_id_card():
	arduino_read_var = int( os.environ['arduino_read'] )
	while arduino_read_var:
		print( os.environ['id_card'] )
		time.sleep(1)
		arduino_read_var = int( os.environ['arduino_read'] )

def parse_arduino_input( command, arduino_controller ):
	command = command.strip()
	if( command == "CM_CLOSE" ):
		os.environ['door_state'] = "closed"
		print("door is closed")
	if( command == "CM_OPEN" ):
		os.environ['door_state'] = "opened"
		print("door is opened")
		arduino_send_command(arduino_controller,"blabla")

def check_to_open_door(card_id,arduino_controller):
	if( os.environ['can_open_door'] == "True" and os.environ['door_state'] == "closed" ):
		db = pymysql.connect("localhost","admin","admin","key" )
		cursor = db.cursor()
		sql = "SELECT card FROM users WHERE card='"+card_id+"' "
		cursor.execute(sql)
		results = []
		results = cursor.fetchall()
		ok_1 = 1
		#print( os.environ['scan_save_lock'] + " " + os.environ['last_card_read'] )
		if( os.environ['scan_save_lock'] == "True" and os.environ['last_card_read'] != card_id ):
			ok_1 = 0
		if( len(results) > 0 and (ok_1 == 1)  ):
			#open door
			print("deschide usa")
			arduino_send_command(arduino_controller,"PGM1_temp")
			
			os.environ['last_card_read'] = "not_defined"
			os.environ['scan_save_lock'] = "False"

			os.environ['id_card'] = "not_defined"
			os.environ['timer_time'] = str( time.time() )

def check_master_card(card_id,arduino_controller):
	db = pymysql.connect("localhost","admin","admin","key" )
	cursor = db.cursor()
	sql_2 = "SELECT value1 FROM keys_config WHERE param1='master_card' "
	cursor.execute(sql_2)
	results_2 = cursor.fetchall()
	master_card = ""
	if(len(results_2) > 0):
		master_card = results_2[0][0].strip()
		print("Mastercard: "+master_card)
	if(master_card == card_id):
		arduino_send_command(arduino_controller,"PGM1_temp")
		return 1
	else:
		return 0

def read_from_arduino(arduino_controller):
	arduino_read_var = int( os.environ['arduino_read'] )
	while arduino_read_var:
		bytes_from_arduino = arduino_controller.readline()
		arduino_input_read = ""
		if( len(bytes_from_arduino) > 0 ):
			for b in bytes_from_arduino:
				arduino_input_read += chr(b)
			if( int( os.environ['arduino_print'] ) ):
				print(arduino_input_read)
			if( parse_card(arduino_input_read) ):
				print("Card ID " + os.environ['id_card'] + " parsed")
				if( check_master_card(os.environ['id_card'],arduino_controller) ):
					do_nothing = 0
				else:
					check_to_open_door(os.environ['id_card'],arduino_controller)
			else:
				parse_arduino_input( arduino_input_read, arduino_controller )
		arduino_read_var = int( os.environ['arduino_read'] )
	print("Printing from arduino stopped")

def read_arduino_2():
	read_buffer = []
	while ( len(read_buffer) == 0 ):
		read_buffer = s.readline()
	return read_buffer

def wait_for_arduino_init():
	time.sleep(3)

def create_arduino_controller(usb_port,usb_baudrate):
	s = create_serial(usb_port,usb_baudrate)
	wait_for_arduino_init()
	return s

def send_sock_message(conn,content,content_length):
	content = str(content)
	if(len(content) < content_length):
		hw = content_length - len(content) + 1
		t = hw*" "
		content += t
	conn.sendall(content.encode("utf-8"))