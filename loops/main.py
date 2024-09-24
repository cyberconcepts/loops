# loops.main

""" Entry point for the loops application.
"""

import os, sys


softwareHome = None
instanceHome = configFile = None


def setWindowsEnvironment():
    global softwareHome, instanceHome, configFile
    basedir = os.path.dirname(os.path.realpath(__file__))
    if basedir.endswith('library.zip'):
        basedir = os.path.dirname(basedir)
    libdir = os.path.join(basedir, 'Lib')
    softwareHome = os.path.join(libdir, 'site-packages')
    instanceHome = os.path.join(basedir, 'instance')
    configFile = os.path.join(instanceHome, 'etc', 'zope.conf')
    sys.path.insert(0, libdir)
    sys.path.insert(0, softwareHome)
    sys.path.insert(0, os.path.join(basedir, 'DLLs'))
    sys.path.insert(0, os.path.join(instanceHome, 'lib', 'python'))


def setZopeEnvironment():
    global softwareHome, instanceHome, configFile
    curdir = os.path.dirname(os.path.realpath(__file__))
    #for i in range(5):
    for i in range(3):
        curdir = os.path.dirname(curdir)
    instanceHome = curdir
    if softwareHome is None:
        softwareHome = os.path.join(os.path.dirname(instanceHome), 'lib', 'python')
    configFile = os.path.join(instanceHome, 'etc', 'zope.conf')
    sys.path[:] = sys.path[1:]  # remove script directory
    sys.path.insert(0, softwareHome)
    sys.path.insert(0, os.path.join(instanceHome, 'lib', 'python'))
    os.environ['USE_RLIBRARY'] = ''     # do not use the R statistics library


def setInstanceHomeInZopeConf():
    zc = open(configFile)
    l1 = zc.readline()
    rest = zc.read()
    zc.close()
    command, key, value = [w.strip() for w in l1.split()]
    if command == '%define' and key == 'INSTANCE' and value != instanceHome:
        print('INSTANCE variable changed from %s to %s.' % (value, instanceHome))
        l1 = ' '.join((command, key, instanceHome)) + '\n'
        zc = open(configFile, 'w')
        zc.write(l1)
        zc.write(rest)
        zc.close()


def startZope(configFile):
    # set up the agent application
    from cybertools.agent.main import setup
    #setup()
    # start Zope using the twisted server
    from zope.app.twisted.main import main
    try:
        main(["-C", configFile])
    except IOError, e:
        if str(e) == '[Errno 11] Resource temporarily unavailable':
            print('WARNING: Background process already running.')
            #from startup import openBrowser
            #openBrowser(None)


def main():
    """ Called from loops.exe (=deploy/start.py). """
    setWindowsEnvironment()
    setInstanceHomeInZopeConf()
    startZope(configFile)


def mainZope():
    """ Start in a regular Zope instance. """
    setZopeEnvironment()
    startZope(configFile)


if __name__ == '__main__':
    mainZope()
