from watsup.winGuiAuto import findTopWindow,findControl,setEditText
from time import sleep  
# Locate notepad's edit area, and enter various bits of text.

notepadWindow = findTopWindow(wantedClass='Notepad')
editArea = findControl(notepadWindow,wantedClass="Edit") 
setEditText(editArea, "Hello, again!")  
sleep(0.8) 
setEditText(editArea, " You still there?",True)      

