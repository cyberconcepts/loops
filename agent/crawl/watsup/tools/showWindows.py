# logic for wxShowWindows

# Author     : Tim Couper - timc@tizmoi.net
# Date       : 1 August 2004
# Copyright  : Copyright TAC Software Ltd, under Python-like licence.
#              Provided as-is, with no warranty.
# Notes      : Requires watsup

import cPickle
from watsup.AppControls import findNewTopWindows
from watsup.winGuiAuto import dumpWindow
from watsup.utils import dumpHwnd
import os.path
from types import ListType

PICKLE_FILE='findall.pkl'

def readPickle(pickle_file=PICKLE_FILE):
    #reads the list in the pickle file if possible
    if os.path.exists(pickle_file):
        return cPickle.load(open(pickle_file))
    else:
        return []
    
def findAll(pickle_file=PICKLE_FILE):
    # get all the top windows:
    res=findNewTopWindows()    
    cPickle.dump(res,open(pickle_file,'w'))
    return res 

def findNew(pickle_file=PICKLE_FILE):
    # get all the top windows, and return any new ones    
    olds=readPickle(pickle_file)       
    return findNewTopWindows(olds)
