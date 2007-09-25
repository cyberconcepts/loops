from watsup.winGuiAuto import findControl,findControls,findTopWindow, \
                              WinGuiAutoError,getEditText,clickButton, \
                              activateMenuItem,getMenuInfo, \
                              getListboxItems,getComboboxItems, \
                              selectListboxItem,selectComboboxItem,\
                              setEditText,getTopMenu, setCheckBox,\
                              getCheckBox
                              
from watsup.launcher import launchApp,terminateApp
import win32gui
import win32con
#from watsup.Knowledge import getKnowledge
from types import ListType,TupleType
 
verbose=False

CONTROL_MAX_WAIT_SECS=3

def PLaunchApp(program,wantedText=None,wantedClass=None):
    hwnd=launchApp(program,wantedText,wantedClass,verbose) 
    return PWindow(hwnd=hwnd) 
  
class PWinControl(object): 
    """Abstract base class for PWindows and PControls"""    
    def __init__(self,parent):
        self.parent=parent
        
    def findPControl(self,hwnd=None,wantedText=None,wantedClass=None,selectionFunction=None):
        """Factory method returning a PControl instance, or a subclass thereof, 
        within a PWinControl instance,
        
        find a unique control - raises exception if non-unique
        """ 
        
        # if wantedClass is not given, let's try and find out what it is;
        # then we should be better able to assign the right PControl subclass
        # to it
        if wantedClass==None:
            #find the wantedClass anyway
            p=PControl(self.parent,hwnd,wantedText,wantedClass,selectionFunction)
            wantedClass=p.className
        else:
            p=None 
        
        # if this is a known class, return the instance of the specific
        # subclass of PControl               
        if KNOWN_CLASSES.has_key(wantedClass):
            if verbose:
                print KNOWN_CLASSES[wantedClass],(self.parent,hwnd,wantedText,wantedClass,selectionFunction)    
    
            return KNOWN_CLASSES[wantedClass](self.parent,hwnd,wantedText,wantedClass,selectionFunction)    

        # in all other cases, return a PControl (we may have already calculated it above)
        if p:
            return p 
        else:
            return PControl(self.parent,hwnd,wantedText,wantedClass,selectionFunction)
 
            
    def findPControls(self,wantedText=None,wantedClass=None,selectionFunction=None):
        # returns a list of PControl instances which match the criteria                
        hwnds=findControls(wantedText,wantedClass,selectionFunction)
        controlList=[]
        for hwnd in hwnds:
            controlList.append(self.findPControl(self,hwnd=hwnd))
        return controlList                     

##class Menu(object):
##    # container for menu items
##    def __init__(self,mwnd):
##        self.mwnd=mwnd
# not sure we need this entity, as we can address MenuItems directly
        
class MenuItem(object):
    def __init__(self,parentWindow,*menuItems):
        self.parentWindow=parentWindow
        #acceept either a tuple/list or *args-type values
        if type(menuItems[0]) in (ListType,TupleType):
            self.menuItemTuple=menuItems[0]
        else:
            self.menuItemTuple=menuItems
        
    def activate(self):
        activateMenuItem(self.parentWindow.hwnd,self.menuItemTuple)        
        
    #-------------------------------------------------------------------------------
    # accessors and properties
    
    def getInfo(self):
        return getMenuInfo(self.parentWindow.hwnd,self.menuItemTuple)
    
    def getName(self):
        return menuInfo.name
    
    def getItemCount(self):
        return menuInfo.itemCount
    
    def getIsChecked(self):
        return menuInfo.IsChecked
    
    def getIsSeparator(self):
        return menuInfo.IsSeparator
    
    def getIsDisabled(self):
        return menuInfo.IsDisabled
    
    def getIsGreyed(self):        
        return menuInfo.IsGreyed  
        
    name=property(getName)
    itemCount=property(getItemCount)
    isChecked=property(getIsChecked)
    isDisabled = property(getIsDisabled)
    isGreyed = property(getIsGreyed)
    isSeparator = property(getIsSeparator)
    
    menuInfo=property(getInfo)
    
    #-------------------------------------------------------------------------------
       
      
