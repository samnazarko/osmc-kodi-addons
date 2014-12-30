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
 - '''

# Standard Modules
import apt
from datetime import datetime
import os

# Kodi Modules
import xbmc
import xbmcaddon
import xbmcgui

__addon__              = xbmcaddon.Addon()
__addonid__            = __addon__.getAddonInfo('id')
__scriptPath__         = __addon__.getAddonInfo('path')
__setting__            = __addon__.getSetting
__image_file__         = os.path.join(__scriptPath__,'resources','media','update_available.png')

DIALOG = xbmcgui.Dialog()
TIME_BETWEEN_CHECKS = 300 # SECONDS


def log(message, label = ''):
	logmsg       = '%s : %s - %s ' % (__addonid__ , str(label), str(message))
	xbmc.log(msg = logmsg)


class Main(object):
	

	def __init__(self):

		self.cache = apt.Cache()
		self.monitor = xbmc.Monitor()
		self.last_check = datetime.now()

		self.check_for_updates(do_it_now=True)

		self.window = xbmcgui.Window(10000)
		self.window.setProperty('OSMC_notification','false')

		# ControlImage(x, y, width, height, filename[, aspectRatio, colorDiffuse])
		self.update_image = xbmcgui.ControlImage(15, 55, 350, 150, __image_file__)

		self.displayed = False

		self._daemon()


	def _daemon(self):

		log('_daemon started')

		while True:

			if self.monitor.waitForAbort(1):
				log('XBMC Aborting')
				self.takedown_notification()
				break

			if self.window.getProperty('OSMC_notification') == 'true' and not self.displayed:
				#posts notification if update is available and notification is not currently displayed
				self.post_notification()

			elif self.window.getProperty('OSMC_notification') == 'false' and self.displayed:
				#removes the notification if a check reveals there is no notification (should not be needed, but just in case)
				self.takedown_notification()

			else:
				self.check_for_updates()


	def post_notification(self):
		log('posting notification')

		self.displayed = True
		self.window.addControl(self.update_image)
		self.update_image.setVisibleCondition('!System.ScreenSaverActive')


	def takedown_notification(self):
		log('taking down notification')

		self.displayed = False
		self.window.removeControl(self.update_image)


	def check_for_updates(self, do_it_now=False):
		''' Checks whether the installed packages are upgradeable '''
	
		tdelta = datetime.now() - self.last_check

		if tdelta.total_seconds() > TIME_BETWEEN_CHECKS or do_it_now:
			
			log('Checking for updates')

			self.last_check = datetime.now()

			self.cache.update()
			self.cache.open(None)
			self.cache.upgrade()
			
			log("The following packages have newer versions and are upgradable:")

			REBOOT_REQUIRED=0

			available_updates = cache.get_changes()

			if available_updates:

				self.window.setProperty('OSMC_notification', 'true')

				for pkg in available_updates:

					if pkg.is_upgradable:

						log('upgradeable', pkg.shortname)

						if "mediacenter" in pkg.shortname:
							REBOOT_REQUIRED=1

				if REBOOT_REQUIRED == 1:

					log("We can't upgrade from Kodi as it needs updating itself")

					ok = DIALOG.ok('OSMC Reboot Required','There are updates available.', 'OSMC needs to be rebooted to complete installation.')
					
				else:

					log("Upgrading!")

					install = DIALOG.yesno('OSMC Update Available', 'There are updates that are available for install.', 'Would you like to install them now?')
					
					if install:
						cache.commit() # Actually installs

						self.window.setProperty('OSMC_notification', 'false')


if __name__ == "__main__":

	Main()
