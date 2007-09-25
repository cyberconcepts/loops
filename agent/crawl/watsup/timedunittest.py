# Author     : Tim Couper - tim@2wave.net
# Date       : 22 July 2004
# Version    : 1.0 
# Copyright  : Copyright TAC Software Ltd, under Python-style licence.
#              Provided as-is, with no warranty.

from unittest import TestCase
from time import time,sleep,ctime
import sys

if sys.platform=='win32':
    import win32gui
    def pump():
        # clear down any waiting messages (it all helps)  
        win32gui.PumpWaitingMessages()
else:
    pump=None

###-------------------------------------------------------------------------------
### hidden globals
##
##_PerformanceDataThisRun=None
##_PerformanceDataStore=None
##_doPerformanceChecks=True
##_recordPerformanceData=True
###-------------------------------------------------------------------------------
##
###-------------------------------------------------------------------------------
### externals
##
##def isRecording():
##    return _recordPerformanceData
##
##def isChecking():
##    return _doPerformanceChecks
##
##def doRecording(doIt=True):
##    global _recordPerformanceData
##    _recordPerformanceData=doIt
##    
##def doChecking(doIt=True):
##    global _doPerformanceChecks
##    _doPerformanceChecks=doIt
##
##def getPerformanceDataThisRun():
##    "returns the Performance data for this run of the tests"
##    global _PerformanceDataThisRun
##    if _PerformanceDataThisRun==None:
##        # create an instance, and load up what was already there          
##        _PerformanceDataThisRun=PerformanceDataThisRun()      
##    return _PerformanceDataThisRun
##
##def getPerformanceDataStore():
##    "returns the all Performance data for all runs of the tests"
##    global _PerformanceDataStore
##    if _PerformanceDataStore==None:
##        # create an instance, and load up what was already there          
##        _PerformanceDataStore=PerformanceDataStore()
##        try:
##            _PerformanceDataStore=cPickle.load(open(_PerformanceDataStore.filename))  
##        except IOError,EOFError:
##            pass          
##    return _PerformanceDataStore
##    
##PERFORMANCE_STORE_FILENAME='PerformanceDataStore.dat'
##
##class PerformanceDataCollectionError(Exception): pass
##class PerformanceDataCollection(dict):
##    def __str__(self):
##        lines=[]
##        keys=self.keys()
##        keys.sort()
##        for msg in keys:
##            lines.append(str(msg))
##            pdiList=self[msg]
##            pdiList.sort()
##            for pdi in pdiList:
##                lines.append('  %s' % pdi)
##        return '\n'.join(lines)
##
###class PerformanceDataThisRunError(Exception): pass
##class PerformanceDataThisRun(PerformanceDataCollection): pass
##        
##class PerformanceDataStoreError(Exception): pass
##class PerformanceDataStore(PerformanceDataCollection):
##    'performs persistent store of PerformanceDataItems'
##    def __init__(self, filename=PERFORMANCE_STORE_FILENAME):
##        self.filename=filename
##            
##    def addItem(self,msg,pdi):
##        'adds a pdi item to items, in the right place'
##        # msg must be immutable        
##        if isinstance(pdi,PerformanceDataItem):          
##            if not self.has_key(msg):
##                self[msg]=[]
##            self[msg].append(pdi)
##        else:
##            e='addItem can only accept PerformanceDataItem instances (%s: %s)' % (msg,str(pdi))
##            raise PerformanceDataStoreError,e   
##                
###-------------------------------------------------------------------------------
##   
##class PerformanceCheckError(AssertionError): pass
##
##class PerformanceCheck(object):
##    
##    def __init__(self):
##        self.reset()
##    
##    def reset(self):
##        self.startTime=time()
##            
##    def check(self,msg,maxDelay=None):
##        res=time()-self.startTime
##        
##        # if we're storing the data
##        if isRecording():
##            pdi=PerformanceDataItem(self.startTime,res,maxDelay)
##            pd=getPerformanceDataThisRun()
##            if not pd.has_key(msg):
##                pd[msg]=[] #list of PerformanceData instances, we hope
##            
##            # add it to the current data being processed    
##            pd[msg].append(pdi)
##            
##            # and add it to the store that we're going to persist  
##            pds=getPerformanceDataStore()
##            pds.addItem(msg,pdi)
##            cPickle.dump(pds,open(pds.filename,'w'))
##            
##        # if we're acting on performance tests:
##        if isChecking() and maxDelay<>None and (res>float(maxDelay)):            
##            res=round(res,2)
##            msg='%s [Delay > %s secs (%s secs)]' % (msg,maxDelay,res)        
##            raise PerformanceCheckError,msg   
##        
##class PerformanceDataItem(object): 
##    "holds a result (as elapsed time value in secs) and the time of invocation"           
##    def __init__(self,startTime,elapsedTime,maxDelay=None):
##        self.startTime=startTime # time of run
##        self.elapsedTime=round(elapsedTime,2) # elapsed time in secs
##        self.maxDelay=maxDelay # user defined delay for check
##        # if None, then there is no upper threshhold
##        
##    def __str__(self):
##        if self.maxDelay==None:
##            ok='OK'
##            md=''
##        else:
##            if  self.elapsedTime<=self.maxDelay:
##                ok='OK'
##            else:
##                ok='Fail'    
##            md= ' (%s)' % self.maxDelay
##            
##        return '%s: %s%s %s' % (ctime(self.startTime), self.elapsedTime, md, ok)    
##    
##    def __cmp__(self,other):
##        if self.startTime<other.startTime:
##            return -1
##        elif self.startTime>other.startTime:
##            return 1
##        else:
##            return 0
##        
        
