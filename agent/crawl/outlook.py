"""
This module reads out information from Microsoft Outlook.

The function loadInbox() reads all Emails of MsOutlook-inbox folder, 
optionally it is possible to read the subfolder of the inbox too.
The emails will be returnes as Python MIME objects in a list.

Tobias Schmid   26.07.2007
"""

import win32com.client
from email.mime.multipart import MIMEMultipart

# DEBUG FLAGS
DEBUG = 0
DEBUG_WRITELINE = 1

# some constants
COMMASPACE = ', '


class MSOutlook:
    def __init__(self):
        self.outlookFound = 0
        try:
            self.oOutlookApp = \
                win32com.client.gencache.EnsureDispatch("Outlook.Application")
            self.outlookFound = 1
        except:
            print "MSOutlook: unable to load Outlook"
        
        self.records = []
        self.mailList = []
              
                         
    def loadInbox(self, keys=None, subfolders=False):
        if not self.outlookFound:
            return
        
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> starting'

        # this should use more try/except blocks or nested blocks
        onMAPI = self.oOutlookApp.GetNamespace("MAPI")
        ofInbox = \
            onMAPI.GetDefaultFolder(win32com.client.constants.olFolderInbox)

        # fetch the mails of the inbox folder
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> fetch mails of inbox folder'
            
        for om in range(len(ofInbox.Items)):
            mail = ofInbox.Items.Item(om + 1)
            if mail.Class == win32com.client.constants.olMail:
                if keys is None:
                    # if we were't give a set of keys to use
                    # then build up a list of keys that we will be
                    # able to process
                    # I didn't include fields of type time, though
                    # those could probably be interpreted
                    keys = []
                    for key in mail._prop_map_get_:
                        if isinstance(getattr(mail, key), (int, str, unicode)):
                            keys.append(key)
                    if DEBUG:
                        keys.sort()
                        print 'Fields\n======================================'
                        for key in keys:
                            print key
                record = {}
                for key in keys:
                    record[key] = getattr(mail, key)
                    
                # Create the container (outer) email message.
                msg = MIMEMultipart()
                # subject
                msg['Subject'] = record['Subject'].encode('utf-8')
                
                # sender 
                sender = str(record['SenderName'].encode('utf-8')) #SenderEmailAddress
                msg['From'] = sender
                
                #recipients
                recipients = []
                for rec in range(record['Recipients'].__len__()):
                    recipients.append(getattr(record['Recipients'].Item(rec+1), 'Address'))
                msg['To'] = COMMASPACE.join(recipients)
                
                # message
                msg.preamble = record['Body'].encode('utf-8')
                
                # add the email message to the list
                self.mailList.append(msg)
                self.records.append(record)
 
                    
        """
        * Fetch the mails of the inbox subfolders
        """
        if subfolders:
            
            if DEBUG_WRITELINE:
                print 'MSOutlook.loadInbox() ===> fetch emails of subfolders'
            
            lInboxSubfolders = getattr(ofInbox, 'Folders') 
            for of in range(lInboxSubfolders.__len__()):
                # get a MAPI-folder object
                oFolder = lInboxSubfolders.Item(of + 1)
                # get items of the folder
                folderItems = getattr(oFolder, 'Items')
                for item in range(len(folderItems)):
                    mail = folderItems.Item(item+1)
                    if mail.Class == win32com.client.constants.olMail:
                        if keys is None:
                            keys = []
                            for key in mail._prop_map_get_:
                                if isinstance(getattr(mail, key), (int, str, unicode)):
                                    keys.append(key)
                            
                            if DEBUG:
                                keys.sort()
                                print 'Fiels\n======================================='
                                for key in keys:
                                    print key
                                    
                        record = {}
                        for key in keys:
                            record[key] = getattr(mail, key)
                        if DEBUG:
                            print of
                    
                        # Create the container (outer) email message.
                        msg = MIMEMultipart()
                        # subject
                        msg['Subject'] = record['Subject'].encode('utf-8')
                        
                        # sender
                        sender == record['SenderName'].encode('utf-8') #SenderEmailAddress
                        msg['From'] = sender
                       
                        # recipients
                        for rec in range(record['Recipients'].__len__()):
                            recipients.append(getattr(record['Recipients'].Item(rec+1), 'Address'))
                        msg['To'] = COMMASPACE.join(recipients)
                        
                        # message
                        msg.preamble = record['Body'].encode('utf-8')
                        
                        # add the email message to the list
                        self.mailList.append(msg)
                        self.records.append(record)
                
        if DEBUG:
            print 'number of mails in Inbox:', len(ofInbox.Items)
            # list of _Folder (subfolder of inbox)
            lInboxSubfolders = getattr(ofInbox, 'Folders')
            # get Count-Attribute of _Folders class
            iInboxSubfoldersCount = getattr(lInboxSubfolders, 'Count')
            # the Item-Method of the _Folders class returns a MAPIFolder object
            oFolder = lInboxSubfolders.Item(0) #1
            
            print 'Count of Inbox-SubFolders:', iInboxSubfoldersCount
            print 'Inbox sub folders (Folder/Mails):'
            for folder in range(iInboxSubfoldersCount):
                oFolder = lInboxSubfolders.Item(folder+1)
                print getattr(oFolder, 'Name'), '/' , len(getattr(oFolder, 'Items')) 
                           
            
        if DEBUG_WRITELINE:
            print 'MSOutlook.loadInbox() ===> ending'
            
        return self.mailList
 
       

if __name__ == '__main__':
    if DEBUG:
        print 'attempting to load Outlook'
    oOutlook = MSOutlook()
    # delayed check for Outlook on win32 box
    if not oOutlook.outlookFound:
        print 'Outlook not found'
        sys.exit(1)

    fieldsMail = ['Body',
                     'HTMLBody',
                     'CC',
                     'SenderName',
                     'Recipients',
                     'To',
                     'Attachments',
                     'Subject'
                     ]
    #                    'BodyFormat',  removed BodyFormat temporarily because it is not available in Outlook.9 (Office2000)
    #                     'SenderEmailAddress', replaced by SenderName

    if DEBUG:
        import time
        print 'loading records...'
        startTime = time.time()
   
    mails = oOutlook.loadInbox(fieldsMail)

    for elem in mails:
        print str(elem)
    
    if DEBUG_WRITELINE:
        print '***Back in main() with some emails in a list....***'
        print 'Mails fetched from MSOutlook inbox folder:', mails.__len__()
    
    if DEBUG:
        print 'loading took %f seconds' % (time.time() - startTime)
