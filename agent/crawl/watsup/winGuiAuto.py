# Module     : winGuiAuto.py
# Synopsis   : Windows GUI automation utilities
# Programmer : Simon Brunning - simon@brunningonline.net
# Date       : 25 June 2003
# Version    : 1.0 
# Copyright  : Released to the public domain. Provided as-is, with no warranty.
# Notes      : Requires Python 2.3, win32all and ctypes 

# Modifications by Tim Couper - tim@tizmoi.net
# 22 Jul 2004
# findControls: deduplicates the list to be returned 
# findControl: handles win32gui.error from initial call to findControls
# getMenuInfo: improved algorithm for calculating no. of items in a menu
# activateMenuItem: improved algorithm for calculating no. of items in a menu
#           
# GLOBALLY corrected spelling: seperator -> separator
#                            : descendent -> descendant
# added findMenuItem

'''Windows GUI automation utilities.

TODO - Until I get around to writing some docs and examples, the tests at the
foot of this module should serve to get you started.

The standard pattern of usage of winGuiAuto is in three stages; identify a
window, identify a control in the window, trigger an action on the control.

The end result is always that you wish to have an effect upon some Windows GUI
control.

The first stage is to identify the window within which the control can be
found. To do this, you can use either findTopWindow or findTopWindows. The
findTopWindow function returns a reference to single window, or throws an
exception if multiple windows or no windows matching the supplied selection
criteria are found. If no matching window is found, immediately, the
findTopWindow function may keep trying to find a match, depending upon suppled
retry aguments. The findTopWindows function returns a list of references to all
windows matching the supplied selection criteria; this list may be empty. The
findTopWindows function will return immediately.

Usually, specifying caption text, the window's class, or both, will be
sufficient to identify the required window. (Note that the window's class is a
Windows API concept; it has nothing to do with Python classes. See http://msdn.microsoft.com/library/en-us/winui/WinUI/WindowsUserInterface/Windowing/Window_89WindowClasse.asp
for an overview.) Caption text will match if the specified text is *contained*
in the windows' captions; this match is case unsensitive. Window class names
must match identically; the full class name must be matched, and the test is
case sensitive.

This matching behavior is usually the most useful - but not always. If other
selection behavior is required, a selection function can be passed to the find
functions.

These returned references are in the form of 'Windows Handles'. All windows and
controls are accessed via a Windows Handle (or hwnd). See
http://msdn.microsoft.com/library/en-us/winui/winui/windowsuserinterface/windowing/windows/aboutwindows.asp
for Microsoft's info-deluge on all things Windows window.

Having identified the window, the next stage is to identify the control. To do
this, you can use either of the findControl and findControls functions. These
work in almost exactly the same way as the findTopWindow and findTopWindows
functions; they take the hwnd of the top level window within which the required
control should be found, and otherwise take the same arguments as the
findTopWindow and findTopWindows functions, and work in the same ways.

Having now identified your control, you can now query its state, and send
actions (in the form of Windows messages) to it. It's at this point that you
are most likely to end up having to extend winGuiAuto in some way; the
developer of the GUI that you are trying to drive is free to develop controls
which respond to different messages in different ways. Still, if standard MFC
controls have been used, you may find that winGuiAuto's functions may provide
much or all of what you need - or at least provide a useful template. These
functions (clickButton, clickStatic, doubleClickStatic, getComboboxItems,
getEditText, getListboxItems, selectComboboxItem, selectListboxItem and
setEditText) should be fairly self evident.

Selection of menu items is a slightly different process: but don't fret; it's
pretty simple. You'll need to identify the hwnd of the top level window that
you want to control using either of the findTopWindow and findTopWindows
functions. You can then call the activateMenuItem function, passing in the top
level window's hwnd and the path to the menu option that you wish to activate.
This path should consist of a list specifiying the path to the required menu
option - see activateMenuItem's docstring for details.

TODO getMenuInfo 

TODO: dumpTopWindows, dumpWindow, Spy++ and Winspector (http://www.windows-spy.com)
Two if the main difficulties you'll come across while using winGuiAuto will be discovering
 the classes of the windows that you want, and where the  provided 
'''

import array
import ctypes
import os
import struct
import sys
import time
import win32api
import win32con
import win32gui

