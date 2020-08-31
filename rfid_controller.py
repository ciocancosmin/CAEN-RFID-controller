import serial


'''
	
	<--->
	VALUE COMMENTS

	MAX_ANTENNA_POWER = 1400mW
	<--->

	<--->
	SET PROTOCOL VALUES

	0x00 = ISO18000-6B
	0x01 = EPCC1G1
	0x02 = ISO18000-6A
	0x03 = EPCC1G2
	<--->

'''
class RFID_Controller:
	usb_port = ""
	baudrate = 0
	serial_object = None
	success_code_hex_array = [0x00,0x00,0x00,0x08,0x00,0x02,0x00,0x00]
	tag_type_array = [0x00,0x00,0x00,0x08,0x00,0x0f]
	read_bytes_nr = 15000
	def __init__(self,usb_port,baudrate):
		self.usb_port = usb_port
		self.baudrate = baudrate
		self.serial_object = serial.Serial(
			port=self.usb_port,
			baudrate=self.baudrate,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=3.0
		)

	def build_header(self,size):
		header_hex_array = [0x80,0x01,0x00,0x42,0x00,0x00,0x53,0x58]
		size_hex_string = str( hex(size) )
		if(len(size_hex_string) == 5):
			header_hex_array.append( int("0x"+size_hex_string[2],0) )
			header_hex_array.append( int("0x"+size_hex_string[3:],0) )
		elif(len(size_hex_string) == 6):
			header_hex_array.append( int("0x"+size_hex_string[2:4],0) )
			header_hex_array.append( int("0x"+size_hex_string[4:],0) )
		else:
			header_hex_array.append( int("0x00",0) )
			header_hex_array.append( int("0x"+size_hex_string[2:],0) )
		return header_hex_array

	def check_equal_arrays(self,array_1,array_2):
		if(len(array_1) == len(array_2)):
			for x in range(len(array_1)):
				if(array_1[x] != array_2[x]):
					return 0
		else:
			return 0

		return 1

	def command_header(self,command_nr):
		command_avp_array = [0x00,0x00,0x00,0x08,0x00,0x01]
		command_avp_array.append( int('0x00',0) )
		command_avp_array.append( int(command_nr,0) )
		return command_avp_array 

	def number_to_hex_array(self,nr,nr_of_bytes):
		return_hex_array = []
		hex_nr = hex(nr)
		hex_nr = hex_nr[2:]
		total_nr_of_zeros = nr_of_bytes*2 - len(hex_nr)
		hex_nr = total_nr_of_zeros * '0' + hex_nr
		for x in range(0,len(hex_nr),2):
			return_hex_array.append( '0x' + hex_nr[x:x+2] )
		return return_hex_array

	def hex_string_to_hex_array(self,hex_string,nr_of_bytes):
		return_hex_array = []
		hex_nr = hex_string[2:]
		total_nr_of_zeros = nr_of_bytes*2 - len(hex_nr)
		hex_nr = total_nr_of_zeros * '0' + hex_nr
		for x in range(0,len(hex_nr),2):
			return_hex_array.append( '0x' + hex_nr[x:x+2] )
		return return_hex_array

	def hex_array_to_int(self,hex_array):
		hex_string = ""
		for x in hex_array:
			if(x != 0):
				hex_string += hex(x)[2:]
		return int("0x"+hex_string,0)

	def string_to_hex(self,string):
		return ( "0x"+string.encode("utf-8").hex() + "00" )

	def return_bytes_array(self,target_array):
		return [int(x,0) for x in target_array]

	def build_avp_array(self,attribute_type,attribute_value,nr_of_bytes_attribute_value):
		attribute_type_array = self.return_bytes_array( self.hex_string_to_hex_array(attribute_type,2) )
		attribute_value_array = self.return_bytes_array( self.hex_string_to_hex_array(attribute_value,nr_of_bytes_attribute_value) )
		return_avp_array = [0x00,0x00]
		return_avp_array += self.return_bytes_array( self.number_to_hex_array( 4 + len(attribute_type_array) + len(attribute_value_array) , 2) )
		return_avp_array += attribute_type_array
		return_avp_array += attribute_value_array
		return return_avp_array

	def set_antenna_power(self,power):
		to_send = []
		avp_power = [0x00,0x00,0x00,0x0a,0x00,0x96]
		avp_power += [int(x,0) for x in self.number_to_hex_array(power,4) ]
		to_send = self.command_header('0x64') + avp_power
		total_message_length = 10 + len(to_send)
		to_send = self.build_header(total_message_length) + to_send
		self.serial_object.write( to_send )
		return_result_array = self.serial_object.read(1000)
		if( self.check_equal_arrays(self.success_code_hex_array,return_result_array[-8:]) ):
			return 1
		else:
			return 0

	def set_antenna_protocol(self,protocol):
		to_send = []
		to_send += self.command_header('0x74')
		to_send += self.build_avp_array('0x54',protocol,4)
		to_send = self.build_header( 10 + len(to_send) ) + to_send
		self.serial_object.write( to_send )
		response_array = self.serial_object.read( self.read_bytes_nr )
		return self.check_equal_arrays( self.success_code_hex_array , response_array[-8:] )

	def get_inventory(self,source=-1):
		to_send = []
		to_send += self.command_header('0x13')
		if(source != -1):
			source_code = "Source_"+str(source)
			attribute_value_hex = self.string_to_hex( source_code )
			to_send += self.build_avp_array( '0xfb', attribute_value_hex , int( ( len(attribute_value_hex) - 2 ) / 2 ) )
		to_send = self.build_header( 10 + len(to_send) ) + to_send
		self.serial_object.write( to_send )
		response_array = self.serial_object.read( self.read_bytes_nr )
		if( self.check_equal_arrays( self.success_code_hex_array , response_array[-8:] ) ):
			response_array = response_array[10:]
			response_array = response_array[:-8]
			x = 0
			tags_array = []
			while ( x < ( len(response_array) - len(self.tag_type_array) ) ):
				if( self.check_equal_arrays( response_array[x:x+len(self.tag_type_array)] , self.tag_type_array ) ):
					x += 6
					tag_id_length = int( "0x" + hex(response_array[x])[2:] + hex(response_array[x+1])[2:] ,0)
					x += 2
					x += 6
					tag_id_string = ""
					for y in range(tag_id_length):
						#print(response_array[x])
						short_hex_string = hex( response_array[x] )[2:]
						if( len( short_hex_string ) == 1):
							short_hex_string = "0" + short_hex_string
						tag_id_string += short_hex_string
						x += 1
					tag_id_string = "E"+tag_id_string
					tags_array.append( tag_id_string )
				else:
					x += 1
			return tags_array
		else:
			return -1

	def sift_array(self,big_array):
		sifted_array = []
		for x in big_array:
			ok = 1
			for y in sifted_array:
				if(x == y):
					ok = 0
					break
			if(ok):
				sifted_array.append(x)
		return sifted_array

	def get_all_inventory(self,sources_nr=3):
		q = []
		for x in range(sources_nr):
			q2 = self.get_inventory(x)
			if(q2 != -1):
				q += q2
		return self.sift_array( q )

	def get_all_inventory_multiple_times(self,times,sources=3):
		q = []
		for x in range(times):
			q += self.get_all_inventory(sources)
		return self.sift_array( q )

	def get_antenna_power(self):
		to_send = []
		avp_to_send = self.command_header('0x73')
		to_send += self.build_header( len(avp_to_send) + 10 )
		to_send += avp_to_send
		self.serial_object.write( to_send )
		response_array = self.serial_object.read(1000)
		if( self.check_equal_arrays( self.success_code_hex_array,response_array[-8:] ) ):
			response_array = response_array[10:]
			response_array = response_array[:-8]
			response_array = response_array[8:]
			response_array = response_array[6:]
			antenna_power_int = self.hex_array_to_int(response_array)
			return antenna_power_int
		else:
			return -1

	def get_antenna_protocol(self):
		to_send = []
		to_send += self.command_header('0x79')
		to_send = self.build_header( 10 + len(to_send) ) + to_send
		self.serial_object.write( to_send )
		response_array = self.serial_object.read(self.read_bytes_nr)
		if( self.check_equal_arrays( self.success_code_hex_array,response_array[-8:] ) ):
			response_array = response_array[:-8]
			response_array = response_array[10:]
			response_array = response_array[8:]
			response_array = response_array[6:]
			return_protocol = hex( self.hex_array_to_int(response_array) )
			return return_protocol
		else:
			return -1


#c = RFID_Controller("/dev/ttyUSB1",115200)

#print( c.get_all_inventory_multiple_times(5) )

#print( c.number_to_hex_array(1000,4) )

#print( c.build_avp_array('0x96','0x3e8',4) )

#q = c.set_antenna_protocol('0x03')

#print( c.set_antenna_power(500) )

'''
q = c.get_inventory(0)
print(len(q))
print(q)
q = c.get_inventory(1)
print(len(q))
print(q)
q = c.get_inventory(2)
print(len(q))
print(q)
'''

#print( c.get_antenna_power() )

#for x in q:
#	print( hex(x) )

#print( c.hex_string_to_hex_array(c.string_to_hex("Source_0"),9) )

#print( c.command_header('0x7c') )

#success_code_hex_array = [0x00,0x00,0x00,0x08,0x00,0x02,0x00,0x00]

#print( check_equal_arrays( success_code_hex_array,[0x00,0x00,0x00,0x08,0x00,0x02,0x00,0x00] ) )


