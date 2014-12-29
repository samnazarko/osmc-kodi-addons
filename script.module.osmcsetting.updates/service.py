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
