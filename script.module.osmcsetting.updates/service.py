# declare file encoding
# -*- coding: utf-8 -*-

#  Copyright (C) 2014 KodeKarnage
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html

'''

Most Important: Updates will never happen without the user's say so, ever.
The Update module controls the settings for a service that periodically checks if an Update is available.
The user can choose a time to check the server, as well as the frequency of the check.
The user can elect to not have any Update check done.
The user will be notified of an Update being available by a notification.
This notification should take the form of a persistent, periodic, discrete, on-screen icon that displays on the Home screen only.
The user can turn off the on-screen notification, but it is on by default.
The user can re-position the notification. (To accommodate different skins.)
The user can nominate an email address, to which the addon will send a notification of an update being available. (This would help people who are maintaining OSMC for family.)
The user can elect to download the update, but not apply it until a time of their choosing.
The user can nominate a location on their media server to store the downloaded Update. (Allowing for easy updates on products with not internet access.)
User can see the packages that will be updated the next major update
The user can select update every package, or only major releases (or never)
User can select their own update icon and position.


'''
'''
UPDATE settings

allow updates:
NO 
YES
	- UPDATE ALL PACKAGES 
	- ONLY MAJOR UPDATES 
	- ONLY DOWNLOAD THE UPDATES, I WILL MANUALLY RUN THE INSTALL MYSELF
		- INSTALL DOWNLOADED UPDATES 
		- INSTALL SELECTED UPDATES 
	- MANUALLY CHECK FOR UPDATES
		- DOWNLOAD AND INSTALL SELECTED UPDATES 

	check for updates:
	NEVER
	HOURLY
	DAILY
	WEEKLY
		- set time to check 

	show notification in HOME:
	NO 
	YES
		- CHOOSE NOTIFICATION 
		- POSTION NOTIFICATION
		- CHOOSE DURATION
		- CHOOSE CYCLE
		- SUPPRESS NOTIFICATION FOR XX TIME 

	SUPPRESS ON-SCREEN PROGRESS BAR DURING DOWNLOAD AND INSTALL

	email me when update is available:
	NO 
	YES
		- email address
		- provide list of updated packages

	email me when an update is completed:
		- provide list of updated packages

	email me 

	save updates to specific folder:
	NO 
	YES
		- specify folder

	observe packages ready for install:
		UPDATE NOW

	auto-reboot after update:
	NO 
	YES

	REVERT PREVIOUS UPDATE
		- SELECT SPECIFIC UPDATES 
		- REVERT TO SPECIFIC DATE
			(does this require keeping a text doc or db with the package names and install date?)

	LIMIT THE SPEED OF DOWNLOADS:
		- set speed (kbps)


FUNCTIONS NEEDED

 - check updates
 - download updates 
 - install updates
 - revert updates
 - onscreen notification
 - onscreen progress notification 
 - check if reboot recquired to continue
 - check to see if the recquired space is available
 - 


 WHEN THERE IS AN UPDATE THAT CAN ONLY BE INSTALLED WITH KODI CLOSED: 
 	- just tell me about it
 	- automatically install if between these times '''

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

