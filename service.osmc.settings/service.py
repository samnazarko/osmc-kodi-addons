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

		# the gui is created and stored in memory for quick access
		# after a few hours, the gui should be removed from memory
		self.stored_gui = settings.OSMCGui()
		self.gui_last_accessed = datetime.now()
		self.skip_check = True

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

					self.open_gui(queue=self.parent_queue)

				elif response == 'refresh_gui':

					# if the gui calls for its own refresh, then delete the existing one and open a new instance

					del self.stored_gui

					self.open_gui(queue=self.parent_queue)

			xbmc.sleep(1000)

			log('blip!')

			# THIS PART MAY NOT BE NEEDED, BUT IS INCLUDED HERE ANYWAY FOR TESTING PURPOSES
			# if the gui was last accessed more than four hours
			if not self.skip_check and (datetime.now() - self.gui_last_accessed).total_seconds() > 14400:

				self.skip_check = True

				del self.stored_gui

		self.listener.stop()


	def open_gui(self):

		log('firstrun? %s' % __setting__('firstrun'))
		
		if __setting__('firstrun') == 'true':

			log('Opening walkthru GUI')

		else:

			log('Opening OSMC settings GUI')

			try:
				# try opening the gui
				threading.Thread(target=self.stored_gui.open()).start()
				self.gui_last_accessed = datetime.now()
				self.skip_check = False

			except:
				# if that doesnt work then it is probably because the gui was too old and has been deleted
				# so recreate the gui and open it

				self.stored_gui = settings.OSMCGui()
				self.gui_last_accessed = datetime.now()
				self.skip_check = False

				threading.Thread(target=self.stored_gui.open()).start()


if __name__ == "__main__":

	Main()

	del Main

	log('Exiting OSMC Settings')