def findTopWindow(wantedText=None,
                  wantedClass=None,
                  selectionFunction=None,
                  maxWait=1,
                  retryInterval=0.1):
    '''Find the hwnd of a top level window.
    
    You can identify windows using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)
    
    If no window matching the specified selection criteria is found
    immediately, further attempts will be made. The retry interval and maximum
    time to wait for a matching window can be specified.

    Arguments:
    
    wantedText          Text which the required window's caption must
                        *contain*. (Case insensitive match.)
    wantedClass         Class to which the required window must belong.
    selectionFunction   Window selection function. Reference to a function
                        should be passed here. The function should take hwnd
                        as an argument, and should return True when passed the
                        hwnd of a desired window.
    maxWait             The maximum time to wait for a matching window, in
                        seconds.
    retryInterval       How frequently to look for a matching window, in
                        seconds
                    
    Raises:
    WinGuiAutoError     When no window or multiple windows found.

    Usage examples:     # Caption contains "Options"
                        optDialog = findTopWindow(wantedText="Options")
                        # Caption *equals* "Notepad"
                        saveDialog = findTopWindow(selectionFunction=lambda hwnd:
                                                                     win32gui.GetWindowText(hwnd)=='Notepad')
    '''
    topWindows = findTopWindows(wantedText, wantedClass, selectionFunction)
    if len(topWindows) > 1:
        raise WinGuiAutoError("Multiple top level windows found for wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction) +
                              ", maxWait=" +
                              repr(maxWait) +
                              ", retryInterval=" +
                              str(retryInterval))
    elif topWindows:
        return topWindows[0]
    elif (maxWait-retryInterval) >= 0:
        time.sleep(retryInterval)
        try:
            return findTopWindow(wantedText=wantedText,
                                  wantedClass=wantedClass,
                                  selectionFunction=selectionFunction,
                                  maxWait=maxWait-retryInterval,
                                  retryInterval=retryInterval)
        except WinGuiAutoError:
            raise WinGuiAutoError("No top level window found for wantedText=" +
                                  repr(wantedText) +
                                  ", wantedClass=" +
                                  repr(wantedClass) +
                                  ", selectionFunction=" +
                                  repr(selectionFunction) +
                                  ", maxWait=" +
                                  repr(maxWait) +
                                  ", retryInterval=" +
                                  str(retryInterval))
    else:
        raise WinGuiAutoError("No top level window found for wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction) +
                              ", maxWait=" +
                              repr(maxWait) +
                              ", retryInterval=" +
                              str(retryInterval))

def findTopWindows(wantedText=None, wantedClass=None, selectionFunction=None):
    '''Find the hwnd of top level windows.
    
    You can identify windows using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Arguments:
    wantedText          Text which required windows' captions must contain.
    wantedClass         Class to which required windows must belong.
    selectionFunction   Window selection function. Reference to a function
                        should be passed here. The function should take hwnd as
                        an argument, and should return True when passed the
                        hwnd of a desired window.

    Returns:            A list containing the window handles of all top level
                        windows matching the supplied selection criteria.

    Usage example:      optDialogs = findTopWindows(wantedText="Options")
    '''
    results = []
    topWindows = []
    win32gui.EnumWindows(_windowEnumerationHandler, topWindows)
    for hwnd, windowText, windowClass in topWindows:
        if wantedText and \
           not _normaliseText(wantedText) in _normaliseText(windowText):
            continue
        if wantedClass and not windowClass == wantedClass:
            continue
        if selectionFunction and not selectionFunction(hwnd):
            continue
        results.append(hwnd)
    return results
    
def dumpTopWindows():
    '''TODO'''
    topWindows = []
    win32gui.EnumWindows(_windowEnumerationHandler, topWindows)
    return topWindows
    
def dumpWindow(hwnd):
    '''Dump all controls from a window into a nested list
    
    Useful during development, allowing to you discover the structure of the
    contents of a window, showing the text and class of all contained controls.
    
    Think of it as a poor man's Spy++. ;-)

    Arguments:      The window handle of the top level window to dump.

    Returns         A nested list of controls. Each entry consists of the
                    control's hwnd, its text, its class, and its sub-controls,
                    if any.

    Usage example:  replaceDialog = findTopWindow(wantedText='Replace')
                    pprint.pprint(dumpWindow(replaceDialog))
    '''
    windows = []
    try:
        win32gui.EnumChildWindows(hwnd, _windowEnumerationHandler, windows)
    except win32gui.error:
        # No child windows
        return
    windows = [list(window) for window in windows]
    for window in windows:
        childHwnd, windowText, windowClass = window
        window_content = dumpWindow(childHwnd)
        if window_content:
            window.append(window_content)
            
    def dedup(thelist):
        '''De-duplicate deeply nested windows list.'''
        def listContainsSublists(thelist):
            return bool([sublist
                         for sublist in thelist
                         if isinstance(sublist, list)])
        found=[]
        def dodedup(thelist):
            todel = []
            for index, thing in enumerate(thelist):
                if isinstance(thing, list) and listContainsSublists(thing):
                    dodedup(thing)
                else:
                    if thing in found:
                        todel.append(index)
                    else:
                        found.append(thing)
            todel.reverse()
            for todel in todel:
                del thelist[todel]
        dodedup(thelist)
    dedup(windows)
    
    return windows

