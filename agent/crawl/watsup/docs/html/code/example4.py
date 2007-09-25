from watsup.launcher import launchApp,terminateApp 
from watsup.winGuiAuto import findTopWindows, findControl,getEditText,clickButton  
from watsup.performance import PerformanceCheck,PerformanceCheckError  
from time import sleep,time                      

def main(myExecutable,myWantedText):
    # find an instance of SimpleForm. If one isn't there, launch it
    forms=findTopWindows(wantedText=myWantedText)
    if forms:
        form=forms[0]
    else:
        form=launchApp(myExecutable,wantedText=myWantedText)       
    
    button=findControl(form,wantedText='Click me')
    editbox=findControl(form,wantedClass='TEdit')

    #start a performance check instance
    p=PerformanceCheck()
    
    clickButton(button)    
    
    # belts and braces to avoid infinite waiting!
    maxWaitTime=2.0
    startTime=time()
    
    while time()-startTime<maxWaitTime:
        t=getEditText(editbox)
        if t:
            break
        else:
            sleep(0.1)
    else:
        raise Exception,'Failed to get value after maxWaitTime of %s secs' % maxWaitTime        
    
    try:
        try:
        #do the check/recording step, identifying this step with the wantedtext
            p.check(myWantedText,1.0)    
        except PerformanceCheckError,e:
            print '** Failed: %s' % e
            
    # and terminate the form
    finally:
        terminateApp(form)
        
    from watsup.performance import nicePrint
    nicePrint()        

if __name__=='__main__':
    print ' please run example4a or 4b'

