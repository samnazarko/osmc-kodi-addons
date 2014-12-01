'''

	The settings for OSMC are handled by the OSMC Settings Addon (OSA).

	In order to accomodate easier changes and enhancements, each OSMC settings group/module is a separate addon. 

	The module can be setup as 
		- an xbmc module
			- the name must take the form script.module.osmcsetting.ModuleSpecificName
			- it must have a folder called lib, and this must contain a file called setting_module.py 
		- as a service
			- the service must have a file called setting_module.py in its resources/lib/ folder.

	The setting_module.py file must have a class called SettingGroup.
	Instances of this class are used by the OSA to:
		- call the settings window for the module to allow the user to make changes
		- call methods of the instance to apply any changes to the settings 

	This class must follow the structure as listed below.

		- the class must have a method called 'apply_settings' for the application of all settings changes 

		- the class must have a dictionary called setting_method_dict, which contains for every applicable setting:
				- the setting name as a key (this must match the id in the settings.xml)
					- the currently active setting value
					- a method to call to apply any changes to the setting 
					o an optional setting specific method to call immediately after booting
				o an optional method to apply before any other setting change methods are called
				o an optional method to apply after all other setting change methods have been called

		- the setting_method_dict must be populated on instantiation of the class
				- this can be from the settings.xml for the module (preferred), or
				- from a separate config file (as in the case of the config.txt file for the Raspberry Pi)
	
		- the class must have a method to open the settings window
				- in most cases this will be the actual settings window, but it does permit the module to have its own skinned
				  window is the developer wants it

'''


def SettingGroup:

	''' 
		A SettingGroup is way to substantiate the settings of an OSMC settings module, and make them available to the 
		OSMC Settings Addon (OSA).

	'''

	def __init___(self):

		''' 
			The setting_method_dict contains all the settings in the settings group, as well as the methods to call when a
			setting_value has changed and the existing setting_value. 
		'''

		self.setting_method_dict = 	{

									'first_method' :	self.first_method,

									'setting_nameX': 	{
														'method_to_apply_changes': self.method_to_apply_changes_X,
														'method_to_apply_onboot' : self.method_to_apply_onboot_X,
														'setting_value' : ''
														},

									'setting_nameY': 	{
														'method_to_apply_changes': self.methodY,
														'setting_value' : ''
														},

									'setting_nameZ': 	{
														'method_to_apply_changes': self.methodZ,
														'setting_value' : ''
														},

									'final_method' :	self.final_method

									}

		# populate the settings data in the setting_method_dict
		self.populate_setting_method_dict()


		# a flag to determine whether a setting change requires a reboot to take effect
		self.reboot_required = False




	# PUBLIC METHOD
	def apply_settings(self):

		'''
			This method will apply all of the settings. It calls the first setting method, if it exists. 
			Then it calls the method listed in setting_method_dict for each setting. Then it calls the
			final method, again, if it exists.
		'''

		# retrieve the current settings
		new_settings = self.settings_processor()

		# apply the settings changes
		self.settings_change_dispatcher(new_settings)

		# call the final method if there is one
		final_method = self.setting_method_dict.get('final_method', False)

		if final_method:
			final_method()


	def settings_change_dispatcher(self, new_settings):

		''' 
			Compares the new settings to their old values and calls the relevant method if the settings have changed.
		'''

		for k, v in self.setting_method_dict.iteritems():

			method = v.get('method_to_apply_changes', False)
			value  = v['setting_value']

			if new_settings[k] != value:

				# change stored setting_value to the new value
				self.setting_method_dict[k]['setting_value'] = new_settings[k]

				if method:
					method(value)


	def settings_retriever_xml(self):

		''' 
			Reads the stored settings (in settings.xml) and returns a dictionary with the setting_name: setting_value .
		'''

		latest_settings = {}

		for key in self.setting_method_dict.keys():

			latest_settings[key] = xbmcaddon.getSetting(key)

		return latest_settings


	def populate_setting_method_dict(self):

		'''
			Populates the setting_value in the setting_method_dict
		'''

		latest_settings = self.settings_processor()

		for key in self.setting_method_dict.keys():

			self.setting_method_dict[key]['setting_value'] = latest_settings[key]


	# PUBLIC METHOD
	def auto_run_settings(self):

		'''
			Checks the name of all settings and runs the relevant method if the setting name ends with "_init" 
		'''

		for k, v in self.setting_method_dict.iteritems():

			method = v.get('method_to_apply_onboot', False)
			value  = v['setting_value']

			if method:
				method(value)


	##############################################################################################################################
	#																															 #

	''' 
		Methods beyond this point are for specific settings. 
	'''

	# SETTING METHOD
	def method_to_apply_changes_X(self, data):

		'''
			Method for implementing changes to setting x 
		'''


	def method_to_apply_onboot_X(self, data):

		'''
			Method for applying the stored setting for setting x on first boot
		'''

	#																															 #
	##############################################################################################################################


	# FIRST SETTING METHOD
	def first_method(self):

		''' 
			The method to call before all the other setting methods are called.

			For example, this could be a call to stop a service. The final method could then start the service again. 
			This can be used to apply the setting changes.

		'''	


	# FINAL SETTING METHOD
	def final_method(self):

		''' 
			The method to call after all the other setting methods have been called.

			For example, in the case of the Raspberry Pi's settings module, the final writing to the config.txt can be delayed
			until all the settings have been updated in the setting_method_dict. 

		'''



NOTES:
 - what about the items that need to be processed all at once?
 - what about the items that the user might manually change offline (like config.txt)