def findControl(topHwnd,
                wantedText=None,
                wantedClass=None,
                selectionFunction=None,
                maxWait=1,
                retryInterval=0.1):
    '''Find a control.
    
    You can identify a control within a top level window, using caption, class,
    a custom selection function, or any combination of these. (Multiple
    selection criteria are ANDed. If this isn't what's wanted, use a selection
    function.)
    
    If no control matching the specified selection criteria is found
    immediately, further attempts will be made. The retry interval and maximum
    time to wait for a matching control can be specified.

    Arguments:
    topHwnd             The window handle of the top level window in which the
                        required controls reside.
    wantedText          Text which the required control's captions must contain.
    wantedClass         Class to which the required control must belong.
    selectionFunction   Control selection function. Reference to a function
                        should be passed here. The function should take hwnd as
                        an argument, and should return True when passed the
                        hwnd of the desired control.
    maxWait             The maximum time to wait for a matching control, in
                        seconds.
    retryInterval       How frequently to look for a matching control, in
                        seconds

    Returns:            The window handle of the first control matching the
                        supplied selection criteria.
                    
    Raises:
    WinGuiAutoError     When no control or multiple controls found.

    Usage example:      optDialog = findTopWindow(wantedText="Options")
                        okButton = findControl(optDialog,
                                               wantedClass="Button",
                                               wantedText="OK")
    '''
    controls = findControls(topHwnd,
                            wantedText=wantedText,
                            wantedClass=wantedClass,
                            selectionFunction=selectionFunction)
    # check for None returned:  Tim 6 Jul 2004
    if controls==None:
        raise WinGuiAutoError("EnumChildWindows failed with win32gui.error "  +
                              repr(topHwnd) +
                              ", wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction) +
                              ", maxWait=" +
                              repr(maxWait) +
                              ", retryInterval=" +
                              str(retryInterval) 
                              )
    
    if len(controls) > 1:
        raise WinGuiAutoError("Multiple controls found for topHwnd=" +
                              repr(topHwnd) +
                              ", wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction) +
                              ", maxWait=" +
                              repr(maxWait) +
                              ", retryInterval=" +
                              str(retryInterval))
    elif controls:
        return controls[0]
    elif (maxWait-retryInterval) >= 0:
        time.sleep(retryInterval)
        try:
            return findControl(topHwnd=topHwnd,
                               wantedText=wantedText,
                               wantedClass=wantedClass,
                               selectionFunction=selectionFunction,
                               maxWait=maxWait-retryInterval,
                               retryInterval=retryInterval)
        except WinGuiAutoError:
            raise WinGuiAutoError("No control found for topHwnd=" +
                                  repr(topHwnd) +
                                  ", wantedText=" +
                                  repr(wantedText) +
                                  ", wantedClass=" +
                                  repr(wantedClass) +
                                  ", selectionFunction=" +
                                  repr(selectionFunction) +
                                  ", maxWait=" +
                                  repr(maxWait) +
                                  ", retryInterval=" +
                                  str(retryInterval))
    else:
        raise WinGuiAutoError("No control found for topHwnd=" +
                              repr(topHwnd) +
                              ", wantedText=" +
                              repr(wantedText) +
                              ", wantedClass=" +
                              repr(wantedClass) +
                              ", selectionFunction=" +
                              repr(selectionFunction) +
                              ", maxWait=" +
                              repr(maxWait) +
                              ", retryInterval=" +
                              str(retryInterval))

def findControls(topHwnd,
                 wantedText=None,
                 wantedClass=None,
                 selectionFunction=None):
    '''Find controls.
    
    You can identify controls using captions, classes, a custom selection
    function, or any combination of these. (Multiple selection criteria are
    ANDed. If this isn't what's wanted, use a selection function.)

    Arguments:
    topHwnd             The window handle of the top level window in which the
                        required controls reside.
    wantedText          Text which the required controls' captions must contain.
    wantedClass         Class to which the required controls must belong.
    selectionFunction   Control selection function. Reference to a function
                        should be passed here. The function should take hwnd as
                        an argument, and should return True when passed the
                        hwnd of a desired control.

    Returns:            The window handles of the controls matching the
                        supplied selection criteria.    

    Usage example:      optDialog = findTopWindow(wantedText="Options")
                        def findButtons(hwnd, windowText, windowClass):
                            return windowClass == "Button"
                        buttons = findControl(optDialog, wantedText="Button")
    '''
    def searchChildWindows(currentHwnd):
        results = []
        childWindows = []
        try:
            win32gui.EnumChildWindows(currentHwnd,
                                      _windowEnumerationHandler,
                                      childWindows)
        except win32gui.error:
            # This seems to mean that the control *cannot* have child windows,
            # i.e. is not a container.
            return
            
        for childHwnd, windowText, windowClass in childWindows:
            descendantMatchingHwnds = searchChildWindows(childHwnd)
            if descendantMatchingHwnds:
                results += descendantMatchingHwnds

            if wantedText and \
               not _normaliseText(wantedText) in _normaliseText(windowText):
                continue
            if wantedClass and \
               not windowClass == wantedClass:
                continue
            if selectionFunction and \
               not selectionFunction(childHwnd):
                continue
            results.append(childHwnd)
        return results

    # deduplicate the returned windows:  Tim 6 Jul 2004
    #return searchChildWindows(topHwnd)
    
    hlist=searchChildWindows(topHwnd)
    
    if hlist:
        # deduplicate the list:
        hdict={}
        for h in hlist:
            hdict[h]=''
        return hdict.keys()  
    else:
        return hlist
     
