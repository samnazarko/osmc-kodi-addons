'''

	The settings for OSMC are handled by the OSMC Settings Addon (OSA).

	In order to more easily accomodate future changes and enhancements, each OSMC settings bundle (module) is a separate addon.
	The module can take the form of an xbmc service, an xbmc script, or an xbmc module, but it must be installed into the users'
	userdata/addons folder.

	The OSA leverages the settings interface provided by XBMC. Each addon has its own individual settings defined in a
	settings.xml file located in the addon's resources/ folder.

	The OSG detects changes to the settings by identifying the differences between a newly read settings.xml and the values from 
	a previously read settings.xml.

	The values of the settings displayed by the OSG are only ever populated by the items in the settings.xml. [Note: meaning that 
	if the settings data is retrieved from a different source, it will need to be populated in the module before it is displayed
	to the user.]

	Each module must have in its folder, a sub-folder called 'resources/osmc'. Within that folder must reside this script (OSMCSetting.py), 
	and the icons to be used in the OSG to represent the module (FX_Icon.png and FO_Icon.png for unfocused and focused images
	respectively).

	When the OSA creates the OSMC Settings GUI (OSG), these modules are identified and the OSMCSetting.py script in each of them 
	is imported. This script provides the mechanism for the OSG to apply the changes required from a change in a setting.

	The OSMCSetting.py file must have a class called OSMCSettingClass as shown below.

	The key variables in this class are:

		addonid							: The id for the addon. This must be the id declared in the addons addon.xml.

		reboot_required					: A boolean to declare if the OS needs to be rebooted. If a change in a specific setting 
									 	  requires an OS reboot to take affect, this is flag that will let the OSG know.

		setting_data_method 			: This dictionary contains:
												- the name of all settings in the module
												- the current value of those settings
												- [optional] a method to call for each setting when the value changes
												- [optional] translate - a method to call to translate the data before adding it to the 
												  setting_data_method dict. The translate method must have a 'reverse' argument which 
												  when set to True, reverses the transformation.  


	The key methods of this class are:

		open_settings_window			: This is called by the OSG when the icon is clicked. This will open the settings window.
										  Usually this would be __addon__.OpenSettings(), but it could be any other script.
										  This allows the creation of action buttons in the GUI, as well as allowing developers 
										  to script and skin their own user interfaces.

		[optional] first_method			: called before any individual settings changes are applied.

		[optional] final_method			: called after all the individual settings changes are done.

		[optional] boot_method			: called when the OSA is first started.

		apply_settings					: This is called by the OSG to apply the changes to any settings that have changed.
										  It calls the first setting method, if it exists. 
										  Then it calls the method listed in setting_data_method for each setting. Then it 
										  calls the final method, again, if it exists.

		populate_setting_data_method	: This method is used to populate the setting_data_method with the current settings data.
										  Usually this will be from the addons setting data stored in settings.xml and retrieved
										  using the settings_retriever_xml method.

										  Sometimes the user is able to edit external setting files (such as the Pi's config.txt).
										  If the developer wants to use this source in place of the data stored in the
										  settings.xml, then they should edit this method to include a mechanism to retrieve and 
										  parse that external data. As the window shown in the OSG populates only with data from 
										  the settings.xml, the developer should ensure that the external data is loaded into that
										  xml before the settings window is opened.


		settings_retriever_xml			: This method is used to retrieve all the data for the settings listed in the 
										  setting_data_method from the addons settings.xml.

	The developer is free to create any methods they see fit, but the ones listed above are specifically used by the OSA.

	Settings changes are applied when the OSG is called to close. But this behaviour can be changed to occur when the addon
	settings window closes by editing the open_settings_window. The method apply_settings will still be called by OSG, so 
	keep that in mind.

'''


# XBMC Modules
import xbmc
import xbmcaddon
import subprocess
import sys
import os

addonid = "script.module.osmcsetting.pi"

