# Standard Modules
import apt
from datetime import datetime
import os
import sys
import subprocess
import Queue
import random
import json

# Kodi Modules
import xbmc
import xbmcaddon
import xbmcgui

# Custom modules
__libpath__ = xbmc.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources','lib'))
sys.path.append(__libpath__)
import comms
import simple_scheduler as sched


__addon__              	= xbmcaddon.Addon()
__addonid__            	= __addon__.getAddonInfo('id')
__scriptPath__         	= __addon__.getAddonInfo('path')
__setting__            	= __addon__.getSetting
__image_file__         	= os.path.join(__scriptPath__,'resources','media','update_available.png')
lang 					= __addon__.getLocalizedString

DIALOG  = xbmcgui.Dialog()


def log(message, label = ''):
	logmsg       = '%s : %s - %s ' % (__addonid__ , str(label), str(message))
	xbmc.log(msg = logmsg)


class Monitah(xbmc.Monitor):

	def __init__(self, **kwargs):
		super(Monitah, self).__init__()

		self.parent_queue = kwargs['parent_queue']


	def onAbortRequested(self):

		log('killing self')

		msg = json.dumps(('kill_yourself', {}))

		self.parent_queue.put(msg)


	def onSettingsChanged(self):
		log('settings changed!!!!!!!!!!!!!!!!!!!!!!!')

		msg = json.dumps(('update_settings', {}))

		self.parent_queue.put(msg)

		log(self.parent_queue, 'self.parent_queue')