def getTopMenu(hWnd):
    '''Get a window's main, top level menu.
    
    Arguments:
    hWnd            The window handle of the top level window for which the top
                    level menu is required.

    Returns:        The menu handle of the window's main, top level menu.

    Usage example:  hMenu = getTopMenu(hWnd)
    '''
    return ctypes.windll.user32.GetMenu(ctypes.c_long(hWnd))

def activateMenuItem(hWnd, menuItemPath):
    '''Activate a menu item
    
    Arguments:
    hWnd                The window handle of the top level window whose menu you 
                        wish to activate.
    menuItemPath        The path to the required menu item. This should be a
                        sequence specifying the path through the menu to the
                        required item. Each item in this path can be specified
                        either as an index, or as a menu name.
                    
    Raises:
    WinGuiAutoError     When the requested menu option isn't found.

    Usage example:      activateMenuItem(notepadWindow, ('file', 'open'))
    
                        Which is exactly equivalent to...
                    
                        activateMenuItem(notepadWindow, (0, 1))
    '''
    # By Axel Kowald (kowald@molgen.mpg.de)
    # Modified by S Brunning to accept strings in addition to indicies.

    # Top level menu    
    hMenu = getTopMenu(hWnd)
    
    # Get top level menu's item count. Is there a better way to do this?
    # Yes .. Tim Couper 22 Jul 2004
    
    hMenuItemCount=win32gui.GetMenuItemCount(hMenu)
    
##    for hMenuItemCount in xrange(256):
##        try:
##            _getMenuInfo(hMenu, hMenuItemCount)
##        except WinGuiAutoError:
##            break
##    hMenuItemCount -= 1
    
    # Walk down submenus
    for submenu in menuItemPath[:-1]:
        try: # submenu is an index
            0 + submenu
            submenuInfo = _getMenuInfo(hMenu, submenu)
            hMenu, hMenuItemCount = submenuInfo.submenu, submenuInfo.itemCount
        except TypeError: # Hopefully, submenu is a menu name
            try:
                dump, hMenu, hMenuItemCount = _findNamedSubmenu(hMenu,
                                                                hMenuItemCount,
                                                                submenu)
            except WinGuiAutoError:
                raise WinGuiAutoError("Menu path " +
                                      repr(menuItemPath) +
                                      " cannot be found.")
           
    # Get required menu item's ID. (the one at the end).
    menuItem = menuItemPath[-1]
    try: # menuItem is an index
        0 + menuItem
        menuItemID = ctypes.windll.user32.GetMenuItemID(hMenu,
                                                        menuItem)
    except TypeError: # Hopefully, menuItem is a menu name
        try:
            subMenuIndex, dump, dump = _findNamedSubmenu(hMenu,
                                        hMenuItemCount,
                                        menuItem)
        except WinGuiAutoError:
            raise WinGuiAutoError("Menu path " +
                                  repr(menuItemPath) +
                                  " cannot be found.")
        menuItemID = ctypes.windll.user32.GetMenuItemID(hMenu, subMenuIndex)

    # Activate    
    win32gui.PostMessage(hWnd, win32con.WM_COMMAND, menuItemID, 0)

##def findMenuItems(hWnd,wantedText):
##    """Finds menu items whose captions contain the text"""
##    hMenu = getTopMenu(hWnd)
##    hMenuItemCount=win32gui.GetMenuItemCount(hMenu)
##    
##    for topItem in xrange(hMenuItemCount):
##            
    
def getMenuInfo(hWnd, menuItemPath):
    '''TODO'''
    
    # Top level menu    
    hMenu = getTopMenu(hWnd)
        
    # Get top level menu's item count. Is there a better way to do this?
    # Yes .. Tim Couper 22 Jul 2004
    hMenuItemCount=win32gui.GetMenuItemCount(hMenu)
    
##    for hMenuItemCount in xrange(256):
##        try:
##            _getMenuInfo(hMenu, hMenuItemCount)
##        except WinGuiAutoError:
##            break
##    hMenuItemCount -= 1
    submenuInfo=None 
    
    # Walk down submenus
    for submenu in menuItemPath:
        try: # submenu is an index
            0 + submenu
            submenuInfo = _getMenuInfo(hMenu, submenu)
            hMenu, hMenuItemCount = submenuInfo.submenu, submenuInfo.itemCount
        except TypeError: # Hopefully, submenu is a menu name
            try:
                submenuIndex, new_hMenu, hMenuItemCount = _findNamedSubmenu(hMenu,
                                                                hMenuItemCount,
                                                                submenu)
                submenuInfo = _getMenuInfo(hMenu, submenuIndex)
                hMenu = new_hMenu
            except WinGuiAutoError:
                raise WinGuiAutoError("Menu path " +
                                      repr(menuItemPath) +
                                      " cannot be found.")
    if submenuInfo==None:
        raise WinGuiAutoError("Menu path " +
                              repr(menuItemPath) +
                              " cannot be found. (Null menu path?)")
        
    
    return submenuInfo
    