class PWindowError(Exception): pass    
class PWindow(PWinControl):  
    
    def __init__(self,hwnd=None,wantedText=None,wantedClass=None,selectionFunction=None,controlParameters=None):
        PWinControl.__init__(self,self)
        
        if hwnd:
            self.hwnd=hwnd
        else:    
            try:
                self.hwnd=findTopWindow(wantedText=wantedText,
                                        wantedClass=wantedClass,
                                        selectionFunction=selectionFunction)
            except WinGuiAutoError,e:
                raise PWindowError,e
        
        # controlParameters is the list of dictionaries with unique
        # definitions of the controls within this Window
        # eg controlParameters=[{'wantedClass':'TButton','wantedText':'Button1'},
        #                       {'wantedClass':'TRadioButton','selectionFunction':chooseIt}]
        self.controls=[]
        if controlParameters<>None:
            for cp in controlParameters:
                hwnd=cp.get('hwnd',None)
                wantedClass=cp.get('wantedClass',None)
                wantedText=cp.get('wantedTest',None)
                selectionFunction=cp.get('selectionFunction',None)
                clist=self.findControls(hwnd=hwnd,                                   
                                   wantedText=wantedText,
                                   wantedClass=wantedClass,
                                   selectionFunction=selectionFunction)
                                          
                self.controls.extend(clist)
         
        self._mainMenuHandle=None
                
    def activateMenuItem(self,menuItem):
        menuItem.activateMenuItem()
        
    def terminate(self):
        terminateApp(self.hwnd)    
    
#-------------------------------------------------------------------------------
#Accessors & properties
    
### top menu item
##   def getMainMenu(self):
##       if self._mainMenuHandle:
##           return self._mainMenuHandle
##       else:
##           return getTopMenu(self.hwnd)  
##      
##    mainMenu=property(getMainMenu)    
#-------------------------------------------------------------------------------
    
class PControlError(Exception): pass          
class PControl(PWinControl):    
    def __init__(self,parent,hwnd=None,wantedText=None,wantedClass=None,selectionFunction=None):
        "Constructor takes either hwnd directly, or others in a controlParameter set"
        PWinControl.__init__(self,parent)
        if hwnd:
            self.hwnd=hwnd
        else:               
            try:
                self.hwnd=findControl(parent.hwnd,
                                   wantedText=wantedText,
                                   wantedClass=wantedClass,
                                   selectionFunction=selectionFunction,
                                   maxWait=CONTROL_MAX_WAIT_SECS)
            except WinGuiAutoError,e:
                raise PControlError,e
            
            
##    def addKnowledge(self,attrName):
##        knowledge=getKnowledge()
##        knowledge.add(self.className,attrName)
                
    #-------------------------------------------------------------------------------
    # general winctrl actions which, if acted upon by a user, might tell us sth about 
    # this unknown control 
    
    def getItems(self):
        # This PControl of unknown class can get items
        # at least the user thinks so 
        #self.addKnowledge('getItems')
        res=getComboboxItems(self.hwnd)
        if not res:
            res=getListboxItems(self.hwnd)
            
        return res
    
    def selectItem(self,item):
        # This PControl of unknown class can select items
        # at least the user thinks so 
        #self.addKnowledge('selectItem')
        res= selectListboxItem(self.hwnd, item) 
        if not res:
            res=selectComboBoxItem(self.hwnd,item)
        return res       
       
    def click(self):
        # This PControl of unknown class is clickable
        # at least the user thinks so 
        #self.addKnowledge('click')
        clickButton(self.hwnd)
    
    def getCaption(self):
        # This PControl of unknown class has a caption,
        # at least the user thinks so  
        #self.addKnowledge('caption')
        return self.getEditText()
          
    def setCheckBox(self, state=3DTrue):
	setCheckBox(self.hwnd, state)
	
    def getCheckBox(self):
	return getCheckBox(self.hwnd)
                                
    #-------------------------------------------------------------------------------
    #Accessors and properties
     
    def getText(self):
        # returns a list of strings which make up the text
        return getEditText(self.hwnd)
    
    def setText(self,text,append=False):
        setEditText(text,append)
        
    def getClassName(self):
        return win32gui.GetClassName(self.hwnd)    
      
    text=property(getText)
    className=property(getClassName)
    caption=property(getCaption)
    items=property(getItems)    
    
    #-------------------------------------------------------------------------------
         
