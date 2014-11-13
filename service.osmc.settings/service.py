#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2014 KodeKarnage

 This Program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2, or (at your option)
 any later version.

 This Program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with XBMC; see the file COPYING.  If not, write to
 the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
 http://www.gnu.org/copyleft/gpl.html
'''

# Standard modules
import os
import shutil
import time
import re
import sys
import json
import Queue
import os
import threading

# XBMC modules
import xbmc
import xbmcaddon
import xbmcgui

# Custom modules
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources','lib')))
import walkthru
import settings
import comms


__addon__        = xbmcaddon.Addon()
__addonid__      = __addon__.getAddonInfo('id')
__setting__      = __addon__.getSetting

def log(message):
	xbmc.log(str(message))

class Main(object):


	def __init__(self):

		# queue for communication with the comm and Main
		self.parent_queue = Queue.Queue()

		# create socket, listen for comms
		self.listener = comms.communicator(self.parent_queue)
		self.listener.start()

		# daemon
		self._daemon()


	def _daemon(self):

		log('daemon started')

		while not xbmc.abortRequested:

			if not self.parent_queue.empty():

				response = self.parent_queue.get()

				log('response : %s' % response)

				self.parent_queue.task_done()
		
				if response == 'open':

					self.open_gui()

			xbmc.sleep(1000)

			log('blip!')

		self.listener.stop()


	def open_gui(self):

		log('firstrun? %s' % __setting__('firstrun'))
		
		if __setting__('firstrun') == 'true':

			log('Opening walkthru GUI')

		gui = walkthru

			# __addon__.setSetting('firstrun', 'false')

		# else:
		# 	gui = settings.gui()

		threading.Thread(target=gui.open()).start()


if __name__ == "__main__":

	Main()

	del Main

	log('Exiting OSMC Settings')