maxWaitSecsDefault=3.0
retrySecsDefault=0.2

class TimedOutError(AssertionError): pass

class TimedTestCase(TestCase): 
    # extends the functionality of unittest.TestCase to 
    # allow multiple attempts at assertion, failif, for 
    # a specific length of time. If the test is not successful by the time
    # that Then it fails
   
    def __init__(self, methodName='runTest',maxWaitSecsDefault=1.0,retrySecsDefault=0.2):
        TestCase.__init__(self,methodName)
        self.maxWaitSecsDefault=float(maxWaitSecsDefault)
        self.retrySecsDefault=float(retrySecsDefault)
    
    def doTimeTest(self,func,*args):
        # remove the last 2 args, as they're out timing values:
        maxWaitSecs=args[-2]
        retrySecs=args[-1]
        args=args[:-2]
        
        if maxWaitSecs==None:
            maxWaitSecs=self.maxWaitSecsDefault
        else:
            try:
                maxWaitSecs=float(maxWaitSecs)  
            except TypeError,e:
                e='%s (maxWaitSecs "%s")' % (e,maxWaitSecs)
                raise TypeError,e 
               
        if retrySecs==None:
            retrySecs=self.retrySecsDefault
        else:
            try:
                retrySecs=float(retrySecs)
            except TypeError,e:
                e='%s (retrySecs "%s")' % (e,retrySecs)
                raise TypeError,e 
        retrySecs=max(0,retrySecs-.001) # allow for the pump,etc below
          
        t=time()
        while (time()-t)<maxWaitSecs : 
            try:                
                func(self,*args) 
                break
            except self.failureException:
                if pump:
                    pump()
                
                sleep(retrySecs)
                
        else:
            # timed out, and still not worked!

            try:                
                func(self,*args) 
            except self.failureException,e:
                raise TimedOutError,e    
     
    def fail(self,msg=None,maxWaitSecs=None,retrySecs=None):
        self.doTimeTest(TestCase.fail,maxWaitSecs,retrySecs)
                        
    def failIf(self, expr, msg=None,maxWaitSecs=None,retrySecs=None):
        "Fail the test if the expression is true."
        self.doTimeTest(TestCase.failIf,expr,msg,maxWaitSecs,retrySecs)

    def failUnless(self, expr, msg=None,maxWaitSecs=None,retrySecs=None):
        """Fail the test unless the expression is true."""
        self.doTimeTest(TestCase.failUnless,expr,msg,maxWaitSecs,retrySecs)

    def failUnlessEqual(self, first, second, msg=None,maxWaitSecs=None,retrySecs=None):
        """Fail if the two objects are unequal as determined by the '=='
           operator.
        """
        self.doTimeTest(TestCase.failUnlessEqual,first,second,msg,maxWaitSecs,retrySecs)

    def failIfEqual(self, first, second, msg=None):
        """Fail if the two objects are equal as determined by the '=='
           operator.
        """
        self.doTimeTest(TestCase.failIfEqual,first,second,msg,maxWaitSecs,retrySecs)

    def failUnlessAlmostEqual(self, first, second, places=7, msg=None):
        """Fail if the two objects are unequal as determined by their
           difference rounded to the given number of decimal places
           (default 7) and comparing to zero.

           Note that decimal places (from zero) is usually not the same
           as significant digits (measured from the most signficant digit).
        """
        self.doTimeTest(TestCase.failUnlessAlmostEqual,first,second,places,msg,maxWaitSecs,retrySecs)

    def failIfAlmostEqual(self, first, second, places=7, msg=None):
        """Fail if the two objects are equal as determined by their
           difference rounded to the given number of decimal places
           (default 7) and comparing to zero.

           Note that decimal places (from zero) is usually not the same
           as significant digits (measured from the most signficant digit).
        """
        self.doTimeTest(TestCase.failIfAlmostEqual,first,second,places,msg,maxWaitSecs,retrySecs)

    assertEqual = assertEquals = failUnlessEqual

    assertNotEqual = assertNotEquals = failIfEqual

    assertAlmostEqual = assertAlmostEquals = failUnlessAlmostEqual

    assertNotAlmostEqual = assertNotAlmostEquals = failIfAlmostEqual

    assert_ = failUnless

