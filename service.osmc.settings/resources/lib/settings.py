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

	__addon__        = xbmcaddon.Addon()
	scriptPath       = __addon__.getAddonInfo('path')


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

	# known modules is a list of tuples detailing all the known and permissable modules and services
	# (order, module name, icon): the order is the hierarchy of addons (which is used to 
	# determine the positions of addon in the gui), the icon is the image that will be used in the
	# gui (they need to be stored in resources/skins/Default/media/)
	known_modules = 	[

						(1,
						"script.module.osmcsetting.dummy",
						"circle.png"),

						]


	# order of addon hierarchy
	# fewer than 9 items
	# 105 is Apply
	one_page = [102, 104, 106, 108, 101, 103, 107, 109]
	
	# more than 8 items, fewer than 17
	# 105 & 205 are Apply
	# 109 is Next
	two_page = [102, 104, 106, 108, 101, 103, 107, 202, 204, 206, 208, 201, 203, 207, 209]

	# more than 16 items, fewer than 25
	# 105 & 205 & 305 are Apply
	# 109 & 209 are Next
	three_page = [102, 104, 106, 108, 101, 103, 107, 202, 204, 206, 208, 201, 203, 207, 302, 304, 306, 308, 301, 303, 307, 309]

	order_lists = [one_page, two_page, three_page]

	# window xml to use
	# xmlfile = 'settings_main.xml'
	xmlfile = 'settings_gui.xml'

	# instantiate the window
	GUI = walkthru_gui(xmlfile, scriptPath, 'Default')

	# check if modules and services exist, add the ones that exist to the live_modules list
	live_modules = [x for x in known_modules if check_live(x) == True].sort()

	# determine which order list is used
	order_list = order_lists[len(live_modules) // 8]

	# place them into the gui
	for i, module in enumerate(live_modules):
		control = self.getControl(order_list[i])
		# set the icon (texturefocus, texturenofocus)
		control.

	# add Applies
	

	# add Nexts


	# display the window
	GUI.doModal()

	log('Exiting GUI')

	del GUI


