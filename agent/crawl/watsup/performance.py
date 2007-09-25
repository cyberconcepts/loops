# Author     : Tim Couper - timc@tizmoi.net
# Date       : 22 July 2004
# Version    : 1.0 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.

from time import time,ctime
import sys
import cPickle

#-------------------------------------------------------------------------------
# hidden globals

_PerformanceDataThisRun=None
_PerformanceDataStore=None

_doPerformanceChecks=True
_recordPerformanceData=False

#-------------------------------------------------------------------------------
# externals

def isRecording():
    return _recordPerformanceData

def isChecking():
    return _doPerformanceChecks

def doRecording(doIt=True):
    global _recordPerformanceData
    _recordPerformanceData=doIt
    
def doChecking(doIt=True):
    global _doPerformanceChecks
    _doPerformanceChecks=doIt

def onOff(bool):
    if bool:
        return 'On'
    else:
        return 'Off'
    
def getPerformanceDataThisRun():
    "returns the Performance data for this run of the tests"
    global _PerformanceDataThisRun
    if _PerformanceDataThisRun==None:
        # create an instance, and load up what was already there          
        _PerformanceDataThisRun=PerformanceDataThisRun()      
    return _PerformanceDataThisRun

def getPerformanceDataStore():
    "returns the all Performance data for all runs of the tests"
    global _PerformanceDataStore
    if _PerformanceDataStore==None:
        # create an instance, and load up what was already there          
        _PerformanceDataStore=PerformanceDataStore()
        try:
            _PerformanceDataStore=cPickle.load(open(_PerformanceDataStore.filename))  
        except IOError,EOFError:
            pass          
    return _PerformanceDataStore
    
PERFORMANCE_STORE_FILENAME='PerformanceDataStore.dat'

class PerformanceDataCollectionError(Exception): pass
class PerformanceDataCollection(dict):
    def __str__(self):
        lines=[]
        keys=self.keys()
        keys.sort()
        for msg in keys:
            lines.append(str(msg))
            pdiList=self[msg]
            pdiList.sort()
            for pdi in pdiList:
                lines.append('  %s' % pdi)
        return '\n'.join(lines)

#class PerformanceDataThisRunError(Exception): pass
class PerformanceDataThisRun(PerformanceDataCollection): pass
        
class PerformanceDataStoreError(Exception): pass
class PerformanceDataStore(PerformanceDataCollection):
    'performs persistent store of PerformanceDataItems'
    def __init__(self, filename=PERFORMANCE_STORE_FILENAME):
        self.filename=filename
            
    def addItem(self,msg,pdi):
        'adds a pdi item to items, in the right place'
        # msg must be immutable        
        if isinstance(pdi,PerformanceDataItem):          
            if not self.has_key(msg):
                self[msg]=[]
            self[msg].append(pdi)
        else:
            e='addItem can only accept PerformanceDataItem instances (%s: %s)' % (msg,str(pdi))
            raise PerformanceDataStoreError,e   
                
#-------------------------------------------------------------------------------
   
class PerformanceCheckError(AssertionError): pass

class PerformanceCheck(object):
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.startTime=time()
            
    def check(self,msg,maxDelay=None):
        res=time()-self.startTime
        
        # if we're storing the data
        if isRecording():
            pdi=PerformanceDataItem(self.startTime,res,maxDelay)
            pd=getPerformanceDataThisRun()
            if not pd.has_key(msg):
                pd[msg]=[] #list of PerformanceData instances, we hope
            
            # add it to the current data being processed    
            pd[msg].append(pdi)
            
            # and add it to the store that we're going to persist  
            pds=getPerformanceDataStore()
            pds.addItem(msg,pdi)
            cPickle.dump(pds,open(pds.filename,'w'))
            
        # if we're acting on performance tests:
        if isChecking() and maxDelay<>None and (res>float(maxDelay)):            
            res=round(res,2)
            msg='%s [Delay > %s secs (%s secs)]' % (msg,maxDelay,res)        
            raise PerformanceCheckError,msg   
        
class PerformanceDataItem(object): 
    "holds a result (as elapsed time value in secs) and the time of invocation"           
    def __init__(self,startTime,elapsedTime,maxDelay=None):
        self.startTime=startTime # time of run
        self.elapsedTime=round(elapsedTime,2) # elapsed time in secs
        self.maxDelay=maxDelay # user defined delay for check
        # if None, then there is no upper threshhold
        
    def __str__(self):
        if self.maxDelay==None:
            ok='OK'
            md=''
        else:
            if  self.elapsedTime<=self.maxDelay:
                ok='OK'
            else:
                ok='Fail'    
            md= ' (%s)' % self.maxDelay
            
        return '%s: %s%s %s' % (ctime(self.startTime), self.elapsedTime, md, ok)    
    
    def __cmp__(self,other):
        if self.startTime<other.startTime:
            return -1
        elif self.startTime>other.startTime:
            return 1
        else:
            return 0
        

def nicePrint(filename=sys.stdout):
    def wout(f,text):
        f.write('%s\n' % text)
                
    if filename==sys.stdout:
        f=sys.stdout
    else:
        f=open(filename,'w')
              
##    from watsup.timedunittest import getPerformanceDataStore,getPerformanceDataThisRun, \
##                                 isRecording 
    if isRecording():
        for func in (getPerformanceDataThisRun,getPerformanceDataStore):
            fn=func.__name__
            wout(f,'\n%s\n%s\n' % (fn,'-'*len(fn)))
            wout(f,str(func()))   
                     
