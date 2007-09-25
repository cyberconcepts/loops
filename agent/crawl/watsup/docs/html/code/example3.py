from watsup.launcher import launchApp,terminateApp 
from watsup.winGuiAuto import findTopWindows                          
import example2

# find an instance of SimpleForm. If one isn't there, launch it
forms=findTopWindows(wantedText='Simple Form')
if forms:
    form=forms[0]
else:
    form=launchApp('simple.exe',wantedText='Simple Form')    

example2.main()

# and terminate the form
terminateApp(form)    


