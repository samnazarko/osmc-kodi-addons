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
		self.APPLY_ICON_IMAGE = 'up.png'
		self.APPLY_ICON_IMAGE_FO = 'down.png'


	def onInit(self):

		# place the items into the gui
		for i, module in enumerate(self.live_modules):

			# set the icon (texturefocus, texturenofocus)
			list_item = xbmcgui.ListItem(label='', label2='', thumbnailImage = module[2])
			list_item.setProperty('FO_ICON','FO_' + module[2])
			list_item.setProperty('Action', module[1])

			self.getControl(self.order_of_fill[i]).addItem(list_item)

		# set up the apply buttons
		for apply_button in self.apply_buttons:

			# set the image
			list_item = xbmcgui.ListItem(label='', label2='', thumbnailImage = self.APPLY_ICON_IMAGE)
			list_item.setProperty('FO_ICON', self.APPLY_ICON_IMAGE_FO)
			list_item.setProperty('Action', "Apply")

			self.getControl(apply_button).addItem(list_item)


	def onClick(self, controlID):

		if not (controlID - 5) % 100:
			self.close()


class OSMCGui(object):

	def __init__(self):

		self.create_gui()

	def create_gui(self):
		# known modules is a list of tuples detailing all the known and permissable modules and services
		# (order, module name, icon): the order is the hierarchy of addons (which is used to 
		# determine the positions of addon in the gui), the icon is the image that will be used in the
		# gui (they need to be stored in resources/skins/Default/media/)
		self.known_modules = 	[

								(1,
								"script.module.osmcsetting.dummy",
								"sub.png"),

								]

		# order of addon hierarchy
		# 105 is Apply
		self.item_order    = [104, 106, 102, 108, 101, 109, 103, 107]
		self.apply_button  = [105]

		# window xml to use
		# xmlfile = 'settings_main.xml'
		self.xmlfile = 'settings_gui.xml'

		# check if modules and services exist, add the ones that exist to the live_modules list
		self.live_modules = [z for z in [self.check_live(x) for x in self.known_modules] if z]
		self.live_modules.sort()

		# determine which order list is used, indexed to 0
		self.number_of_pages_needed = (len(self.live_modules) // 8) +1

		self.order_of_fill = [ item + (100 * x) for item in self.item_order   for x in range(self.number_of_pages_needed) ]
		self.apply_buttons = [ item + (100 * x) for item in self.apply_button for x in range(self.number_of_pages_needed) ]


		# instantiate the window
		self.GUI = walkthru_gui(self.xmlfile, scriptPath, 'Default', order_of_fill=self.order_of_fill,
			apply_buttons=self.apply_buttons, live_modules=self.live_modules)

	

	def open(self):

		'''
			Opens the gui window
		'''

		# display the window
		self.GUI.doModal()

		log('Exiting GUI')

		del self.GUI



	def check_live(self, module):
		'''
			Checks to see whether the module exists and is active. If it doesnt exist, or is set to inactive,
			then return False, otherwise import the module (or the setting_module.py in the service or addons
			resources/lib/) and create then return the instance of the SettingGroup in that module.
		'''

		return module