# Custom modules
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon(addonid).getAddonInfo('path'), 'resources','osmc')))

# OSMC SETTING Modules
import config_tools as ct


class OSMCSettingClass(object):

	''' 
		A OSMCSettingClass is way to substantiate the settings of an OSMC settings module, and make them available to the 
		OSMC Settings Addon (OSA).

	'''

	def __init__(self):

		''' 
			The setting_data_method contains all the settings in the settings group, as well as the methods to call when a
			setting_value has changed and the existing setting_value. 
		'''

		self.addonid = addonid
		self.me = xbmcaddon.Addon(self.addonid)

		self.description = 	"""
								This is the text that is shown on the OSG. It should describe what the settings module is for,
								the settings it controls, and anything else you want, I suppose.
							"""

		self.not_going_to_config = [	'store_hdmi_to_file',
										'gpu_memory',
										]

		self.values_set_elsewhere = [	'hdmi_edid_file',
										'hdmi_force_hotplug',
										'gpu_mem_256',
										'gpu_mem_512',
										]

		# The setting_value in this dict is what is used in the settings.xml. The need to be translated from any external source,
		# line the config.txt, and then translated again for writing back.
		# I have added a translate method to translate the data recieved from an external source before adding it to the setting dict
		# I have also added a default setting here, because the settings stored in the settings.xml cannot be relied upon,
		# because if the user adds a setting, then deletes it offline, the settings.xml will add it back in when the addon exits.
		# A default value of configignore means that the setting should never be passed to the config parser.
		self.setting_data_method = 	{
									'hdmi_safe': 				{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_bool
																		},
									'hdmi_ignore_edid': 		{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_bool
																		},
									'store_hdmi_to_file':		{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_store_hdmi,
																			'apply' : self.apply_store_hdmi,
																			},
									'hdmi_edid_file': 			{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_bool
																		},
									'hdmi_force_hotplug': 		{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_bool,
																		},
									'hdmi_ignore_cec': 			{'setting_value' : '',
																	'default': 'false',
																		'translate': self.translate_bool
																		},
									'hdmi_boost': 				{'setting_value' : '',
																	'default': '0',
																	},
									'hdmi_group': 				{'setting_value' : '',
																	'default': '0',
																	},
									'hdmi_mode': 				{'setting_value' : '',
																	'default': '0',
																	},
									'display_rotate': 			{'setting_value' : '',
																	'default': '0',
																	},
									'gpu_memory':				{'setting_value' : '',
																	'default': 'false',
																		'apply': self.apply_gpu_memory,
																			'translate': self.translate_gpu_mem
																	},
									'gpu_mem_256': 				{'setting_value' : '',
																	'default': '64',
																	},
									'gpu_mem_512': 				{'setting_value' : '',
																	'default': '64',
																	},
									'decode_MPG2': 				{'setting_value' : '',
																	'default': '',
																	},
									'decode_WVC1': 				{'setting_value' : '',
																	'default': '',
																	},
									'other_settings_string': 	{'setting_value' : '',
																	'default': '',
																		'translate': self.translate_other_string
																		},								
									}

		# list to hold the keys for the other string settings
		self.unknown_setting_keys = []

		# list to hold the keys for the settings that need to be removed from the config.txt
		self.remove_list = []

		# the location of the config file FOR TESTING ONLY									
		self.test_config = '/home/kubkev/Documents/config.txt'

		# populate the settings data in the setting_data_method
		# self.populate_setting_data_method()

		# a flag to determine whether a setting change requires a reboot to take effect
		self.reboot_required = False

		print 'START'
		for x, k in self.setting_data_method.iteritems():
			print "%s = %s" % (x, k.get('setting_value','farts'))


	def populate_setting_data_method(self):

		'''
			Populates the setting_value in the setting_data_method.
		'''

		# this is the method to use if you are populating the dict from the settings.xml
		# latest_settings = self.settings_retriever_xml()

		# but I am going to set up my own process in addition to the xml one, I will be reading some
		# settings from the config.txt, and getting the rest from the settings.xml
		self.config_settings = ct.read_config(self.test_config)

		# cycle through the setting_data_method dict, and populate with the settings values
		for key in self.setting_data_method.keys():

			# grab the translate method (if there is one)
			translate_method = self.setting_data_method.get(key,{}).get('translate',{})

			# if the key is in the config.txt
			if key in self.config_settings:

				# get the setting value, translate it if needed
				if translate_method:
					setting_value = translate_method(self.config_settings[key])
				else:
					setting_value = self.config_settings[key]

				# set the value in the setting_data_method
				self.setting_data_method[key]['setting_value'] = setting_value
				
				# also set the value in the settings.xml
				self.me.setSetting(key, setting_value)

			else:
				# if the key ISNT in the config.txt then set the value from the default stored in 
				# the setting_data_method dict

				setting_value = self.setting_data_method[key].get('default','')

				# get the setting value, translate it if needed
				if translate_method:
					setting_value = translate_method(setting_value)

				# if default is setting_value, then the setting has been set in the translation so ignore it
				if setting_value not in self.not_going_to_config:
					self.setting_data_method[key]['setting_value'] = setting_value

				# also set the value in the settings.xml
				self.me.setSetting(key, setting_value)


	def open_settings_window(self):

		'''
			The method determines what happens when the item is clicked in the settings GUI.
			Usually this would be __addon__.OpenSettings(), but it could be any other script.
			This allows the creation of action buttons in the GUI, as well as allowing developers to script and skin their 
			own user interfaces.
		'''

		# read the config.txt file everytime the settings are opened. This is unavoidable because it is possible for
		# the user to have made manual changes to the config.txt while OSG is active.
		self.populate_setting_data_method()

		for x, k in self.setting_data_method.iteritems():
			print "%s = %s" % (x, k.get('setting_value','farts'))


		self.me.openSettings()


		# code placed here will run when the modules settings window is closed
		self.apply_permitted = True
		
		self.apply_settings()

		self.apply_permitted = False

		# apply_permitted will prevent the apply function being called by anything other than this method.
		# This stops it from being called twice, once when the settings are closed and another when the OSG is closed

		print 'END'
		for x, k in self.setting_data_method.iteritems():
			print "%s = %s" % (x, k.get('setting_value','farts'))


	def apply_settings(self):

		'''
			This method will apply all of the settings. It calls the first_method, if it exists. 
			Then it calls the method listed in setting_data_method for each setting. Then it calls the
			final_method, again, if it exists.
		'''

		if not self.apply_permitted:
			return

		# retrieve the current settings from the settings.xml (this is where the user has made changes)
		new_settings = self.settings_retriever_xml()

		# dict to hold the keys of the changed settings
		self.changed_settings = {}

		# list to hold the keys of the settings that need to be removed from the 

		# call the first method, if there is one
		self.first_method()

		# apply the individual settings changes
		for k, v in self.setting_data_method.iteritems():

			# get the application method and stored setting value from the dictionary
			method = v.get('apply', False)
			value  = v.get('setting_value', '')

			# if the new setting is different to the stored setting then change the dict and run the 'apply' method
			if new_settings[k] != value:

				# change stored setting_value to the new value
				self.setting_data_method[k]['setting_value'] = new_settings[k]
		
				# add it to the changed settings dict
				self.changed_settings[k] = new_settings[k]

				# if a specific apply method exists for the setting, then call that
				try:
					method(new_settings[k])
				except:
					pass

		# call the final method if there is one
		self.final_method()


	def settings_retriever_xml(self):

		''' 
			Reads the stored settings (in settings.xml) and returns a dictionary with the setting_name: setting_value. This 
			method cannot be overwritten.
		'''

		latest_settings = {}

		addon = xbmcaddon.Addon(self.addonid)

		for key in self.setting_data_method.keys():

			latest_settings[key] = addon.getSetting(key)

		return latest_settings


	##############################################################################################################################
	#																															 #
	def first_method(self):

		''' 
			The method to call before all the other setting methods are called.

			For example, this could be a call to stop a service. The final method could then restart the service again. 
			This can be used to apply the setting changes.

		'''	


	def final_method(self):

		''' 
			The method to call after all the other setting methods have been called.

			For example, in the case of the Raspberry Pi's settings module, the final writing to the config.txt can be delayed
			until all the settings have been updated in the setting_data_method. 

		'''

		''' This method will write the changed settings to the config.txt file. '''

		# translate the changed settings into values that can be used in the config.txt
		translated_settings = {}
		for k, v in self.changed_settings.iteritems():

			# ignore the setting if it is not to be added to the config.txt
			if k in self.not_going_to_config:
				# translated_settings[k] = 'remove'
				continue

			# translate the setting if needed
			translate_method = self.setting_data_method.get(k,{}).get('translate', False)

			if translate_method:
				value = translate_method(v, reverse=True)
			else:
				value = v #.get('setting_value','')

			# if this is the other_settings_string then break up into the individual settings
			if k == 'other_settings_string':
				for key, svalue in value.iteritems():
					translated_settings[key] = svalue
			else:
				translated_settings[k] = value

		# transfer the remove list into the changes dict
		for remove_key in self.remove_list:
			translated_settings[remove_key] = 'remove'

		self.remove_list = []

		# write the settings to the config.txt
		ct.write_config(self.test_config, translated_settings)


	def boot_method(self):

		''' 
			The method to call when the OSA is first activated (on reboot)

		'''

		pass

	#																															 #
	##############################################################################################################################


	##############################################################################################################################
	#																															 #

	''' 
		Methods beyond this point are for specific settings. 
	'''

	def apply_store_hdmi(self, data):

		'''
			Method for implementing changes to setting store_hdmi_to_file. If the setting is on, then change two dependent
			settings and run something in the command line. If it is off, then disable those two settings.
		'''
		print '============================'
		print data
		print type(data)
		print '============================'
		
		if data == 'true':

			print "store hdmi true"

			# change the dependent settings to 1
			self.setting_data_method['hdmi_edid_file']['setting_value'] = 'true'
			self.setting_data_method['hdmi_force_hotplug']['setting_value'] = 'true'

			# add it to the changed settings dict
			self.changed_settings['hdmi_edid_file'] = 'true'
			self.changed_settings['hdmi_force_hotplug'] = 'true'

			# run the sub_process : "tvservice -d /boot/edid.dat"
			subprocess.call(["tvservice", "-d", "/boot/edid.dat"])

		else:

			print "store hdmi false"

			self.setting_data_method['hdmi_edid_file']['setting_value'] = 'false'
			self.setting_data_method['hdmi_force_hotplug']['setting_value'] = 'false'

			# add it to the changed settings dict
			self.changed_settings['hdmi_edid_file'] = 'false'
			self.changed_settings['hdmi_force_hotplug'] = 'false'


	def apply_gpu_memory(self, data):

		''' Takes the value for gpu_memory and applies it to both gpu_mem_256 and gpu_mem_512 '''

		try:
			cdata = int(data)
		except:
			cdata = 64

		# change stored setting_value to the new value
		self.setting_data_method['gpu_mem_512']['setting_value'] = min(448,cdata)
		self.setting_data_method['gpu_mem_256']['setting_value'] = min(192,cdata)

		# add it to the changed settings dict
		self.changed_settings['gpu_mem_512'] = min(448,cdata)
		self.changed_settings['gpu_mem_256'] = min(192,cdata)


	def translate_bool(self, data, reverse=False):

		''' method to convert number or text into boolean '''

		if not reverse:
			if data in [1, '1']:
				return 'true'
			else:
				return 'false'

		else:
			if data in [1, '1', 'true']:
				return '1'
			else:
				# any boolean that is set to 0 in the settings.xml should be removed from the config.txt
				return '0'


	def translate_other_string(self, data='', reverse=False):

		''' 
			Method to collate all the unknown settings from the config.txt into a single string, delimited by |:-:|.
			The reverse function returns a dictionary with {setting_name: setting_value, ... }
		'''

		if not reverse:
			config_keys = set(self.config_settings.keys())
			xml_keys    = set(self.setting_data_method.keys())

			self.unknown_setting_keys = list(config_keys.difference(xml_keys))

			unknown_settings = [str(x) + '=' + str(self.config_settings[x]) for x in self.unknown_setting_keys]

			return "|:-:|".join(unknown_settings)

		else:

			no_space_data = data.replace(" ",'')
			setting_pairs = no_space_data.split("|:-:|")

			other_settings = []

			for setting in setting_pairs:
				set_list = setting.split('=')

				if len(set_list) == 2:
					other_settings.append(tuple(set_list))

			new_unknown_settings = dict(other_settings)

			# construct a list of keys that are in self.unknown_setting_keys but not in new_unknown_settings_keys
			new_unknown_settings_keys = set(new_unknown_settings.keys())
			unknown_settings_keys = set(self.unknown_setting_keys)

			removals = list(unknown_settings_keys.difference(new_unknown_settings_keys))

			# setup the removed unknown settings to be removed from the config.txt
			for rem in removals:
				new_unknown_settings[rem] = 'remove'

			# change the self.unknown_setting_keys list to the current list of unknown keys
			self.unknown_setting_keys = list(new_unknown_settings_keys)

			return new_unknown_settings


	def translate_store_hdmi(self, data, reverse=False):

		''' Returns 1 if hdmi_edid_file and hdmi_force_hotplug are set to 1.
			In reverse,  '''

		if not reverse:
			if all([self.config_settings.get('hdmi_edid_file', 0), self.config_settings.get('hdmi_force_hotplug', 0)]):
				
				print 'translate_store_hdmi'
				print self.config_settings.get('hdmi_edid_file', 'farts')
				print self.config_settings.get('hdmi_force_hotplug', 'farts')


				return 'true'
			else:
				
				self.me.setSetting('hdmi_edid_file', 'false')
				self.me.setSetting('hdmi_force_hotplug', 'false')

				return 'false'

		else:
			return 'remove'
			# this setting will never be sent for reversed translation


	def translate_gpu_mem(self, data, reverse=False):

		''' 
			If gpu_mem is present in the config.txt, then apply it to both gpu_mem_256 and gpu_mem_512.
			Any new config.txt should be missing the gpu_mem setting.
		'''

		if not reverse:

			# if either 256 or 512 is present, then use that figure instead
			if 'gpu_mem_512' in self.config_settings:
				
				# set gpu_mem for removal from the config.txt
				self.remove_list.append('gpu_mem')
				return self.config_settings['gpu_mem_512']

			elif 'gpu_mem_256' in self.config_settings:
				
				# set gpu_mem for removal from the config.txt
				self.remove_list.append('gpu_mem')
				return self.config_settings['gpu_mem_256']

			# if neither of those are present, then take the gpu_mem figure and overwrite the other ones.
			gpu_data = self.config_settings.get('gpu_mem', 64)

			# change the settings in the dict
			self.setting_data_method['gpu_mem_256']['setting_value'] = min(192, int(gpu_data))
			self.setting_data_method['gpu_mem_512']['setting_value'] = min(448, int(gpu_data))
			self.setting_data_method['gpu_memory']['setting_value'] = gpu_data

			# set gpu_mem for removal from the config.txt
			self.remove_list.append('gpu_mem')

		else:
			return 'remove'
			# this setting will never be sent for reversed translation


	#																															 #
	##############################################################################################################################

if __name__ == "__main__":
	pass

