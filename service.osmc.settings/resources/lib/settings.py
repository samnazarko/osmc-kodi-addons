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

	def __init__(self, strXMLname, strFallbackPath, strDefaultName, **kwargs):

		self.order_of_fill  = kwargs.get('order_of_fill',  [])
		self.apply_buttons  = kwargs.get('apply_buttons',  [])
		self.live_modules = kwargs.get('live_modules', [])

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

		# these are for testing only
		APPLY_ICON_IMAGE = 'key.png'
		APPLY_ICON_IMAGE_FO = 'lock.png'

		# place the items into the gui
		for i, module in enumerate(self.live_modules):

			# set the icon (texturefocus, texturenofocus)
			list_item = xbmcgui.ListItem(label='', label2='', thumbnailImage = module[2])
			list_item.setProperty('FO_ICON') = 'FO_' + module[2]
			list_item.setProperty('Action') = module[1]

			self.getControl(self.order_of_fill[i]).addItem(list_item)

		# set up the apply buttons
		for apply_button in self.apply_buttons:

			# set the image
			list_item = xbmcgui.ListItem(label='', label2='', thumbnailImage = APPLY_ICON_IMAGE)
			list_item.setProperty('FO_ICON') = APPLY_ICON_IMAGE_FO
			list_item.setProperty('Action') = "Apply"

			self.getControl(apply_button).addItem(list_item)




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
						"sub.png"),

						]


	# order of addon hierarchy
	# 105 is Apply
	item_order    = [104, 106, 102, 108, 101, 109, 103, 107]
	apply_button  = [105]

	order_lists = [one_page, two_page, three_page]

	# window xml to use
	# xmlfile = 'settings_main.xml'
	xmlfile = 'settings_gui.xml'

	# check if modules and services exist, add the ones that exist to the live_modules list
	live_modules = [x for x in known_modules if check_live(x) == True].sort()

	# determine which order list is used, indexed to 0
	number_of_pages_needed = (len(live_modules) // 8)

	order_of_fill = [ item + (100 * (x + 1)) for item in item_order   for x in range(number_of_pages_needed) ]
	apply_buttons = [ item + (100 * (x + 1)) for item in apply_button for x in range(number_of_pages_needed) ]


	# instantiate the window
	GUI = walkthru_gui(xmlfile, scriptPath, 'Default', order_of_fill=order_of_fill, apply_buttons=apply_buttons, live_modules=live_modules)


	# display the window
	GUI.doModal()

	log('Exiting GUI')

	del GUI


