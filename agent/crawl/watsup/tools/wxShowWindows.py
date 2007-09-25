#!/usr/bin/env python
#Boa:App:BoaApp

# Author     : Tim Couper - tim@tizmoi.net
# Date       : 1 August 2004
# Copyright  : Copyright TAC Software Ltd, under Python-like licence.
#              Provided as-is, with no warranty.
# Notes      : Requires watsup,wxPython

from wxPython.wx import *

import fmShowWindows

modules ={'fmShowWindows': [1, 'Main frame of Application', 'fmShowWindows.py']}

class BoaApp(wxApp):
    def OnInit(self):
        wxInitAllImageHandlers()
        self.main = fmShowWindows.create(None)
        self.main.Show()
        self.SetTopWindow(self.main)
        return True

def main():
    application = BoaApp(0)
    application.MainLoop()

if __name__ == '__main__':
    main()
