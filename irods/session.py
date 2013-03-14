import socket 
import hashlib
import struct
from message import iRODSMessage

class iRODSSession(object):
	def __init__(self, host=None, port=None, user=None, zone=None, password=None):
		self.host = host
		self.port = port
		self.user = user
		self.zone = zone
		self.password = password	
		self.socket = None
		self.authenticated = False
		self._connect()

	def _send(self, message):
		return self.socket.send(message.pack())

	def _recv(self):
		return iRODSMessage.recv(self.socket)

	def _connect(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.host, self.port))
		main_message = "<StartupPack_PI><irodsProt>0</irodsProt><connectCnt>0</connectCnt><proxyUser>rods</proxyUser><proxyRcatZone>tempZone</proxyRcatZone><clientUser>rods</clientUser><clientRcatZone>tempZone</clientRcatZone><relVersion>rods3.2</relVersion><apiVersion>d</apiVersion><option></option></StartupPack_PI>"
		msg_header = "<MsgHeader_PI><type>RODS_CONNECT</type><msgLen>%d</msgLen><errorLen>0</errorLen><bsLen>0</bsLen><intInfo>0</intInfo></MsgHeader_PI>" % len(main_message)
		msg_header_length = struct.pack(">i", len(msg_header))
		msg = msg_header_length + msg_header + main_message
		sent = self.socket.send(msg)
		version_msg = self._recv()

	def _login(self):
		# authenticate
		auth_req = iRODSMessage(type='RODS_API_REQ', int_info=703)
		self._send(auth_req)

		# challenge
		challenge = self._recv()
		response_len = 16
		max_pwd_len = 50
		padded_pwd = struct.pack("50s", "rods")
		m = hashlib.md5()
		m.update(challenge.msg)
		m.update(padded_pwd)
		encoded_pwd = m.digest()

		encoded_pwd = encoded_pwd.replace('\x00', '\x01')
		pwd_msg = encoded_pwd + 'rods' + '\x00'
		pwd_request = iRODSMessage(type='RODS_API_REQ', int_info=704, msg=pwd_msg)
		self._send(pwd_request)

		auth_response = self._recv()
		if auth_response.error:
			raise Exception("Unsuccessful login attempt")
		else:
			self.authenticated = True
			print "Successful login"

	def disconnect(self):
		disconnect_msg = iRODSMessage(type='RODS_DISCONNECT')
		self._send(disconnect_msg)
		self.socket.close()