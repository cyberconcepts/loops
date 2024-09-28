# loops.tests

import os.path
import sys

def fixPythonPath(doPrint=False):
    sys.path = [os.path.dirname(__file__)] + sys.path[1:]
    if doPrint:
        print('sys.path =', sys.path)