TIME_BETWEEN_CHECKS = 3600 # SECONDS


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

	''' This service checks for new updates, then:
			- posts a notification on the home screen to say there is an update available, or
			- downloads the updates
			- installs the updates 
			- restarts Kodi to implement changes
		The check for updates is done using the python-apt module. This module must be run as root, so is being called in
		external scripts from the command line using sudo. The other script communicates with the update service using a socket file.
	'''
	

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

		# window on which to paste the update notification
		self.window = xbmcgui.Window(10000)

		# property which determines whether the notification should be pasted to the window
		self.window.setProperty('OSMC_notification','false')

		# ControlImage(x, y, width, height, filename[, aspectRatio, colorDiffuse])
		self.update_image = xbmcgui.ControlImage(15, 55, 350, 150, __image_file__)
		self.update_image.setVisibleCondition('!System.ScreenSaverActive')

		# this flag is present when updates have been downloaded but the user wants to reboot themselves manually via the settings
		# it is deleted using the 'setting_exit_install.py' script.
		self.block_update_file = '/var/tmp/.dont_install_downloaded_updates'
		if os.path.isfile(self.block_update_file):
			self.skip_update_check = True
		else:
			self.skip_update_check = False

		# attribute that records whether the image is being displayed or not
		self.displayed = False

		# a preliminary check for updates (for testing only)
		if self.s['check_onboot']:
			if not self.skip_update_check and self.s['check_freq'] != lang(32003):
				self.check_for_updates(do_it_now=True)

		# keep alive method
		self._daemon()


	def progress_bar(self, **kwargs):

		log(kwargs, 'kwargs')

		kill = kwargs.get('kill', False)

		if kill:
			
			try:
				self.pDialog.close()
				del self.pDialog
			except:
				pass

			return

		percent = kwargs.get('percent','nix')
		heading = kwargs.get('heading','nix')
		message = kwargs.get('message', 'nix')

		keys = ['percent', 'heading', 'message']
		args = [percent, heading, message]
		update_args = {k:v for k, v in zip(keys, args) if v != 'nix'}

		try:
			log(update_args, 'update_args')
			self.pDialog.update(**update_args)

		except:

			self.pDialog = xbmcgui.DialogProgressBG()
			self.pDialog.create('OSMC Update', 'Update Running.')

			self.progress_bar(**update_args)


	def update_settings(self):

		log('Updating Settings...')


		if self.first_run:
			self.first_run = False

			self.scheduler_settings = ['check_freq', 'check_weekday', 'check_day', 'check_time', 'check_hour', 'check_minute']
			
			self.s = {}

			self.s['check_onboot']		= True if 		__setting__('check_onboot') 	== 'true' else False
			self.s['check_freq'] 		= 				__setting__('check_freq')
			self.s['check_weekday'] 	= int(float(	__setting__('check_weekday')	))
			self.s['check_day'] 		= int(float(	__setting__('check_day')		))
			self.s['check_time'] 		= int(float(	__setting__('check_time')		))
			self.s['check_hour'] 		= int(float(	__setting__('check_hour')		))
			self.s['check_minute'] 		= int(float(	__setting__('check_minute')		))

			log(self.s, 'Initial Settings')

			return

		else:

			tmp_s = {}

			tmp_s['check_onboot']		= True if 		__setting__('check_onboot') 	== 'true' else False
			tmp_s['check_freq'] 		= 				__setting__('check_freq')
			tmp_s['check_weekday'] 		= int(float(	__setting__('check_weekday')	))
			tmp_s['check_day'] 			= int(float(	__setting__('check_day')		))
			tmp_s['check_time'] 		= int(float(	__setting__('check_time')		))
			tmp_s['check_hour'] 		= int(float(	__setting__('check_hour')		))
			tmp_s['check_minute'] 		= int(float(	__setting__('check_minute')		))


		update_scheduler = False

		for k, v in tmp_s.iteritems():

			if v == self.s[k]:
				continue
			else:
				self.s[k] = v
				update_scheduler = True

		if update_scheduler:
			self.scheduler = sched.SimpleScheduler(self.s)

		log(self.scheduler.trigger_time, 'trigger_time')


	def kill_yourself(self):
		self.keep_alive = False 


	def _daemon(self):

		log('_daemon started')

		self.keep_alive = True

		while self.keep_alive:
		# while True:

			log('blurp %s' % self.randomid)

			# check whether the notification should be posted or removed
			self.check_notification()

			# check queue, see if there is any data
			try:
				# the only thing the script should be sent is a tuple ('instruction as string', data)
				raw_comm_from_script = self.parent_queue.get(False)
				comm_from_script = json.loads(raw_comm_from_script)
				log(comm_from_script, 'comm_from_script')

			except:
				comm_from_script = False 

			if comm_from_script:

				log(comm_from_script, 'comm_from_script')

				# process the information from the child scripts
				if comm_from_script:
					method = self.action_dict.get(comm_from_script[0], False)
					if method: 
						log(comm_from_script[1],'comm_from_script[1]')
						method(**comm_from_script[1])

			# check for updates each second :;: TESTING only (normal updates are only called by the scheduler or by the user)
			# if not self.skip_update_check and self.s['check_freq'] != lang(32003):
			# 	self.check_for_updates()

			# check for an early exit
			if not self.keep_alive: break

			xbmc.sleep(500)


		self.listener.stop()
		# del self.listener
		# log('del self.listener')

		# del self.monitor
		# log('del self.monitor')

		self.takedown_notification()
		log('self.takedown_notification()')

		# del self.update_image
		# log('del self.update_image')

		# del self.window 
		# log('del self.window')

		log('XBMC Aborting')


	def apt_commit_complete(self):

		self.window.setProperty('OSMC_notification', 'false')


	def apt_fetch_complete(self):

		log('apt_fetch_complete called')

		exit_install = DIALOG.yesno('OSMC Update Available', 'Updates have been downloaded, but Kodi will need to exit to install them.', 'Would you like to exit and install the updates now?')

		if exit_install:
			subprocess.Popen('sudo systemctl start update-manual')

		else:
			okey = DIALOG.yesno('OSMC Update Available', 'Would you like to install the updates automatically on the next reboot,', 'or do you want to manually call the install from the OSMC settings?', yeslabel="Auto", nolabel="Manual")

			if okey: # auto install at next reboot

				try:
					# remove the file that blocks updates on reboot
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

		# non_downloadable_updates = []

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


	def post_notification(self):
		log('posting notification')

		self.displayed = True
		self.window.addControl(self.update_image)


	def takedown_notification(self):
		log('taking down notification')

		self.displayed = False
		try:
			self.window.removeControl(self.update_image)
		except Exception as e:
			log(e, 'an EXCEPTION occurred')


	def check_notification(self):

		if self.window.getProperty('OSMC_notification') == 'true' and not self.displayed:
			#posts notification if update is available and notification is not currently displayed
			self.post_notification()

		elif self.window.getProperty('OSMC_notification') == 'false' and self.displayed:
			#removes the notification if a check reveals there is no notification (should not be needed, but just in case)
			self.takedown_notification()

		return


	def check_for_updates(self, do_it_now=False):
		''' Checks whether the installed packages are upgradeable. 
			This is part 1; calls an external script to update the apt cache. '''
	
		#this is here for testing
		self.window.setProperty('OSMC_notification', 'false')
		
		log(do_it_now, 'Checking for updates, do_it_now')

		self.call_child_script('update')

	
	def call_child_script(self, action):
		
		# try:
		log(action, 'calling child, action ')
		subprocess.Popen(['sudo', 'python','%s/apt_cache_action.py' % __libpath__, action])
		
		# subprocess.check_output(['sudo', 'python','/home/kubkev/.kodi/addons/script.module.osmcsetting.updates/resources/lib/apt_cache_action.py', action])
		# os.system('sudo python /home/kubkev/.kodi/addons/script.module.osmcsetting.updates/resources/lib/apt_cache_action.py %s' % action)
		# except subprocess.CalledProcessError as CPE:  

		# 	log(CPE.returncode, 'subprocess, return code: ')                                                                                                 
		# 	log(CPE.output, 'subprocess, output: ')


if __name__ == "__main__":

	m = Main()
	del m
