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
import imp


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

		self.order_of_fill  = kwargs.get('order_of_fill', [])
		self.apply_buttons  = kwargs.get('apply_buttons', [])
		self.live_modules   = kwargs.get('live_modules' , [])

		log(kwargs)

		log(len(self.live_modules))

		self.module_holder  = {}

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

		self.first_run = True

		# these are for testing only
		self.APPLY_ICON_IMAGE = 'up.png'
		self.APPLY_ICON_IMAGE_FO = 'down.png'


	def onInit(self):

		if self.first_run:
			self.first_run = False

			

			# place the items into the gui
			for i, module in enumerate(self.live_modules):

				# set the icon (texturefocus, texturenofocus)
				list_item = xbmcgui.ListItem(label=module['id'], label2='', thumbnailImage = module['FX_Icon'])
				list_item.setProperty('FO_ICON', module['FO_Icon'])

				controlID = self.order_of_fill[i]

				self.getControl(controlID).addItem(list_item)

				self.module_holder[controlID] = module

			# set up the apply buttons
			for apply_button in self.apply_buttons:

				# set the image
				list_item = xbmcgui.ListItem(label='', label2='', thumbnailImage = self.APPLY_ICON_IMAGE)
				list_item.setProperty('FO_ICON', self.APPLY_ICON_IMAGE_FO)
				list_item.setProperty('Action', "Apply")

				self.getControl(apply_button).addItem(list_item)


	def onAction(self, action):

		actionID = action.getId()

		if (actionID in (10, 92)):
			self.close()


	def onClick(self, controlID):

		if not (controlID - 5) % 100:
			self.close()

		else:

			module = self.module_holder.get(controlID, {})
			instance = module.get('SET', False)

			log(instance)

			# try:
			instance.open_settings_window()
			# except:
			# log('Settings window for __ %s __ failed to open' % module.get('id', "Unknown"))


class OSMCGui(object):

	def __init__(self, **kwargs):

		self.queue = kwargs['queue']

		self.create_gui()

	def create_gui(self):
		# known modules is a list of tuples detailing all the known and permissable modules and services
		# (order, module name, icon): the order is the hierarchy of addons (which is used to 
		# determine the positions of addon in the gui), the icon is the image that will be used in the
		# gui (they need to be stored in resources/skins/Default/media/)
		self.known_modules_order = 	{
									"script.module.osmcsetting.dummy":			0
									}

		# order of addon hierarchy
		# 105 is Apply
		self.item_order    = [104, 106, 102, 108, 101, 109, 103, 107]
		self.apply_button  = [105]

		# window xml to use
		# xmlfile = 'settings_main.xml'
		self.xmlfile = 'settings_gui.xml'

		# check if modules and services exist, add the ones that exist to the live_modules list
		self.ordered_live_modules = self.retrieve_modules()
		self.ordered_live_modules.sort()
		self.live_modules = [x[1] for x in self.ordered_live_modules]

		# determine which order list is used, indexed to 0
		self.number_of_pages_needed = (len(self.live_modules) // 9) +1

		log('number_of_pages_needed')
		log(self.number_of_pages_needed)

		self.order_of_fill = [ item + (100 * x) for x in range(self.number_of_pages_needed) for item in self.item_order    ]
		self.apply_buttons = [ item + (100 * x) for x in range(self.number_of_pages_needed) for item in self.apply_button  ]


		# instantiate the window
		self.GUI = walkthru_gui(self.xmlfile, scriptPath, 'Default', order_of_fill=self.order_of_fill,
			apply_buttons=self.apply_buttons, live_modules=self.live_modules)

	
	def open(self):

		'''
			Opens the gui window
		'''
		
		log('Opening GUI')
		# display the window
		self.GUI.doModal()

		# run the apply_settings method on all modules
		for module in self.live_modules:
			m = module.get('SET', False)
			try:
				m.apply_settings()
			except:
				log('apply_settings failed for %s' % m.addonid)


		# check is a reboot is required
		reboot = False
		for module in self.live_modules:
			m = module.get('SET', False)
			try:
				if m.reboot_required:
					reboot = True
					break
			except:
				pass

		if reboot:
			self.queue.put('reboot')


		log('Exiting GUI')

		# del self.GUI


	def retrieve_modules(self):
		'''
			Checks to see whether the module exists and is active. If it doesnt exist (or is set to inactive)
			then return False, otherwise import the module (or the setting_module.py in the service or addons
			resources/lib/) and create then return the instance of the SettingGroup in that module.

		'''

		self.module_tally = 1000

		addon_folder  = os.path.join(xbmc.translatePath("special://home"), "addons/")

		folders       = [item for item in os.listdir(addon_folder) if os.path.isdir(os.path.join(addon_folder, item))]

		osmc_modules   = [x for x in [self.inspect_folder(addon_folder, folder) for folder in folders] if x]

		return osmc_modules


	def inspect_folder(self, addon_folder, sub_folder):
		'''
			Checks the provided folder to see if it is a genuine OSMC module.
			Returns a tuple.
				(preferred order of module, module name: {unfocussed icon, focussed icon, instance of OSMCSetting class})
		'''

		# check for osmc subfolder, return nothing is it doesnt exist
		osmc_subfolder = os.path.join(addon_folder, sub_folder, "resources", "osmc")
		if not os.path.isdir(osmc_subfolder): return

		# check for OSMCSetting.py, return nothing is it doesnt exist
		osmc_setting_file = os.path.join(osmc_subfolder, "OSMCSetting.py")
		if not os.path.isfile(osmc_setting_file): return

		# check for the unfocussed icon.png
		osmc_setting_FX_icon = os.path.join(osmc_subfolder, "FX_Icon.png")
		if not os.path.isfile(osmc_setting_FX_icon): return

		# check for the focussed icon.png
		osmc_setting_FO_icon = os.path.join(osmc_subfolder, "FO_Icon.png")
		if not os.path.isfile(osmc_setting_FO_icon): return

		# if you got this far then this is almost certainly an OSMC setting
		# try:
		new_module_name = sub_folder.replace('.','')
		log(new_module_name)
		OSMCSetting = imp.load_source(new_module_name, osmc_setting_file)
		log(dir(OSMCSetting))
		setting_instance = OSMCSetting.OSMCSettingClass()
		# except:
		# 	log('OSMCSetting __ %s __ failed to import' % sub_folder)
		# 	return

		# success!
		log('OSMC Setting Module __ %s __ found and imported' % sub_folder)

		# DETERMINE ORRDER OF ADDONS, THIS CAN BE HARDCODED FOR SOME OR THE USER SHOULD BE ABLE TO CHOOSE THEIR OWN ORDER
		if sub_folder in self.known_modules_order.keys():
			order = self.known_modules_order[sub_folder]
		else:
			order = self.module_tally
			self.module_tally += 1

		return (order, {'id': sub_folder, 'FX_Icon': osmc_setting_FX_icon, 'FO_Icon': osmc_setting_FO_icon, 'SET':setting_instance})


