""" watsup system utilities
"""

# Author     : Tim Couper - timc@tizmoi.net
# Date       : 22 July 2004
# Version    : 1.0 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.
# Notes      : Requires win32all

import win32gui
import win32api
import sys

class WatsupError(Exception): pass

##def kill(pid):

##    """kill function for Win32"""

##    handle = win32api.OpenProcess(1, 0, pid)

##    return (0 != win32api.TerminateProcess(handle, 0))

def dumpHwnd(hwnd):
    t=list(tupleHwnd(hwnd))
    t.reverse()
    return '%s:"%s" (%d)' % tuple(t) #(win32gui.GetClassName(hwnd),win32gui.GetWindowText(hwnd),hwnd)

def tupleHwnd(hwnd):
    return (hwnd,win32gui.GetWindowText(hwnd),win32gui.GetClassName(hwnd))

def pump():
    win32gui.PumpWaitingMessages()    

if __name__=='__main__':
    pass