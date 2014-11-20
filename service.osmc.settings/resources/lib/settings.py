# XBMC modules
import xbmc
import xbmcgui
import xbmcaddon

# STANDARD library modules
import ast
import datetime
import json
import os
import pickle
import Queue
import select
import socket
import threading
import time
import sys
path = xbmcaddon.Addon().getAddonInfo('path')
lib = os.path.join(path, 'resources','lib')
media = os.path.join(path, 'resources','skins','Default','media')
sys.path.append(xbmc.translatePath(lib))



def log(message):
	xbmc.log(str(message))

class walkthru_gui(xbmcgui.WindowXMLDialog):

	def __init__(self, strXMLname, strFallbackPath, strDefaultName):

		self.nine_icons = [ 'square.png',
							'up.png',
							'circle.png',
							'left.png',
							'sub.png',
							'right.png',
							'lock.png',
							'down.png',
							'key.png'
							]

		pass

	def onInit(self):

		self.hdg = self.getControl(110)
		self.hdg.setLabel('Exit')
		self.hdg.setVisible(True)

		self.panel = self.getControl(52)

		for icon in self.nine_icons:

			icon_path = os.path.join(media, icon)

			self.tmp = xbmcgui.ListItem(label=icon, label2='', thumbnailImage=icon_path)
			self.panel.addItem(self.tmp)

	def onClick(self, controlID):

		if controlID == 110:
			self.close()


def open():

	__addon__        = xbmcaddon.Addon()
	scriptPath       = __addon__.getAddonInfo('path')
	xmlfile = 'settings_main.xml'

	GUI = walkthru_gui(xmlfile, scriptPath, 'Default')

	GUI.doModal()

	log('Exiting GUI')

	del GUI


