"""
This module reads out information from Microsoft Outlook.

The function loadInbox() reads all Emails of MsOutlook-inbox folder, 
optionally it is possible to read the subfolder of the inbox too.
The emails will be returnes as Python MIME objects in a list.

Tobias Schmid   26.07.2007
"""

import win32com.client
import ctypes 
import win32api, win32process, win32con
import re
from email.mime.multipart import MIMEMultipart

from watsup.winGuiAuto import findTopWindow, findControl, findControls, clickButton, \
                              getComboboxItems, selectComboboxItem, setCheckBox

from twisted.internet.defer import Deferred
from twisted.internet.task import coiterate
from twisted.internet import threads
from zope.interface import implements

from loops.agent.interfaces import IResource
from loops.agent.crawl.base import CrawlingJob as BaseCrawlingJob
from loops.agent.crawl.base import Metadata


# DEBUG FLAGS
DEBUG = 1
DEBUG_WRITELINE = 1

# some constants
COMMASPACE = ', '


class CrawlingJob(BaseCrawlingJob):

    keys = ""
    inbox = ""
    subfolders = ""
    pattern = ""

    def collect(self):
        self.collected = []
        coiterate(self.crawlOutlook()).addCallback(self.finished)
        # TODO: addErrback()
        self.deferred = Deferred()
        return self.deferred


    def finished(self, result):
        self.deferred.callback(self.collected)


    def crawlOutlook(self):
        outlookFound = 0
        try:
            oOutlookApp = \
                win32com.client.gencache.EnsureDispatch("Outlook.Application")
            outlookFound = 1
        except:
            print "MSOutlook: unable to load Outlook"
        
        records = []
        
        if not outlookFound:
            return

        # fetch the params
        criteria = self.params
        self.keys = criteria.get('keys') 
        self.inbox = criteria.get('inbox') #boolean 
        self.subfolders = criteria.get('subfolders') #boolean
        self.pattern = criteria.get('pattern')
        if self.pattern != '':
            self.pattern = re.compile(criteria.get('pattern') or '.*')
        else:
            self.pattern = None
        
        
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> starting'
            
        # try to handle the Outlook dialog
        #d = threads.deferToThread(self.handleOutlookDialog)
        #d.addCallback(self.printResult)

        # catch Inbox folder
        onMAPI = oOutlookApp.GetNamespace("MAPI")
        ofInbox = \
            onMAPI.GetDefaultFolder(win32com.client.constants.olFolderInbox)

        # fetch the mails of the inbox folder
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> fetch mails of inbox folder'
        
        # fetch mails from inbox  
        if self.inbox:
            self.loadEmail(ofInbox)                 
                        
        # fetch mails of inbox subfolders 
        if self.subfolders and self.pattern is None:
            
            if DEBUG_WRITELINE:
                print 'MSOutlook.loadInbox() ===> fetch emails of subfolders'
            
            lInboxSubfolders = getattr(ofInbox, 'Folders') 
            for of in range(lInboxSubfolders.__len__()):
                # get a MAPI-folder object and load its emails
                self.loadEmail(lInboxSubfolders.Item(of + 1))
        
        # pattern, just read the specified subfolder             
        elif self.subfolders and self.pattern:
             
            if DEBUG_WRITELINE:
                print 'MSOutlook.loadInbox() ===> fetch emails of specified subfolder'            
            lInboxSubfolders = getattr(ofInbox, 'Folders') 
            for of in range(lInboxSubfolders.__len__()):
                # get a MAPI-folder object and load its emails
                if self.pattern.match(getattr(lInboxSubfolders.Item(of + 1), 'Name')):
                    self.loadEmail(lInboxSubfolders.Item(of + 1)) #oFolder
                
                
        if DEBUG:
            print 'number of mails in Inbox:', len(ofInbox.Items)
            # list of _Folder (subfolder of inbox)
            lInboxSubfolders = getattr(ofInbox, 'Folders')
            # get Count-Attribute of _Folders class
            iInboxSubfoldersCount = getattr(lInboxSubfolders, 'Count')
            # the Item-Method of the _Folders class returns a MAPIFolder object
            oFolder = lInboxSubfolders.Item(1)
            
            print 'Count of Inbox-SubFolders:', iInboxSubfoldersCount
            print 'Inbox sub folders (Folder/Mails):'
            for folder in range(iInboxSubfoldersCount):
                oFolder = lInboxSubfolders.Item(folder+1)
                print getattr(oFolder, 'Name'), '/' , len(getattr(oFolder, 'Items')) 
                           
            
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> ending'
        yield '1'
    
    
    def loadEmail(self, oFolder):
        # get items of the folder
        folderItems = getattr(oFolder, 'Items')
        for item in range(len(folderItems)):
            mail = folderItems.Item(item+1)
            if mail.Class == win32com.client.constants.olMail:
                if self.keys is None:
                    self.keys = []
                    for key in mail._prop_map_get_:
                        if isinstance(getattr(mail, key), (int, str, unicode)):
                            self.keys.append(key)
                    
                    if DEBUG:
                        self.keys.sort()
                        print 'Fiels\n======================================='
                        for key in self.keys:
                            print key
                            
                record = {}
                for key in self.keys:
                    record[key] = getattr(mail, key)
                if DEBUG:
                    print str(item)
            
                # Create the mime email object
                msg = self.createEmailMime(record)
                
                # list with mime objects
                self.collected.append((OutlookResource(msg)))
     
     
    def createEmailMime(self, emails):
        # Create the container (outer) email message.
        msg = MIMEMultipart()
        # subject
        msg['Subject'] = emails['Subject'].encode('utf-8')
                
        # sender
        if emails.has_key('SenderEmailAddress'):
            sender = str(emails['SenderEmailAddress'].encode('utf-8'))
        else:
            sender = str(emails['SenderName'].encode('utf-8'))            
        msg['From'] = sender

        # CC
        #msg['CC'] = str(emails['CC'].encode('utf-8'))

        # ReceivedTime
        #msg['Date'] = str(emails['ReceivedTime'])
                
        #recipients
        recipients = []

        if emails.has_key('Recipients'):
            for rec in range(emails['Recipients'].__len__()):
                recipients.append(getattr(emails['Recipients'].Item(rec+1), 'Address'))
                msg['To'] = COMMASPACE.join(recipients)
        else:
            recipients.append(emails['To'])
            msg['To'] = COMMASPACE.join(recipients)           
               
        # message
        msg.preamble = emails['Body'].encode('utf-8')
        
        return msg


    def handleOutlookDialog(self):
        """
        This function handles the outlook dialog, which appears if someone
        tries to access to MS Outlook.
        """

        hwnd = None
        
        while True: 
            hwnd = ctypes.windll.user32.FindWindowExA(None, hwnd, None, None)
            print 'searching....'
            if hwnd == None: 
                    break 
            else: 
                val = u"\0" * 1024 
                ctypes.windll.user32.GetWindowTextW(hwnd, val, len(val)) 
                val = val.replace(u"\000", u"") 
                
                if val and repr(val) == "u'Microsoft Office Outlook'":
                    print repr(val)
                    print '===> MSOutlook dialog box found'
                    #tid, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # get a handle
                    #handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
                    # terminate the process by the handle
                    #win32api.TerminateProcess(handle, 0)
                    # close the handle - thankyou
                    #win32api.CloseHandle(handle)
                    
                    # get the Main Control
                    form = findTopWindow(wantedText='Microsoft Office Outlook')
                    controls = findControls(form)
                    
                    # get the check box
                    checkBox = findControl(form, wantedText='Zugriff')
                    setCheckBox(checkBox, 1)
                    
                    # get the combo box
                    comboBox = findControl(form, wantedClass='ComboBox')
                    items = getComboboxItems(comboBox)
                    selectComboboxItem(comboBox, items[3])#'10 Minuten'                   
                
                    # finally get the button and click it
                    button = findControl(form, wantedText = 'Erteilen')
                    clickButton(button)
                    print '-> dialog found and handled'
                    break

    def printResult(self):
        print '--> Outlook dialog handled'


class OutlookResource(object):

    implements(IResource)

    def __init__(self, oEmail):
        self.oEmail = oEmail

    @property
    def data(self):
        return self.oEmail   
    
