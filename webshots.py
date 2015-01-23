#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Create Web page with common browser resolutions for given URL and save them as
# PNG files in current working directory.
#
# Requires PhantomJS: http://phantomjs.org/
# Written by Ramiro Gómez http://ramiro.org/
# MIT licensed: http://rg.mit-license.org/

import argparse, os
from subprocess import call

phantomscript = os.path.join(os.path.dirname(__file__), 'webshots.js')

# common screen resolutions from gs.statcounter.com
resolutions = [
    [1440, 900], [1366, 768], [1280, 1024], [1280, 800], [1024, 768], # web
    [800, 600], [480, 800], [360, 640], [320, 480], [240, 320] # mobile
]

call(['phantomjs', phantomscript, 'http://www.cs.odu.edu', '1024', '768', 'odu', 'filename'])

#p1 solved in timeout
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/19981206020810/http://www.weather.com/twc/homepage.twc', '1440', '900'])#redirectUrl
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/19990202193156/http://weather.com/', '1440', '900'])#yields redirectUrl, resolved through redirect.js
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/19990208010830/http://weather.com/', '1440', '900'])# from location through curl -I, rendered


#p2
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/20040113144126/http://www.w2.weather.com/common/jump.html?/', '1440', '900'])#yields unable to load, fail
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/20031231213644/http://www.w2.weather.com/common/jump2.html?/', '1440', '900'])# location from header

#p3
#call(['phantomjs', phantomscript, 'http://wayback.archive-it.org/all/20120101231316/http://www.weather.com/', '1440', '900'])# error in page

#p4
#call(['phantomjs', phantomscript, 'http://wayback.vefsafn.is/wayback/20000620180259/http://www.cnn.com/', '1440', '900'])# href attached to click on dormant redirect page: http://wayback.vefsafn.is/wayback/20000620180259/http://cnn.com/ 

#call(['phantomjs', phantomscript, 'http://web.archive.org/web/20031231213644/http://www.w2.weather.com/common/jump.html?/', '1440', '900'])#from curl location

#/web/20031231213644/http://www.w2.weather.com/common/jump2.html?/
#call(['phantomjs', phantomscript, 'http://web.archive.org/web/19981203143139/http://www.cs.odu.edu/', '1440', '900'])

