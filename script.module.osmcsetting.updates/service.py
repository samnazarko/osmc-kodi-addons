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
import subprocess
import Queue

# Kodi Modules
import xbmc
import xbmcaddon
import xbmcgui

# Custom modules
sys.path.append(xbmc.translatePath(os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources','lib')))
import comms

__addon__              = xbmcaddon.Addon()
__addonid__            = __addon__.getAddonInfo('id')
__scriptPath__         = __addon__.getAddonInfo('path')
__setting__            = __addon__.getSetting
__image_file__         = os.path.join(__scriptPath__,'resources','media','update_available.png')

DIALOG = xbmcgui.Dialog()
TIME_BETWEEN_CHECKS = 3600 # SECONDS


def log(message, label = ''):
	logmsg       = '%s : %s - %s ' % (__addonid__ , str(label), str(message))
	xbmc.log(msg = logmsg)


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

		# dictionary containing the permissable actions (communicated from the child apt scripts) 
		# and the corresponding methods in the parent
		self.action_dict = 	{
								'apt_cache update complete' : self.apt_update_complete,
								'apt_cache commit complete' : self.apt_commit_complete,
							}


		# queue for communication with the comm and Main
		self.parent_queue = Queue.Queue()

		# create socket, listen for comms
		self.listener = comms.communicator(self.parent_queue, socket_file='/var/tmp/osmc.settings.update.sockfile')
		self.listener.start()

		# monitor for identifying addon settings updates and kodi abort requests
		self.monitor = xbmc.Monitor()

		# window on which to paste the update notification
		self.window = xbmcgui.Window(10000)

		# property which determines whether the notification should be pasted to the window
		self.window.setProperty('OSMC_notification','false')

		# ControlImage(x, y, width, height, filename[, aspectRatio, colorDiffuse])
		self.update_image = xbmcgui.ControlImage(15, 55, 350, 150, __image_file__)
		self.update_image.setVisibleCondition('!System.ScreenSaverActive')

		# attribute that records whether the image is being displayed or not
		self.displayed = False

		# the time of the last check for updates
		self.last_check = datetime.now()

		# a preliminary check for updates (for testing only)
		self.check_for_updates(do_it_now=True)

		# keep alive method
		self._daemon()


	def _daemon(self):

		log('_daemon started')

		count = 0

		# while not xbmc.abortRequested:
		while True:

			log('blurp')

			if not count % 100:
				log(count, '_daemon still alive')
				count += 1
			
			# check whether the notification should be posted or removed
			self.check_notification()

			# check queue, see if there is any data
			try:
				raw_comm_from_script = self.parent_queue.get(False)
			except:
				raw_comm_from_script = False 

			if raw_comm_from_script:

				log(raw_comm_from_script, 'raw_comm_from_script')

				# process the information from the child scripts
				if raw_comm_from_script:
					method = self.action_dict.get(raw_comm_from_script, False)
					if method: method()

			# check for updates each second
			self.check_for_updates()

			if self.monitor.waitForAbort(1):
				break

		log('XBMC Aborting')
		self.takedown_notification()
		self.listener.stop()


	def apt_commit_complete(self):

		self.window.setProperty('OSMC_notification', 'false')


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

		if REBOOT_REQUIRED == 1:

			log("We can't upgrade from within Kodi as it needs updating itself")

			# okey_dokey = DIALOG.ok('OSMC Reboot Required','There are updates available.', 'OSMC needs to be rebooted to complete installation.')
			
		else:

			log("Upgrading!")

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
		except:
			pass


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
	
		tdelta = datetime.now() - self.last_check

		if tdelta.total_seconds() > TIME_BETWEEN_CHECKS or do_it_now:

			#this is here for testing
			self.window.setProperty('OSMC_notification', 'false')
			
			log(do_it_now, 'Checking for updates, do_it_now')

			self.last_check = datetime.now()

			self.call_child_script('update')

	
	def call_child_script(self, action):
		
		# try:
		log(action, 'calling child, action ')
		# subprocess.check_output(['sudo', 'python','/home/kubkev/.kodi/addons/script.module.osmcsetting.updates/resources/lib/apt_cache_action.py', action])
		subprocess.call(['sudo', 'python','/home/kubkev/.kodi/addons/script.module.osmcsetting.updates/resources/lib/apt_cache_action.py', action])
		
		# except subprocess.CalledProcessError as CPE:  

		# 	log(CPE.returncode, 'subprocess, return code: ')                                                                                                 
		# 	log(CPE.output, 'subprocess, output: ')


if __name__ == "__main__":

	m = Main()
	del m.monitor
	del m.window 
	del m.update_image
	del m
