import unittest
import os.path, imp, os
from types import ListType, TupleType

def buildSuite(paths,recurse_directories=False):
    # returns a suite of TestCase classes from the list of paths,
    # These may be files and directories. If directories,
    # there's the opportunity to recurse down all
    
    def visit(args,dirname,allnames):
        
        for aname in allnames:
            fullname=os.path.join(dirname,aname)
            if os.path.isdir(fullname):                
                res=buildSuitesFromDirectory(fullname)
                if res:
                    suites.extend(res)   
        
    #ensure paths is a list:
    if type(paths) not in (ListType, TupleType):
        paths=[paths]
    
    suites=[]        
    for path in paths:
        if os.path.isfile(path):
            res=buildSuiteFromFile(path)
            if res:
                suites.append(res)
        elif os.path.isdir(path): 
            #print 'Directory: %s' % path  
            # find all the TestCases in this directory:
            res=buildSuitesFromDirectory(path)
            if res:
               suites.extend(res)
                    
            if recurse_directories:
                os.path.walk(path,visit,suites)
    
    t=unittest.TestSuite()  
    for suite in suites:        
        for test in suite._tests:
            t.addTest(test)
                    
    if len(t._tests):
        return t          
    else:
        return None
    
                    
def buildSuiteFromFile(filename):   
    modname, modtype = os.path.splitext(os.path.basename(filename))  
    
    if modtype.lower() == '.py':      
        moduleToTest = imp.load_source(modname, filename, file(filename))
    #elif modtype.lower() in {'.pyc':0, '.pyo':0}:
    #    moduleToTest = imp.load_compiled(modname, filename, file(filename, 'rb'))
    else:
        return None
        
    suite= unittest.defaultTestLoader.loadTestsFromModule(moduleToTest)
    for test in suite._tests: # tests is a TestSuite class
        # remove any which are null:
        if len(test._tests)==0:
            suite._tests.remove(test)
     
    if len(suite._tests): #not interested if no tests!
        return suite
    else:
        return None
       
def buildSuitesFromDirectory(dirname):
    filenames=os.listdir(dirname)
    suites=[]
    for filename in filenames:
        fullname=os.path.join(dirname,filename)
        res=buildSuiteFromFile(fullname)
        if res:            
            suites.append(res)
            
    return suites

if __name__=='__main__':
    
     dir='c:/MyProducts/watsup/examples/unittests'
     fs=[]
     for fname in ('ExampleTestsAgain.py','ExampleTests.py'):
         fs.append(os.path.join(dir,fname))
     myfile=os.path.abspath( __file__)    
     #print buildSuite(myfile)
     mydir=os.path.split(myfile)[0]
     suite= buildSuite(dir,True)
     print '------------'
     print suite._tests
         
    
    