def _getMenuInfo(hMenu, uIDItem):
    '''Get various info about a menu item.
    
    Arguments:
    hMenu               The menu in which the item is to be found.
    uIDItem             The item's index

    Returns:            Menu item information object. This object is basically
                        a 'bunch'
                        (see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308).
                        It will have useful attributes: name, itemCount,
                        submenu, isChecked, isDisabled, isGreyed, and
                        isSeparator
                    
    Raises:
    WinGuiAutoError     When the requested menu option isn't found.       

    Usage example:      submenuInfo = _getMenuInfo(hMenu, submenu)
                        hMenu, hMenuItemCount = submenuInfo.submenu, submenuInfo.itemCount
    '''
    # An object to hold the menu info
    class MenuInfo(Bunch):
        pass
    menuInfo = MenuInfo()

    # Menu state    
    menuState = ctypes.windll.user32.GetMenuState(hMenu,
                                                  uIDItem,
                                                  win32con.MF_BYPOSITION)
    if menuState == -1:
        raise WinGuiAutoError("No such menu item, hMenu=" +
                              str(hMenu) +
                              " uIDItem=" +
                              str(uIDItem))
    
    # Menu name
    menuName = ctypes.c_buffer("\000" * 32)
    ctypes.windll.user32.GetMenuStringA(ctypes.c_int(hMenu),
                                        ctypes.c_int(uIDItem),
                                        menuName, ctypes.c_int(len(menuName)),
                                        win32con.MF_BYPOSITION)
    menuInfo.name = menuName.value

    # Sub menu info
    menuInfo.itemCount = menuState >> 8
    if bool(menuState & win32con.MF_POPUP):
        menuInfo.submenu = ctypes.windll.user32.GetSubMenu(hMenu, uIDItem)
    else:
        menuInfo.submenu = None
        
    menuInfo.isChecked = bool(menuState & win32con.MF_CHECKED)
    menuInfo.isDisabled = bool(menuState & win32con.MF_DISABLED)
    menuInfo.isGreyed = bool(menuState & win32con.MF_GRAYED)
    menuInfo.isSeparator = bool(menuState & win32con.MF_SEPARATOR)
    # ... there are more, but these are the ones I'm interested in thus far.
    
    return menuInfo

def clickButton(hwnd):
    '''Simulates a single mouse click on a button

    Arguments:
    hwnd    Window handle of the required button.

    Usage example:  okButton = findControl(fontDialog,
                                           wantedClass="Button",
                                           wantedText="OK")
                    clickButton(okButton)
    '''
    _sendNotifyMessage(hwnd, win32con.BN_CLICKED)

def clickStatic(hwnd):
    '''Simulates a single mouse click on a static

    Arguments:
    hwnd    Window handle of the required static.

    Usage example:  TODO
    '''
    _sendNotifyMessage(hwnd, win32con.STN_CLICKED)

def doubleClickStatic(hwnd):
    '''Simulates a double mouse click on a static

    Arguments:
    hwnd    Window handle of the required static.

    Usage example:  TODO
    '''
    _sendNotifyMessage(hwnd, win32con.STN_DBLCLK)

def getComboboxItems(hwnd):
    '''Returns the items in a combo box control.

    Arguments:
    hwnd            Window handle for the combo box.

    Returns:        Combo box items.

    Usage example:  fontCombo = findControl(fontDialog, wantedClass="ComboBox")
                    fontComboItems = getComboboxItems(fontCombo)
    '''
    
    return _getMultipleWindowValues(hwnd,
                                    getCountMessage=win32con.CB_GETCOUNT,
                                    getValueMessage=win32con.CB_GETLBTEXT)

def selectComboboxItem(hwnd, item):
    '''Selects a specified item in a Combo box control.

    Arguments:
    hwnd            Window handle of the required combo box.
    item            The reqired item. Either an index, of the text of the
                    required item.

    Usage example:  fontComboItems = getComboboxItems(fontCombo)
                    selectComboboxItem(fontCombo,
                                       random.choice(fontComboItems))
    '''
    try: # item is an index Use this to select
        0 + item
        win32gui.SendMessage(hwnd, win32con.CB_SETCURSEL, item, 0)
        _sendNotifyMessage(hwnd, win32con.CBN_SELCHANGE)
    except TypeError: # Item is a string - find the index, and use that
        items = getComboboxItems(hwnd)
        itemIndex = items.index(item)
        selectComboboxItem(hwnd, itemIndex)

def getListboxItems(hwnd):
    '''Returns the items in a list box control.

    Arguments:
    hwnd            Window handle for the list box.

    Returns:        List box items.

    Usage example:  docType = findControl(newDialog, wantedClass="ListBox")
                    typeListBox = getListboxItems(docType)
    '''
    
    return _getMultipleWindowValues(hwnd,
                                    getCountMessage=win32con.LB_GETCOUNT,
                                    getValueMessage=win32con.LB_GETTEXT)

