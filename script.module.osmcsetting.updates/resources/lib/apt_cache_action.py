''' This script is run as root by the osmc update module. '''

import apt
import socket
import sys
from datetime import datetime

t = datetime

class Logger(object):
	def __init__(self, filename="Default.log"):
		self.terminal = sys.stdout
		self.log = open(filename, "a")

	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)

try:
	sys.stdout = Logger("/home/kubkev/test.txt")
except:
	pass


class Main(object):

	def __init__(self, action):

		print '==================================================================='
		print '%s %s running' % (t.now(), 'apt_cache_action.py')

		self.action = action

		self.address = '/var/tmp/osmc.settings.update.sockfile'

		self.cache = apt.Cache()

		self.action_to_method = {
								'update': self.update,
								'commit' : self.commit,

								}

		try:
			self.act()
		except Exception as e:
			print '%s %s exception occurred' % (t.now(), 'apt_cache_action.py')
			print e

		self.respond()

		print '%s %s exiting' % (t.now(), 'apt_cache_action.py')
		print '==================================================================='


	def respond(self):
		print '%s %s sending response' % (t.now(), 'apt_cache_action.py')
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.connect(self.address)
		sock.sendall('apt_cache %s complete' % self.action) 
		sock.close()
		print '%s %s response sent' % (t.now(), 'apt_cache_action.py')


	def act(self):

		action = self.action_to_method.get(self.action, False)
		if action:
			action()


	def update(self):
		print '%s %s updating cache' % (t.now(), 'apt_cache_action.py')
		self.cache.update()
		print '%s %s cache updated' % (t.now(), 'apt_cache_action.py')


	def commit(self):
		print '%s %s upgrading all packages' % (t.now(), 'apt_cache_action.py')
		self.cache.upgrade()
		print '%s %s committing cache' % (t.now(), 'apt_cache_action.py')
		self.cache.commit()
		print '%s %s cache committed' % (t.now(), 'apt_cache_action.py')


if __name__ == "__main__":

	if len(sys.argv) > 1:

		action = sys.argv[1]

		m = Main(action)

		del m