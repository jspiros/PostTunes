#
#  PostTunesAppDelegate.py
#  PostTunes
#
#  Created by Joseph Spiros on 3/5/09.
#  Copyright iThink Software 2009. All rights reserved.
#

import objc
from urllib import urlencode
from urllib2 import urlopen, URLError
from base64 import b64encode
from PyObjCTools import AppHelper
from Foundation import *
from AppKit import *
from ScriptingBridge import *

class PostTunesAppDelegate(NSObject):
	preferencesWindow = objc.IBOutlet()
	warnFailure = objc.ivar(u"warnFailure")
	lastPersistentID = objc.ivar(u"lastPersistentID")
	handlerURL = objc.ivar(u"handlerURL")
	secretKey = objc.ivar(u"secretKey")
	
	def init(self):
		self = super(PostTunesAppDelegate, self).init()
		if not self:
			return None
		self.warnFailure = True
		self.lastPersistentID = None
		self.handlerURL = None
		self.secretKey = None
		return self
	
	def awakeFromNib(self):
		self.handlerURL = NSUserDefaults.standardUserDefaults().stringForKey_("handlerURL")
		self.secretKey = NSUserDefaults.standardUserDefaults().stringForKey_("secretKey")
		if not self.handlerURL:
			self.runConfigurationAlert_title_description_(None, "In order for PostTunes to post tracks, you must set a Handler URL. The optional Secret Key may be used by the script at the Handler URL to validate your posts.")
		self.observeNote()
	
	def runConfigurationAlert_title_description_(self, title, description):
		if not title:
			title = "PostTunes Configuration"
		alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(title, "OK", "Quit PostTunes", None, description)
		alert.setAccessoryView_(self.preferencesWindow.contentView().retain())
		alert.setAlertStyle_(NSCriticalAlertStyle)
		alertReturn = alert.runModal()
		if alertReturn == NSAlertDefaultReturn:
			self.handlerURL = NSUserDefaults.standardUserDefaults().stringForKey_("handlerURL")
			if not self.handlerURL:
				self.runConfigurationAlert_title_description_("PostTunes Handler URL Missing", "You must set a Handler URL for PostTunes to function.")
		elif alertReturn == NSAlertAlternateReturn:
			AppHelper.stopEventLoop()
	
	def observeNote(self):
		NSDistributedNotificationCenter.defaultCenter().addObserver_selector_name_object_(self, "gotNotification:", "com.apple.iTunes.playerInfo", None)
	
	def gotNotification_(self, notification):
		self.handlerURL = NSUserDefaults.standardUserDefaults().stringForKey_("handlerURL")
		self.secretKey = NSUserDefaults.standardUserDefaults().stringForKey_("secretKey")
		if notification:
			noteInfo = notification.userInfo()
			playerState = noteInfo["Player State"]
			if "PersistentID" in noteInfo:
				persistentID = noteInfo["PersistentID"]
				if (persistentID != self.lastPersistentID) and ("Name" in noteInfo):
					if playerState == "Playing":
						if self.handlerURL:
							# started playing a new track
							# get the applescript track and make sure it's the same (compare name)
							iTunes = SBApplication.applicationWithBundleIdentifier_("com.apple.iTunes")
							iTunesTrack = iTunes.currentTrack()
							if iTunesTrack.name() == noteInfo["Name"]:
								self.trackChanged_iTunesTrack_(noteInfo, iTunesTrack)
								self.lastPersistentID = persistentID
						else:
							self.runConfigurationAlert_title_description_("PostTunes Handler URL Missing", "PostTunes was unable to post a track due to the Handler URL being missing. You must set a Handler URL for PostTunes to function.")
								
			else:
				self.lastPersistentID = None
				# stopped playing
	
	def trackChanged_iTunesTrack_(self, noteInfo, iTunesTrack):
		trackData = {"title": noteInfo["Name"]}
		if self.secretKey:
			trackData["key"] = self.secretKey
		if "Artist" in noteInfo:
			trackData["artist"] = noteInfo["Artist"]
		if "Album" in noteInfo:
			trackData["album"] = noteInfo["Album"]
		if "Store URL" in noteInfo:
			trackData["url"] = noteInfo["Store URL"]
		iTunesArtworks = iTunesTrack.artworks()
		if len(iTunesArtworks) >= 1:
			artwork = iTunesArtworks[0]
			artworkTIFF = artwork.data().TIFFRepresentation()
			artworkPNG = NSBitmapImageRep.imageRepWithData_(artworkTIFF).representationUsingType_properties_(NSPNGFileType, None)
			trackData["artpng"] = b64encode(artworkPNG.bytes())
		try:
			urlopen(self.handlerURL, urlencode(trackData))
		except URLError:
			description = (u"PostTunes encountered an error when attempting to post the track \"%s\" to your Handler URL." % trackData["title"])
			NSLog(u"%s Handler URL: %s" % (description, self.handlerURL))
			if self.warnFailure:
				alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_("PostTunes Could Not Post Track", "OK", "Configure PostTunes", "Quit PostTunes", description)
				alert.setAlertStyle_(NSCriticalAlertStyle)
				alert.setShowsSuppressionButton_(True)
				alertReturn = alert.runModal()
				if alert.suppressionButton().state() == NSOnState:
					self.warnFailure = False
				if alertReturn == NSAlertAlternateReturn:
					self.runConfigurationAlert_title_description_(None, (u"%s Please confirm your Handler URL." % description))
				elif alertReturn == NSAlertOtherReturn:
					AppHelper.stopEventLoop()
