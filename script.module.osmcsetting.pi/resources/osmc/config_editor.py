# XBMC Modules
import xbmc
import xbmcaddon
import xbmcgui
import subprocess
import sys

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK      = 92
SAVE                 = 5
HEADING              = 1
ACTION_SELECT_ITEM   = 7

__addon__  = xbmcaddon.Addon("script.module.osmcsetting.pi")
scriptPath = __addon__.getAddonInfo('path')
DIALOG     = xbmcgui.Dialog()
IMAGE = os.path.join(scriptPath,'resources','osmc','FO_Icon.png')

def lang(id):
    san = __addon__.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return san 


class ConfigEditor(xbmcgui.WindowXMLDialog):


	def onInit(self):

		# give the settings enough time to be saved to the config.txt
		xbmc.sleep(150)

		self.del_string = ' [' + lang(32056) + ']'

		self.config = '/boot/config.txt'

		# FOR TESTINGS
		# self.config = '/home/kubkev/Documents/config.txt'

		with open(self.config, 'r') as f:
			self.lines = f.readlines()

		print 'coooooooooooooonfigeditor: ', self.lines

		self.lines = [line.replace('\n','') for line in self.lines if line not in ['\n', '', '\t']]

		# Save button
		self.ok = self.getControl(SAVE)
		self.ok.setLabel(lang(32050))

		# Heading
		self.hdg = self.getControl(HEADING)
		self.hdg.setLabel(lang(32051))
		self.hdg.setVisible(True)

		# Hide unused list frame
		self.x = self.getControl(3)
		self.x.setVisible(False)

		# Populate the list frame
		self.list_control      = self.getControl(6)

		self.items = [lang(32052)]
		self.items.extend(self.lines)

		self.item_count = len(self.items)

		# Start the window with the first item highlighted
		# self.list_control.getListItem(0).select(True)

		# Set action when clicking right from the Save button
		self.ok.controlRight(self.list_control)

		for i in self.items:
			# populate the random list
			self.tmp = xbmcgui.ListItem(i, thumbnailImage=IMAGE)
			self.list_control.addItem(self.tmp)

		self.setFocus(self.list_control)

	def onAction(self, action):
		actionID = action.getId()
		if (actionID in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK)):
			print 'coooooooooooooonfigeditor: CLOSE'
			self.close()

	def onClick(self, controlID):
		print 'coooooooooooooonfigeditor: ', controlID

		if controlID == SAVE:
			print 'coooooooooooooonfigeditor: SAVE'

			final_action = DIALOG.yesno(lang(32052), lang(32053), nolabel=lang(32054), yeslabel=lang(32055))

			if final_action:

				print 'coooooooooooooonfigeditor: final action'

				new_config = []

				for i in range(self.item_count):
					if i == 0: continue

					item = self.list_control.getListItem(i)

					currentlabel = item.getLabel()

					print currentlabel

					if self.del_string not in currentlabel:
						new_config.append(currentlabel)

				# temporary location for the config.txt
				tmp_loc = '/var/tmp/config.txt'

				# write the long_string_file to the config.txt
				with open(tmp_loc,'w') as f:
					for line in new_config:
						f.write(line.replace(" = ","=") + '\n')
						print 'coooooooooooooonfigeditor: ' + line

				# copy over the temp config.txt to /boot/ as superuser
				subprocess.call(["sudo", "mv", tmp_loc, self.config ])

				# THIS IS JUST FOR TESTING, LAPTOP DOESNT LIKE SUDO HERE
				try:
					subprocess.call(["mv", tmp_loc, self.config ])
				except:
					pass

				print 'coooooooooooooonfigeditor: writing ended'

			self.close()

		else:
			selected_entry = self.list_control.getSelectedPosition()
			item = self.list_control.getSelectedItem()
			currentlabel = item.getLabel()
			
			if selected_entry != 0:

				if self.del_string not in currentlabel:
					action = DIALOG.yesno(lang(32051), lang(32057), nolabel=lang(32058), yeslabel=lang(32059))

					if action:
						# delete
						item.setLabel(currentlabel + self.del_string)

					else:
						# edit
						d = DIALOG.input(lang(32060), currentlabel, type=xbmcgui.INPUT_ALPHANUM)

						if d:
							item.setLabel(d)

				else:
					action = DIALOG.yesno(lang(32051), lang(32061), nolabel=lang(32058), yeslabel=lang(32062))

					if action:
						# delete
						item.setLabel(currentlabel[:len(currentlabel) - len(self.del_string)])

					else:
						# edit
						d = DIALOG.input(lang(32063), currentlabel, type=xbmcgui.INPUT_ALPHANUM)

						if d:
							item.setLabel(d)

			else:
				d = DIALOG.input(lang(32064), type=xbmcgui.INPUT_ALPHANUM)

				self.list_control.addItem(xbmcgui.ListItem(d))

				self.item_count += 1




if __name__ == "__main__":

	print 'coooooooooooooonfigeditor: OPEN'
	CE = ConfigEditor("DialogSelect.xml", scriptPath, 'Default')
	
	CE.doModal()
	
	del CE

	print 'coooooooooooooonfigeditor: CLOSED'
	
	xbmc.sleep(150)

	__addon__.openSettings()
