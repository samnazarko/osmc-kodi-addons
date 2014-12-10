# Standard modules
import socket
import threading
import os

# XBMC modules
import xbmc
import xbmcaddon
import xbmcgui

def log(message):
	xbmc.log(str(message))

class communicator(threading.Thread):

	def __init__(self, parent_queue):

		# queue back to parent
		self.parent_queue = parent_queue

		# not sure I need this, but oh well
		#self.wait_evt = threading.Event()

		threading.Thread.__init__(self)

		self.daemon = True

		# create the listening socket, it creates new connections when connected to
		self.address = '/var/tmp/osmc.settings.sockfile'

		if os.path.exists(self.address):
			os.remove(self.address)

		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

		# allows the address to be reused (helpful with testing)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(self.address)
		self.sock.listen(1)
		
		self.stopped = False


	def stop(self):
		''' Orderly shutdown of the socket, sends message to run loop
			to exit. '''

		try:

			self.stopped = True
				
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			sock.connect(self.address)
			sock.send('exit')
			sock.close()
			self.sock.close()
				
		except Exception, e:

			log('Comms error trying to stop: {}'.format(e))


	def run(self):

		log('Comms started')

		while not xbmc.abortRequested and not self.stopped:

			# wait here for a connection
			conn, addr = self.sock.accept()

			log(conn)
			log(addr)

			# turn off blocking for this temporary connection
			# this will allow the loop to collect all parts of the message
			conn.setblocking(0)

			passed = False
			total_wait = 0
			wait = 5

			while not xbmc.abortRequested and not passed and total_wait < 2500:
				try:
					data = conn.recv(8192)
					passed = True
				except:
					total_wait += wait
					xbmc.sleep(5)

			if not passed:
				log('Connection failed to collect data.')
				break

			log('data = %s' % data)

			# if the message is to stop, then kill the loop
			if data == 'exit':
				self.stopped = True
				conn.close()
				break

			# send the data to Main for it to process
			self.parent_queue.put(data)

			# # wait 3 seconds for a response from Main
			# try:
			# 	response = self.from_Parent_queue.get(True, 3)

			# 	# serialise dict for transfer back over the connection
			# 	serial_response = pickle.dumps(response)

			# 	# send the response back
			# 	conn.send(serial_response)

			# 	self.log('Comms sent response: ' + str(serial_response)[:50])

			# except Queue.Empty:
			# 	# if the queue is empty, then send back a response saying so
			# 	log('Main took too long to respond.')
			# 	self.conn.send('Service Timeout')

			# close the connection
			conn.close()