def selectListboxItem(hwnd, item):
    '''Selects a specified item in a list box control.

    Arguments:
    hwnd            Window handle of the required list box.
    item            The reqired item. Either an index, of the text of the
                    required item.

    Usage example:  docType = findControl(newDialog, wantedClass="ListBox")
                    typeListBox = getListboxItems(docType)
                    
                    # Select a type at random
                    selectListboxItem(docType,
                                      random.randint(0, len(typeListBox)-1))
    '''
    try: # item is an index Use this to select
        0 + item
        win32gui.SendMessage(hwnd, win32con.LB_SETCURSEL, item, 0)
        _sendNotifyMessage(hwnd, win32con.LBN_SELCHANGE)
    except TypeError: # Item is a string - find the index, and use that
        items = getListboxItems(hwnd)
        itemIndex = items.index(item)
        selectListboxItem(hwnd, itemIndex)
                                    
def getEditText(hwnd):
    '''Returns the text in an edit control.

    Arguments:
    hwnd            Window handle for the edit control.

    Returns         Edit control text lines.

    Usage example:  pprint.pprint(getEditText(editArea))
    '''
    return _getMultipleWindowValues(hwnd,
                                    getCountMessage=win32con.EM_GETLINECOUNT,
                                    getValueMessage=win32con.EM_GETLINE)
    
def setEditText(hwnd, text, append=False):
    '''Set an edit control's text.
    
    Arguments:
    hwnd            The edit control's hwnd.
    text            The text to send to the control. This can be a single
                    string, or a sequence of strings. If the latter, each will
                    be become a a separate line in the control.
    append          Should the new text be appended to the existing text?
                    Defaults to False, meaning that any existing text will be
                    replaced. If True, the new text will be appended to the end
                    of the existing text.
                    Note that the first line of the new text will be directly
                    appended to the end of the last line of the existing text.
                    If appending lines of text, you may wish to pass in an
                    empty string as the 1st element of the 'text' argument.

    Usage example:  print "Enter various bits of text."
                    setEditText(editArea, "Hello, again!")
                    setEditText(editArea, "You still there?")
                    setEditText(editArea, ["Here come", "two lines!"])
                    
                    print "Add some..."
                    setEditText(editArea, ["", "And a 3rd one!"], append=True)
    '''
    
    # Ensure that text is a list        
    try:
        text + ''
        text = [text]
    except TypeError:
        pass

    # Set the current selection range, depending on append flag
    if append:
        win32gui.SendMessage(hwnd,
                             win32con.EM_SETSEL,
                             -1,
                             0)
    else:
        win32gui.SendMessage(hwnd,
                             win32con.EM_SETSEL,
                             0,
                             -1)
                             
    # Send the text
    win32gui.SendMessage(hwnd,
                         win32con.EM_REPLACESEL,
                         True,
                         os.linesep.join(text))

def setCheckBox(hwnd, state = True):
	""" 
	Activates a CheckBox button.
	
	Inputs -
	hwnd - Handle of GUI element
	state - Boolean
	True - Activate the Checkbox
	False - Clear the CheckBox
	
	Outputs -
	Integer -- Result of the Win32gui.SendMessage Command
	
	Note: There is a 3rd state to a CheckBox. Since it is not
	common has been split to another function
	setCheckBox_Indeterminate.
	"""
	win32gui.SendMessage( 	hwnd,
				win32con.BM_SETCHECK,
				win32con.BST_CHECKED,
				0 )


def setCheckBox_Indeterminate(hwnd):
	""" 
	Activates a CheckBox button.
	
	Inputs -
	hwnd - Handle of GUI element
	
	Outputs -
	Integer -- Result of the Win32gui.SendMessage Command
	
	"""
	win32gui.SendMessage( 	hwnd,
				win32con.BM_SETCHECK,
				win32con.BST_INDETERMINATE,
				0 )

def getCheckBox(hwnd):
	""" 
	Returns the status from a CheckBox button.
	
	Inputs -
	hwnd - Handle of GUI element
	
	Outputs -
	0 - win32Gui send message error
	win32con.BST_CHECKED- The Checkbox is checked
	win32con.BST_INDETERMINATE - The Checkbox is checked and =
	greyed out.
	win32con.BST_UNCHECKED- The checkbox is not checked
	=20
	"""
	value = win32gui.SendMessage( 	hwnd,
					win32con.BM_GETCHECK,
					0,
					0 )
	return value