class PEdit(PControl): 
    def __init__(self,parent,hwnd=None,wantedText=None,wantedClass=None,selectionFunction=None):
        PControl.__init__(self,parent,hwnd,wantedText,wantedClass,selectionFunction)

    #-------------------------------------------------------------------------------
    #Accessors and properties        

    def getText(self):
        # returns a simple string - PEdit controls only have one value
        p=PControl.getText(self)
        if p:
            return p[0]
        else:
            return ''
        
    text=property(getText) 
    caption=None #undefine the caption property
    
    #-------------------------------------------------------------------------------

class PText(PControl):
    # multi-line text control
    caption=None
    
class PComboBox(PControl):
    
    def selectItem(self,item):
        selectComboboxItem(self.hwnd,item)
    
    #-------------------------------------------------------------------------------
    #Accessors and properties 
    
    def getItems(self):
        return getComboboxItems(self.hwnd)       
        
    items=property(getItems)
   
    
    #-------------------------------------------------------------------------------
            

class PDelphiComboBox(PComboBox): 
    # The Delphi Combo box has a control of class Edit within
    # it, which contains the text
    def __init__(self,parent,hwnd=None,wantedText=None,wantedClass=None,selectionFunction=None):
        PControl.__init__(self,parent,hwnd,wantedText,wantedClass,selectionFunction)
        self.editCtrl=self.findPControl(wantedClass='Edit')
    #-------------------------------------------------------------------------------
    #Accessors and properties        

    def getText(self):
        # get the content from the control Edit:
            
        return self.editCtrl.getText()
    
    text=property(getText)  
   
    
    #-------------------------------------------------------------------------------

class PButton(PControl): 
    
    def click(self):        
        clickButton(self.hwnd)
        
    #-------------------------------------------------------------------------------
    #Accessors and properties        
        
    caption=property(PControl.getText)    
    
    #-------------------------------------------------------------------------------
 
class PListBox(PControl):
    
    def selectItem(self,item):
        return selectListboxItem(self.hwnd, item)
    
    #-------------------------------------------------------------------------------
    #Accessors and properties 
    
    def getItems(self):
        return getListboxItems(self.hwnd)       
        
    items=property(getItems)
   
    
    #-------------------------------------------------------------------------------
        
class PCheckBox(PControl):
    
   
    #-------------------------------------------------------------------------------
    #Accessors and properties 
    
  
    caption=property(PControl.getText)
    
    def getCheckStatus(self):
    	return self.getCheckBox()
    	
    def isChecked(self):
    	return self.getCheckStatus()#=3D=3D win32con.BST_INDETERMINATE
    
    def isIndeterminate(self):
	return self.getCheckStatus() #=3D=3D win32con.BST_INDETERMINATE
	=20

    def isNotChecked(self):
	return self.getCheckStatus() #=3D=3D win32con.BST_UNCHECKED
	=20
   
    def setChecked(self):
	setCheckBox(hwnd, state = True)

    def setUnChecked(self):
	setCheckBox(hwnd, state = False)

    
    #-------------------------------------------------------------------------------        
KNOWN_CLASSES={'TEdit': PEdit,
               'TComboBox': PDelphiComboBox,
               'ComboBox': PComboBox,
               'TButton': PButton,
               'TListBox': PListBox,
               'ListBox': PListBox,
               'CheckBox': PCheckBox,
               'TCheckBox': PCheckBox,
               
               }       
    