class Main(object):

	''' This service allows for the checking for new updates, then:
			- posts a notification on the home screen to say there is an update available, or
			- calls for the download of the updates
			- calls for the installation of the updates 
			- restarts Kodi to implement changes
		The check for updates is done using the python-apt module. This module must be run as root, so is being called in
		external scripts from the command line using sudo. The other script communicates with the update service using a socket file.
	'''
	
	# MAIN METHOD
	def __init__(self):

		self.first_run = True

		# dictionary containing the permissable actions (communicated from the child apt scripts) 
		# and the corresponding methods in the parent
		self.action_dict = 	{
								'apt_cache update complete' : self.apt_update_complete,
								'apt_cache commit complete' : self.apt_commit_complete,
								'apt_cache fetch complete'  : self.apt_fetch_complete,
								'progress_bar'				: self.progress_bar,
								'update_settings'			: self.update_settings,
								'kill_yourself'				: self.kill_yourself,
								'call_child_script'			: self.call_child_script,

							}

		# queue for communication with the comm and Main
		self.parent_queue = Queue.Queue()

		self.randomid = random.randint(0,1000)

		# create socket, listen for comms
		self.listener = comms.communicator(self.parent_queue, socket_file='/var/tmp/osmc.settings.update.sockfile')
		self.listener.start()

		# grab the settings
		self.update_settings()

		# a class to handle scheduling update checks
		self.scheduler = sched.SimpleScheduler(self.s)
		log(self.scheduler.trigger_time, 'trigger_time')


		# monitor for identifying addon settings updates and kodi abort requests
		self.monitor = Monitah(parent_queue = self.parent_queue)

		# window onto which to paste the update notification
		self.window = xbmcgui.Window(10000)

		# property which determines whether the notification should be pasted to the window
		self.window.setProperty('OSMC_notification','false')

		# ControlImage(x, y, width, height, filename[, aspectRatio, colorDiffuse])
		self.update_image = xbmcgui.ControlImage(15, 55, 175, 75, __image_file__)
		self.window.addControl(self.update_image)
		self.update_image.setVisibleCondition('[SubString(Window(Home).Property(OSMC_notification), true, left)]')

		log(xbmc.getCondVisibility('SubString(Window(Home).Property(OSMC_notification), false, left)'), 'getCondVisibility')
		log(xbmc.getCondVisibility('SubString(Window(Home).Property(OSMC_notification), true, left)'), 'getCondVisibility')

		# this flag is present when updates have been downloaded but the user wants to reboot themselves manually via the settings
		# it is deleted using the 'setting_exit_install.py' script.
		self.block_update_file = '/var/tmp/.dont_install_downloaded_updates'
		if os.path.isfile(self.block_update_file):
			self.skip_update_check = True
		else:
			self.skip_update_check = False

		# a preliminary check for updates (for testing only)
		if self.s['check_onboot']:
			if not self.skip_update_check and self.s['check_freq'] != lang(32003):
				self.call_child_script('update')

		# keep alive method
		self._daemon()


	# MAIN METHOD
	def _daemon(self):

		log('_daemon started')

		self.keep_alive = True

		count = 0 	# FOR TESTING ONLY

		while self.keep_alive:

			# periodic announcement to confirm the service is alive
			# FOR TESTING ONLY
			if not count % 100:									# FOR TESTING ONLY
				log('blurp %s' % self.randomid)					# FOR TESTING ONLY
			count += 1 											# FOR TESTING ONLY
			# FOR TESTING ONLY

			# check queue for data
			try:
				# the only thing the script should be sent is a tuple ('instruction as string', data as dict),
				# everything else is ignored
				raw_comm_from_script = self.parent_queue.get(False)
				
				# tell the queue that we are done with the task at hand
				self.parent_queue.task_done()

				# de-serialise the message into its original tuple
				comm_from_script = json.loads(raw_comm_from_script)

				log(comm_from_script, 'comm_from_script')

				# process the information from the child scripts
				if comm_from_script:

					# retrieve the relevant method
					method = self.action_dict.get(comm_from_script[0], False)
					if method: 

						# call the appropriate method with the data
						method(**comm_from_script[1])

					else:

						log(comm_from_script, 'instruction has no assigned method')

			except Queue.Empty:
				# the only exception that should be handled is when the queue is empty
				pass

			# check for an early exit
			if not self.keep_alive: break

			# this controls the frequency of the instruction processing
			xbmc.sleep(500)


		# stop the listener
		self.listener.stop()
		# del self.listener
		# log('listener cleaned up')

		del self.monitor
		log('del self.monitor')
		del self.update_image
		log('del self.update_image')

		del self.window 
		log('del self.window')

		# self.takedown_notification()
		# log('notification control removed from window(10000)')

		log('XBMC Aborting')


	# MAIN METHOD
	def takedown_notification(self):
		log('taking down notification')

		try:
			self.window.removeControl(self.update_image)
		except Exception as e:
			log(e, 'an EXCEPTION occurred')


	# MAIN METHOD
	def call_child_script(self, action):
		
		log(action, 'calling child, action ')
		subprocess.Popen(['sudo', 'python','%s/apt_cache_action.py' % __libpath__, action])


	# MAIN METHOD
	def update_settings(self):

		''' Updates the settings for the service while the service is still running '''

		log('Updating Settings...')

		if self.first_run:

			''' Construct the settings dicionary '''

			self.first_run = False

			self.scheduler_settings = ['check_freq', 'check_weekday', 'check_day', 'check_time', 'check_hour', 'check_minute']
			self.icon_settings		= ['']
			
			self.s = {}

			self.s['check_onboot']		= True if 		__setting__('check_onboot') 		== 'true' else False
			self.s['check_freq'] 		= 				__setting__('check_freq')
			self.s['check_weekday'] 	= int(float(	__setting__('check_weekday')		))
			self.s['check_day'] 		= int(float(	__setting__('check_day')			))
			self.s['check_time'] 		= int(float(	__setting__('check_time')			))
			self.s['check_hour'] 		= int(float(	__setting__('check_hour')			))
			self.s['check_minute'] 		= int(float(	__setting__('check_minute')			))
			self.s['suppress_progress']	= True if 		__setting__('suppress_progress') 	== 'true' else False

			log(self.s, 'Initial Settings')

			return

		else:

			''' Construct a temporary dictionary for comparison with the existing settings dict '''

			tmp_s = {}

			tmp_s['check_onboot']		= True if 		__setting__('check_onboot') 	== 'true' else False
			tmp_s['check_freq'] 		= 				__setting__('check_freq')
			tmp_s['check_weekday'] 		= int(float(	__setting__('check_weekday')	))
			tmp_s['check_day'] 			= int(float(	__setting__('check_day')		))
			tmp_s['check_time'] 		= int(float(	__setting__('check_time')		))
			tmp_s['check_hour'] 		= int(float(	__setting__('check_hour')		))
			tmp_s['check_minute'] 		= int(float(	__setting__('check_minute')		))
			tmp_s['suppress_progress']	= True if 		__setting__('suppress_progress') 	== 'true' else False


		# flag to determine whether the update scheduler needs to be reconstructed
		update_scheduler = False

		# check the items in the temp dict and if they are differenct from the current settings, change the current settings,
		# prompt action if certain settings are changed (like the scheduler settings)
		for k, v in tmp_s.iteritems():

			if v == self.s[k]:
				continue
			else:
				self.s[k] = v
				update_scheduler = True

		# reconstruct the scheduler if needed
		if update_scheduler:
			self.scheduler = sched.SimpleScheduler(self.s)

		log(self.scheduler.trigger_time, 'trigger_time')


	# ACTION METHOD
	def progress_bar(self, **kwargs):

		''' Controls the creation and updating of the background prgress bar in kodi.
			The data gets sent from the apt_cache_action script via the socket
			percent, 	must be an integer
			heading,	string containing the running total of items, bytes and speed
			message, 	string containing the name of the package or the active process.
		 '''

		# return immediately if the user has suppressed on-screen progress updates or kwargs is empty
		if self.s['suppress_progress'] or not kwargs: return

		log(kwargs, 'kwargs')

		# check for kill order in kwargs
		kill = kwargs.get('kill', False)

		if kill:
			# if it is present, kill the dialog and delete it
			
			try:
				self.pDialog.close()
				del self.pDialog
			except:
				pass

			return

		# retrieve the necessary data for the progress dialog, if the data isnt supplied, then use 'nix' in its place
		# the progress dialog update has 3 optional arguments
		percent = kwargs.get('percent','nix')
		heading = kwargs.get('heading','nix')
		message = kwargs.get('message', 'nix')

		# create a dict of the actionable arguments
		keys = ['percent', 'heading', 'message']
		args = [percent, heading, message]
		update_args = {k:v for k, v in zip(keys, args) if v != 'nix'}

		# try to update the progress dialog
		try:
			log(update_args, 'update_args')
			self.pDialog.update(**update_args)

		except AttributeError:

			# on a AttributeError create the dialog and start showing it, the name error will be raised if pDialog doesnt exist

			self.pDialog = xbmcgui.DialogProgressBG()
			self.pDialog.create('OSMC Update', 'Update Running.')

			self.pDialog.update(**update_args)

		except Exception as e:

			# on any other error, just log it and try to remove the dialog from the screen 

			log(e, 'pDialog has encountered and error')

			try:
				self.pDialog.close()
				del self.pDialog
			except:
				# a name error here is not interesting
				pass


	# ACTION METHOD
	def kill_yourself(self):
		self.keep_alive = False 


	# ACTION METHOD
	def apt_commit_complete(self):

		# on commit complete, remove the notification from the Home window

		self.window.setProperty('OSMC_notification', 'false')


	# ACTION METHOD
	def apt_fetch_complete(self):

		log('apt_fetch_complete called')

		exit_install = DIALOG.yesno('OSMC Update Available', 'Updates have been downloaded, but Kodi will need to exit to install them.', 'Would you like to exit and install the updates now?')

		if exit_install:

			subprocess.Popen(['sudo', 'systemctl', 'start', 'update-manual'])

		else:
			okey = DIALOG.yesno('OSMC Update Available', 'Would you like to install the updates automatically on the next reboot,', 'or do you want to manually call the install from the OSMC settings?', yeslabel="Auto", nolabel="Manual")

			if okey: # auto install at next reboot

				try:
					# remove the file that blocks updates on reboot if it is present
					os.remove(self.block_update_file)

				except:
					pass

			else: # install the updates only when the user choose to from the settings
				
				# create the file that will prevent the installation of downloaded updates untill the user say so
				with open(self.block_update_file, 'w') as f:
					f.write('d')

				# trigger the flag to skip update checks
				self.skip_update_check = True

			self.window.setProperty('OSMC_notification', 'true')


	# ACTION METHOD
	def apt_update_complete(self):

		self.cache = apt.Cache()

		REBOOT_REQUIRED = 0

		log('apt_update_complete called')
		log('opening cache')

		self.cache.open(None)

		log('opened, upgrading cache')

		self.cache.upgrade()

		log('upgraded, getting changes')

		available_updates = self.cache.get_changes()

		if not available_updates: 
			log('There are no packages to upgrade')
			# DIALOG.ok('OSMC Update', 'There are no packages to upgrade')
			del self.cache
			return 		# if there are no updates then just return nothing

		log('The following packages have newer versions and are upgradable: ')

		for pkg in available_updates:
			if pkg.is_upgradable:

				log('is upgradeable', pkg.shortname)

				if "mediacenter" in pkg.shortname:
					REBOOT_REQUIRED = 1

		del self.cache

		# TESTING ONLY
		# REBOOT_REQUIRED = 1 # TESTING ONLY
		# TESTING ONLY

		if REBOOT_REQUIRED == 1:

			log("We can't upgrade from within Kodi as it needs updating itself")

			# Downloading all the debs at once require su access. So we call an external script to download the updates 
			# to the default apt_cache. That other script provides a progress update to this parent script, 
			# which is displayed as a background progress bar
			self.call_child_script('fetch')

		else:

			log("Updates are available, no reboot is required")

			self.window.setProperty('OSMC_notification', 'true')

			install = DIALOG.yesno('OSMC Update Available', 'There are updates that are available for install.', 'Would you like to install them now?')

			if install:

				self.call_child_script('commit') # Actually installs

				self.window.setProperty('OSMC_notification', 'false')

			else:

				okey_dokey = DIALOG.ok('OSMC Update Available', 'Fair enough, then.', 'You can install them from within the OSMC settings later.')


