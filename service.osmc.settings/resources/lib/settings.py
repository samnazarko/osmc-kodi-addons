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


def json_query(query):

	print 'heeere'

	xbmc_request = json.dumps(query)
	raw = xbmc.executeJSONRPC(xbmc_request)
	clean = unicode(raw, 'utf-8', errors='ignore')
	response = json.loads(clean)
	result = response.get('result', response)

	return result

all_addons = {  "jsonrpc"    : "2.0",
				"method"     : "Addons.GetAddons",
				"params"     : {
							    "enabled": "all",
							    "properties": 
											["thumbnail", "enabled"]
							   },
				"id"         : 1 }


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

		pass

		# self.hdg = self.getControl(110)
		# self.hdg.setLabel('Exit')
		# self.hdg.setVisible(True)

		# self.panel = self.getControl(52)

		# for icon in self.nine_icons:

		# 	icon_path = os.path.join(media, icon)

		# 	self.tmp = xbmcgui.ListItem(label=icon, label2='', thumbnailImage=icon_path)
		# 	self.panel.addItem(self.tmp)

	def onClick(self, controlID):

		if controlID == 105:
			self.close()


def open():

	__addon__        = xbmcaddon.Addon()
	scriptPath       = __addon__.getAddonInfo('path')
	xmlfile = 'settings_main.xml'
	xmlfile = 'settings_gui.xml'

	GUI = walkthru_gui(xmlfile, scriptPath, 'Default')

	test = xbmcaddon.Addon('script.module.osmcsetting.dummy')

	test.openSettings()

	# THIS WILL NOT WORK WITH MODULES

	# get all addons
	addon_list = json_query(all_addons)

	addons = addon_list.get('addons',{})

	# find all osmc setting addons
	# get the addons names and icons
	for addon in addons:
		log(addon.get('addonid',''))
		if 'script.module.osmcsetting.' in addon.get('addonid',''):
			log(addon)


	# load them into the window

	# GUI.doModal()

	log('Exiting GUI')

	del GUI


