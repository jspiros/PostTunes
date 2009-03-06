#
#  main.py
#  PostTunes
#
#  Created by Joseph Spiros on 3/5/09.
#  Copyright iThink Software 2009. All rights reserved.
#

#import modules required by application
import objc
import Foundation
import AppKit

from PyObjCTools import AppHelper

# import modules containing classes required to start application and load MainMenu.nib
import PostTunesAppDelegate

# pass control to AppKit
AppHelper.runEventLoop()
