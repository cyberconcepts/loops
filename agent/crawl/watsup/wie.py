# provides a testing interface to web applications via the PAMIE module

# Author     : Tim Couper - timc@tizmoi.net
# Date       : 22 July 2004
# Version    : 1.0 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.

from cPAMIE import PAMIE

def findRunningIE():
    from win32com.client import Dispatch 
    from win32gui import GetClassName

    ShellWindowsCLSID = '{9BA05972-F6A8-11CF-A442-00A0C90A8F39}'
    ShellWindows = Dispatch ( ShellWindowsCLSID )
    
    # try to get an ie instance from the window
    for shellwindow in ShellWindows :
        if GetClassName ( shellwindow.HWND ) == 'IEFrame' :
            return shellwindow 

class WatsupIE(PAMIE):
    def __init__(self,url=None, timeOut=1000, useExistingIfPossible=False):
        
        self._ie=None 
        
        if useExistingIfPossible:
            self._ie=findRunningIE()
               
        if self._ie:
            # this case can only arise if we've located a running IE;
            
            # the code below should be everything else in PAMIE.__init__, 
            # apart from instantiation of the new ie instance:
            if url:
                self._ie.Navigate(url)
            else:
                self._ie.Navigate('about:blank')
            self._timeOut = timeOut
            self._ie.Visible = 1 
        else:
            PAMIE.__init__(self,url,timeOut)    
    
            