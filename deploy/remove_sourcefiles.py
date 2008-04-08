#! /usr/bin/env python

"""
Remove .py and (if .pyo files present) .pyc from the directory given.

$Id$
"""

import os, sys


def removeSourceFiles(path):
    for root, dirs, files in os.walk(path):
        for d in dirs:
            if d == '.svn':
                removeDirectory(os.path.join(root, d))
        for f in list(files):
            if f == 'README.txt':
                os.unlink(os.path.join(root, f))
                continue
            name, ext = os.path.splitext(f)
            pyc = name + '.pyc'
            pycPath = os.path.join(root, pyc)
            pyo = name + '.pyo'
            pyoPath = os.path.join(root, pyo)
            py = name + '.py'
            pyPath = os.path.join(root, py)
            if ext == '.pyc':
                if pyo in files:
                    print pyoPath,
                    files.remove(pyo)
                    os.unlink(pyoPath)
                if py in files:
                    print pyPath,
                    files.remove(py)
                    os.unlink(pyPath)
            elif ext == '.pyo':
                if py in files:
                    print pyPath,
                    files.remove(py)
                    os.unlink(pyPath)

def removeDirectory(path):
    for root, dirs, files in os.walk(path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            removeDirectory(os.path.join(root, d))
        os.rmdir(path)


if __name__ == '__main__':
    removeSourceFiles(sys.argv[1])

