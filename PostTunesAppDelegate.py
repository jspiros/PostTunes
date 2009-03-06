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
from Foundation import *
from AppKit import *
from ScriptingBridge import *

class PostTunesAppDelegate(NSObject):
	preferencesWindow = objc.IBOutlet()
	warnPreferences = objc.ivar(u"warnPreferences")
	warnFailure = objc.ivar(u"warnFailure")
	lastPersistentID = objc.ivar(u"lastPersistentID")
	handlerURL = objc.ivar(u"handlerURL")
	secretKey = objc.ivar(u"secretKey")
	
	def init(self):
		self = super(PostTunesAppDelegate, self).init()
		if not self:
			return None
		self.warnPreferences = True
		self.warnFailure = True
		self.lastPersistentID = None
		self.handlerURL = None
		self.secretKey = None
		self.observeNote()
		return self
	
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
							NSLog(u"Track Not Posted: You have not provided PostTunes with the Handler URL to use.")
							if self.warnPreferences:
								alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_("Track Not Posted", "Open PostTunes Preferences", "Ignore", None, u"You have not provided PostTunes with the Handler URL to use.")
								if alert.runModal() == NSAlertDefaultReturn:
									self.preferencesWindow.makeKeyAndOrderFront_(self)
								elif alert.runModal() == NSAlertAlternateReturn:
									self.warnPreferences = False
								
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
			NSLog(u"PostTunes encountered an error when attempting to submit a track to: %s" % self.handlerURL)
			if self.warnFailure:
				alert = NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_("Track Not Posted", "Open PostTunes Preferences", "Ignore", None, (u"PostTunes encountered an error when attempting to submit a track to:\n%s" % self.handlerURL))
				if alert.runModal() == NSAlertDefaultReturn:
					self.preferencesWindow.makeKeyAndOrderFront_(self)
				elif alert.runModal() == NSAlertAlternateReturn:
					self.warnFailure = False