def _getMultipleWindowValues(hwnd, getCountMessage, getValueMessage):
    '''
    
    A common pattern in the Win32 API is that in order to retrieve a
    series of values, you use one message to get a count of available
    items, and another to retrieve them. This internal utility function
    performs the common processing for this pattern.

    Arguments:
    hwnd                Window handle for the window for which items should be
                        retrieved.
    getCountMessage     Item count message.
    getValueMessage     Value retrieval message.

    Returns:            Retrieved items.
    '''
    result = []
    
    MAX_VALUE_LENGTH = 256
    bufferlength  = struct.pack('i', MAX_VALUE_LENGTH) # This is a C style int.
    
    valuecount = win32gui.SendMessage(hwnd, getCountMessage, 0, 0)
    for itemIndex in range(valuecount):
        valuebuffer = array.array('c',
                                  bufferlength +
                                  ' ' * (MAX_VALUE_LENGTH - len(bufferlength)))
        valueLength = win32gui.SendMessage(hwnd,
                                           getValueMessage,
                                           itemIndex,
                                           valuebuffer)
        result.append(valuebuffer.tostring()[:valueLength])
    return result

def _windowEnumerationHandler(hwnd, resultList):
    '''win32gui.EnumWindows() callback.
    
    Pass to win32gui.EnumWindows() or win32gui.EnumChildWindows() to
    generate a list of window handle, window text, window class tuples.
    '''
    resultList.append((hwnd,
                       win32gui.GetWindowText(hwnd),
                       win32gui.GetClassName(hwnd)))
    
def _buildWinLong(high, low):
    '''Build a windows long parameter from high and low words.
    
    See http://support.microsoft.com/support/kb/articles/q189/1/70.asp
    '''
    # return ((high << 16) | low)
    return int(struct.unpack('>L',
                             struct.pack('>2H',
                                         high,
                                         low)) [0])
        
def _sendNotifyMessage(hwnd, notifyMessage):
    '''Send a notify message to a control.'''
    win32gui.SendMessage(win32gui.GetParent(hwnd),
                         win32con.WM_COMMAND,
                         _buildWinLong(notifyMessage,
                                       win32api.GetWindowLong(hwnd,
                                                              win32con.GWL_ID)),
                         hwnd)

def _normaliseText(controlText):
    '''Remove '&' characters, and lower case.
    
    Useful for matching control text.'''
    return controlText.lower().replace('&', '')

def _findNamedSubmenu(hMenu, hMenuItemCount, submenuName):
    '''Find the index number of a menu's submenu with a specific name.'''
    for submenuIndex in range(hMenuItemCount):
        submenuInfo = _getMenuInfo(hMenu, submenuIndex)
        if _normaliseText(submenuInfo.name).startswith(_normaliseText(submenuName)):
            return submenuIndex, submenuInfo.submenu, submenuInfo.itemCount
    raise WinGuiAutoError("No submenu found for hMenu=" +
                          repr(hMenu) +
                          ", hMenuItemCount=" +
                          repr(hMenuItemCount) +
                          ", submenuName=" +
                          repr(submenuName))

def _dedup(thelist):
    '''De-duplicate deeply nested list.'''
    found=[]
    def dodedup(thelist):
        for index, thing in enumerate(thelist):
            if isinstance(thing, list):
                dodedup(thing)
            else:
                if thing in found:
                    del thelist[index]
                else:
                    found.append(thing)
                
                              
class Bunch(object):
    '''See http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308'''
    
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
        
    def __str__(self):
        state = ["%s=%r" % (attribute, value)
                 for (attribute, value)
                 in self.__dict__.items()]
        return '\n'.join(state)
    
class WinGuiAutoError(Exception):
    pass
        
