""" Class and functions to find the windowText and className for a given executable
"""

# Author     : Tim Couper - tim@2wave.net
# Date       : 22 July 2004
# Version    : 1.1 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.
# Notes      : Requires Python 2.3, win32all, ctypes & watsup package

import os.path

from watsup.winGuiAuto import findTopWindows,findControls,dumpWindow,\
                       dumpTopWindows
from watsup.utils import dumpHwnd,tupleHwnd
from watsup.launcher import AppThread,terminateApp
from watsup.OrderedDict import OrderedDict
from time import time,sleep
from types import ListType

THREAD_TIMEOUT_SECS=2.0
INDENT=2

#wstruct is of the form [hwnd,wclass,wtext] or
#                       [hwnd,wclass,wtext,[winstruct]

##def printwstruct(wstruct):
##    print 'printFormat had trouble with:\n%s' % str(wstruct[3])        
##    import pprint
##    print '------'
##    pprint.pprint(wstruct)
##    print '------' 
    
def printFormat(wstruct,indent=0):
    def printwstruct(wstruct):
        print 'printFormat had trouble with:\n%s' % str(wstruct[3])        
        import pprint
        print '------'
        pprint.pprint(wstruct)
        print '------' 
    """wstruct is either a wintuple, or a recursive list of wintuples
    """   
    
    # type 1
    if type(wstruct[1]) is not ListType:        
        print '%s%s: %s' % (' '*indent,wstruct[2],wstruct[1])  
        if len(wstruct)>3 and wstruct[3]<>None:        
            try:            
                for item in wstruct[3]:
                    printFormat(item,indent+INDENT)
            except:
                print_wstruct(wstruct)
    # type 2:
    else:
        for item in wstruct[1]:
            printFormat(item,indent+INDENT)           
                
        
class AppControls(object):
    def __init__(self,program,wantedText=None,wantedClass=None,selectionFunction=None,verbose=False):
        
        self.wantedText=wantedText
        self.wantedClass=wantedClass
        self.selectionFunction=selectionFunction
        
        self.verbose=verbose
        
        topHwnds,unwantedHwnds,self.appThread=findAppTopWindows(program,verbose=verbose) #should only be one, but you never know
                
        self.topHwnds=[]           
        self.unwantedHwnds=unwantedHwnds
        
    def run(self):
        while self.appThread.isAlive():        
            results=findNewTopWindows(self.unwantedHwnds,self.verbose)                
            if results:               
                self.process(results) # update the list of topWindows and unwanted TopWindows                
  
    def process(self,results):                      
        for hwnd in results:
            
            ctHwnds=findControls(hwnd)                              
            if ctHwnds:
                # we only add hwnd if there are controlHwnds
                # as there may be a form which exists
                # as an hwnd, but has not controls materialised yet
                self.unwantedHwnds.append(hwnd)                 
                self.write(hwnd)
                for ctHwnd in ctHwnds:
                    self.unwantedHwnds.append(ctHwnd)
    
    def write(self,hwnd):
        h=tupleHwnd(hwnd)
        t=[h[0],h[1],h[2],dumpWindow(hwnd)]
        printFormat(t)
   
def findNewTopWindows(unwantedHwnds=[],verbose=False):
    # returns a list of all top windows' hwnds we haven't
    # found yet
    htuples=dumpTopWindows()
    
    if verbose:
        print '..%d windows found (%d windows in unwanted)' % (len(htuples),len(unwantedHwnds))   
    results=[]
    for htuple in htuples:
        hwnd=htuple[0]
        if hwnd not in unwantedHwnds:         
            if verbose:
                print '..adding %s' % dumpHwnd(hwnd)
            results.append(hwnd)
                 
    return results

def findAppTopWindows(program,verbose=False):
    """returns the hwnds for the program, along with the hwnds for the 
    stuff that are to be ignored
    """
       
    # first we run findTopWindows before launching the program; store the hwnds found
    # (note that it doesn't matter if an instance of the program IS running
    # as we'll start another one whose hwnds will be new)
    
    # run findTopWindows, and remove from the list any which are stored
    unwantedHwnds=findNewTopWindows() # list of topWindow hwnds that exist
    if verbose:
        print '..%d original window(s)' % len(unwantedHwnds)
    # run the program
    appThread=AppThread(program,verbose)
    appThread.start()
    # give the thread a chance to get going:
    results=[]
    t=time()    
    while not results and ((time()-t)<THREAD_TIMEOUT_SECS):
        sleep(0.2) # means that the thread hasn't launched; give it a chance
        results=findNewTopWindows(unwantedHwnds,verbose)
                  
    if not results:
        # stop the program         
        terminateApp()    
        raise Exception, 'Failed to find any new windows!'
    
    if verbose:
        print '..%d additional (new) non-trivial window(s)' % len(results)
     
    if verbose:
        for hwnd in results:
            print '..%s: %s' % tupleHwnd(hwnd)[:2]
    
    return results,unwantedHwnds,appThread
      
if __name__=='__main__':
    pass
