""" launch & terminate a windows application
"""

# Author     : Tim Couper - tim@2wave.net
# Date       : 22 July 2004
# Version    : 1.0 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.
# Notes      : Requires Python 2.3, win32all, ctypes, SendKeys & winGuiAuto 


import os.path
import threading
import win32gui
#import win32api
#import win32con
import SendKeys
from watsup.utils import WatsupError
from watsup.winGuiAuto import findTopWindow,findTopWindows, \
                              WinGuiAutoError,activateMenuItem 

MENU_TERMINATIONS=[('file', 'exit'),('file', 'quit')]

def launchApp(program,wantedText=None,wantedClass=None,verbose=False):
    global p
    p=AppThread(program,verbose)
    p.start()
    try:
        return findTopWindow(wantedText=wantedText,wantedClass=wantedClass)
    except WinGuiAutoError,e:
        pass
    
    # find all the Windows that are lurking about, and terminate them
    # this I can't do until terminateApp can find a window and bring it to focus
    # for now, find one top window and return that; if there are none, 
    # it should raise an exception
    try:
        return findTopWindows(wantedText=wantedText,wantedClass=wantedClass)[0] 
    except IndexError:
        raise WatsupError,'Failed to find any windows'
         
class AppThread(threading.Thread):
    def __init__(self,program,verbose=False):
        threading.Thread.__init__(self,name=program)
        self.program=program
        self.verbose=verbose
        
    def run(self):
        """main control loop"""
        #check the given program exists, and is a file:
        # if the program has no type, make it .exe:
        if os.path.splitext(self.program)[1]=='':
            prog='%s.exe' % self.program
        else:
            prog=self.program    
        
        prog=os.path.abspath(prog)
        
        if os.path.isfile(prog):
            # launch the new application in a separate thread  
            if self.verbose:
                print '..launching "%s"' % prog
            os.system('"%s"' % prog)
            
        else:
            print 'AppThread: program not found: "%s"\n' % prog    
        
        if self.verbose:
                print '..terminating "%s"' % prog     

    
def terminateApp(hwnd=None): 
    """Terminate the application by:
    If there's a file-exit menu, click that
    If there's a file-Quit menu, click that
    Otherwise, send Alt-F4 to the current active window
** it's the calling program responsibility to get the right active window 
    """
    if hwnd:
        for fileExit in MENU_TERMINATIONS:
            try:
                activateMenuItem(hwnd, fileExit)
                return
            except WinGuiAutoError:
                pass
    
    # blast the current window with ALT F4 ..
    SendKeys.SendKeys("%{F4}")
    #win32gui.PumpWaitingMessages()
##    from watsup.winGuiAuto import findControl,findTopWindows
##    topHs=findTopWindows(wantedText='MyTestForm')
##    for topH in topHs:
##        #hwnd=findControl(topH)
##        a=win32gui.findWindow(topH)
##        print a, topH
##        win32gui.SetFocus(topH)
##        win32gui.PumpWaitingMessages()
##        SendKeys.SendKeys("%{F4}")
##        

##    if not hwnd and (wantedText or wantedClass):
##        hwnds=findTopWindows(wantedText=wantedText,wantedClass=wantedClass)            
##    elif hwnd:
##        hwnds=[hwnd]
##    
##    if hwnds:
##        for hwnd in hwnds:    
##            #win32gui.SetFocus(hwnd) 
##            #win32gui.SetActiveWindow(hwnd)   
##            # mm the above don;t work, perhaps because the 
##            # window is actually to be found in another thread
##               
##            SendKeys.SendKeys("%{F4}")
    
if __name__=='__main__':
    pass