def self_test():
    '''Self test - drives Notepad and WordPad.'''
    # I'd like to use unittest here, but I've no idea how to automate these
    # tests. As it is, you just have to *watch* the test! ;-)
    import pprint, random
    
    # NT/2K/XP versions of Notepad have a different menu stuctures.
    WIN_VERSION_DECODE = {(1, 4, 0): "95",
                          (1, 4, 10): "98",
                          (1, 4, 90): "ME",
                          (2, 4, 0): "NT",
                          (2, 5, 0): "2K",
                          (2, 5, 1): "XP"}
    win_version = os.sys.getwindowsversion()
    win_version = WIN_VERSION_DECODE[win_version[3], win_version[0], win_version[1]]
    print "win_version=", win_version
    x=raw_input('->')
    print "Let's see what top windows we have at the 'mo:"
    pprint.pprint(dumpTopWindows())
    x=raw_input('->')
    print "Open and locate Notepad"
    os.startfile('notepad')
    notepadWindow = findTopWindow(wantedClass='Notepad')
    x=raw_input('->')
    print "Look at some menu item info"
    
    print 'File menu'
    print getMenuInfo(notepadWindow, ('file',))
    print "file|exit"
    print getMenuInfo(notepadWindow, ('file', 'exit'))
    x=raw_input('->')
    print "Open and locate the 'replace' dialogue"
    if win_version in ["NT"]:
        activateMenuItem(notepadWindow, ['search', 'replace'])
    elif win_version in ["2K", "XP"]:
        activateMenuItem(notepadWindow, ['edit', 'replace'])
    else:
        raise Exception("Tests not written for this OS yet. Feel free!")
    replaceDialog = findTopWindow(wantedText='Replace', wantedClass="#32770")
    x=raw_input('->')
    print "Locate the 'find' edit box"
    findValue = findControls(replaceDialog, wantedClass="Edit")[0]
    x=raw_input('->')                               
    print "Enter some text - and wait long enough for it to be seen"
    setEditText(findValue, "Hello, mate!")
    time.sleep(.5)
    x=raw_input('->')
    
    print "Locate the 'cancel' button, and click it."
    cancelButton = findControl(replaceDialog,
                               wantedClass="Button",
                               wantedText="Cancel")
    clickButton(cancelButton)
    x=raw_input('->')
    print "Open and locate the 'font' dialogue"
    if win_version in ["NT"]:
        activateMenuItem(notepadWindow, ['edit', 'set font'])
    elif win_version in ["2K", "XP"]:
        activateMenuItem(notepadWindow, ['format', 'font'])
    print findTopWindows(wantedText='Font', wantedClass="#32770")
    x=raw_input('->')
    fontDialog = findTopWindow(wantedText='Font', wantedClass="#32770")
    
    print "Let's see if dumping works. Dump the 'font' dialogue contents:"
    pprint.pprint(dumpWindow(fontDialog))
    x=raw_input('->')
    
    print "Change the font"
    fontCombos = findControls(fontDialog, wantedClass="ComboBox")
    print "Find the font selection combo"
    for fontCombo in fontCombos:
        fontComboItems = getComboboxItems(fontCombo)
        if 'Arial' in fontComboItems:
            break
    x=raw_input('->')
    print "Select at random"
    selectComboboxItem(fontCombo, random.choice(fontComboItems))
    time.sleep(.5)
    
    okButton = findControl(fontDialog, wantedClass="Button", wantedText="OK")
    clickButton(okButton)
    x=raw_input('->')
    
    print "Locate notepad's edit area, and enter various bits of text."
    editArea = findControl(notepadWindow,wantedClass="Edit")
    setEditText(editArea, "Hello, again!")
    time.sleep(.5)
    setEditText(editArea, "You still there?")
    time.sleep(.5)
    setEditText(editArea, ["Here come", "two lines!"])
    time.sleep(.5)
    x=raw_input('->')
    
    print "Add some..."
    setEditText(editArea, ["", "And a 3rd one!"], append=True)
    time.sleep(.5)
    
    print "See what's there now:"
    pprint.pprint(getEditText(editArea))
    x=raw_input('->')
    
    print "Exit notepad"
    activateMenuItem(notepadWindow, ('file', 'exit'))
    time.sleep(.5)
    
    print "Don't save."
    saveDialog = findTopWindow(selectionFunction=lambda hwnd:
                                                 win32gui.GetWindowText(hwnd)=='Notepad')
    noButton = findControl(saveDialog,wantedClass="Button", wantedText="no")
    clickButton(noButton)
    x=raw_input('->')
    
    print "Check you get an exception for non-existent top window"
    try:
        findTopWindow(wantedText="Banana")
        raise Exception("Test failed")
    except WinGuiAutoError, winGuiAutoError:
        print "Yup, got: ", str(winGuiAutoError)
    x=raw_input('->')
    print "OK, now we'll have a go with WordPad."
    os.startfile('wordpad')
    wordpadWindow = findTopWindow(wantedText='WordPad')
    x=raw_input('->')
    print "Open and locate the 'new document' dialog."
    activateMenuItem(wordpadWindow, [0, 0])
    newDialog = findTopWindow(wantedText='New', wantedClass="#32770")
    x=raw_input('->')
    print "Check you get an exception for non-existent control"
    try:
        findControl(newDialog, wantedClass="Banana")
        raise Exception("Test failed")
    except WinGuiAutoError, winGuiAutoError:
        print "Yup, got: ", str(winGuiAutoError)
    x=raw_input('->')
    print "Locate the 'document type' list box"
    docType = findControl(newDialog, wantedClass="ListBox")
    typeListBox = getListboxItems(docType)
    print "getListboxItems(docType)=", typeListBox
    x=raw_input('->')
    print "Select a type at random"
    selectListboxItem(docType, random.randint(0, len(typeListBox)-1))
    time.sleep(.5)
    clickButton(findControl(newDialog, wantedClass="Button", wantedText="OK"))
    x=raw_input('->')
    print "Check you get an exception for non-existent menu path"
    try:
        activateMenuItem(wordpadWindow, ('not', 'there'))
        raise Exception("Test failed")
    except WinGuiAutoError, winGuiAutoError:
        print "Yup, got: ", str(winGuiAutoError)
    x=raw_input('->')
    print "Check you get an exception for non-existent menu item"
    try:
        activateMenuItem(wordpadWindow, ('file', 'missing'))
        raise Exception("Test failed")
    except WinGuiAutoError, winGuiAutoError:
        print "Yup, got: ", str(winGuiAutoError)
    x=raw_input('->')    
    print "Exit wordpad"
    activateMenuItem(wordpadWindow, ('file', 'exit'))
    x=raw_input('->')
    print "Err, that's it."

if __name__ == '__main__':
    self_test()