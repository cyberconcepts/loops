#------------------------------------------------------
# AgentHome.py
# source file for agent UI
# author: Juergen Menzinger
# version: 0.1
#------------------------------------------------------

# one possibility is to always stay in the same class by calling its object instance as
# a return value when returning from a methodCall'. But this would require to change the current
# __init__ procedure so that the changes concerning the ini file are always directly written
# to the file or there is a routine which starts one time to initialize (maybe for example reading the
# whole ini File into the self.IniDict if it is not already filled and for each setting just chnaging the
# self.IniDict

from nevow import loaders, rend, static, url, inevow
from nevow.inevow import IRequest
from twisted.internet import defer

"""
Import could look like this:
from loops.agent.crawl.MailCrawler import MailCrawler
"""


# ---- global definitions ---------------------------------
# THIS SECTION IS USED FOR PROJECT INTERNAL DEBUG ONLY
INIFILE = "usermode.ini"
JOBFILE = "joblist.txt"
#----------------------------------------------------------


#/////////////////////////////////////////////////////////////////////////////////////////////
#----------------------------    AgentHome    --------------------------------------------------
# root page of the Agent UI
# every method called on the agent ui has it s child
# method inside here

class AgentHome(rend.Page):

    child_css = static.File('css')
    child_images = static.File('images')
    docFactory = loaders.xmlfile('AgentStart.html')


    def __init__(self,IniDict={}):
        
        #TODO: implement automatic reading of default ini file, or one passed via constructor
        #-------- ini settings ------------------------
        # THIS SECTION IS USED FOR PROJECT INTERNAL DEBUG ONLY
        self.iniFile = INIFILE
        self.IniDict = IniDict
        #-----------------------------------------------
        
        #-------- get ini settings from file --------
        # stores IniFile settings in self.IniDict

        if self.IniDict == {}:

            fPointer = open(self.iniFile,"r")
            IniSettings = fPointer.readlines()
 
            for iniLine in IniSettings:
                elem = iniLine.split(":")
                self.IniDict[elem[0]] = elem[1]
                
            fPointer.close()

        print "[AgentHome] self.UserMode: ", self.IniDict["UserMode"]


    """
    def locateChild(self, ctx, segments):
        return self, ()
        """
    # see nevow.url.py ?

    #///////////////////////////////////////////////////////////////////
    #----------AgentHome: CHILD PAGES SECTION--------------------------------------
    # this code section contains all child methods that load
    # a new (html-) page

    def child_joboverview(self,context):

        """ User requested page from menue: "job overview" """
        return JobOverView(self.IniDict)

    #//////////////////////////////////////////////////////////////////
    #--------AgentHome: CHILD METHODS SECTION-------------------------------------
    # this code section contains all form methods invoked in AgentHome
    # including their callback methods

    #---- page "Startpage" methods (class AgentHome) ----

    def child_ChangeUserMode(self,context):

        """User has klicked the Change User Mode button
           change UserMode from Simple <-> Professional"""

        print "[child_ChangeUserMode] UserMode: ", self.IniDict["UserMode"]
        print "[child_ChangeUserMode] ----retrieving form values----"
        
        form = IRequest(context).args

        if form != {}:

            for elem in form:
                print "[child_ChangeUserMode] ", form[elem]

        if self.IniDict["UserMode"] == "Simple":
            self.IniDict["UserMode"] = "Advanced"

        else:
            self.IniDict["UserMode"] = "Simple"
            print "[child_ChangeUserMode] : ", self.IniDict["UserMode"]

            """
            Write changed setting back to the iniFile ?
            filePointer = open(self.iniFile,"rw")
            """
            
        return AgentHome(self.IniDict)


    def child_collectOutlookMails(self,context):

        """User requested page from menue: "Collect Outlook Mails" """

        """
        deferred = MailCrawler.getOutlookMails()
        deferred.addCallback(self.defMailCrawl,context)
        deferred.addErrback(self.defMailCrawlError,context)

        return deferred
        """

        return AgentOutlookMailView(self.IniDict)



    def defMailCrawl(self,MailCollection,context):

        """here the returned collection is forwared to the page
        that is displaying it"""

        return AgentOutlookMailView(self.IniDict,MailCollection)


    def defMailCrawlError(self,ErrorMessage,context):

        """handles errors that ocurred in the MailCrawler"""

        return AgentHome(self.IniDict)
        

    #---- page "job overview" methods (class JobOverView)----

    def child_ViewJobDetails(self,context):
        
        form = IRequest(context).args
        selectedJob = form['jobList'][0]
        
        return JobOverViewDetails(self.IniDict, selectedJob)


    #////////////////////////////////////////////////////////////
    #-------------AgentHome: RENDER SECTION------------------------
    # this code section contains the Nevow Rendering Methods
    # for building the page element tree
        
    def render_getActiveUserMode(self,context,data):
        return self.IniDict["UserMode"]


    def render_getAgentVersion(self,context,data):
        return "0.1 alpha"


    

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////
#-----------------    PAGES SECTION    -------------------------------------------------------------------------
# all classes in this section are pages called via the navigation menue of AgentHome

class JobOverView(rend.Page):
    
    docFactory = loaders.xmlfile('AgentJobView.html')

    def __init__(self, IniDict):

        self.IniSettings = IniDict

    #-------------RENDER SECTION---------------------------------
    # this code section contains the Nevow Rendering Methods
    # for building the page element tree

    def data_displayViewForm(self,context,data):
        return "Overview of all running Crawling jobs"

    def render_getActiveUserMode(self,context,data):
        return self.IniSettings["UserMode"]

    def render_fillJobList(self,ctx,data):

        #---- get the registered jobs from the jobfile ----
        #
        fpJobFile = open(JOBFILE,"r")
        lines = fpJobFile.readlines()
        fpJobFile.close()
        patternList = []
        gen_pattern = inevow.IQ(ctx).patternGenerator('optionsJobList')

        for elem in lines:
            patternList.append(gen_pattern(data=elem))
 
        return patternList




class JobOverViewDetails(rend.Page):

    docFactory = loaders.xmlfile('AgentJobViewDetail.html')

    def __init__(self, IniDict={}, selectedJob=""):

        self.IniSettings = IniDict
        self.jobdetails = selectedJob


    #-------------RENDER SECTION---------------------------------
    # this code section contains the Nevow Rendering Methods
    # for building the page element tree

    def data_displayViewForm(self,context,data):
        return "Detailed view of crawling job."

    def render_getActiveUserMode(self,context,data):
        return self.IniSettings["UserMode"]

    def render_displayJobDetails(self,ctx,data):

        print "*******************************************************"
        print "[render_displayJobDetails] received form: ", str(self.jobdetails)
        print "[render_displayJobDetails] received IniForm: ", str(self.IniSettings)
        print "*******************************************************"

        patternList = []
        gen_pattern = inevow.IQ(ctx).patternGenerator('jobDetails')

        for elem in self.jobdetails:
            patternList.append(gen_pattern(data=elem))
 
        return patternList


class AgentOutlookMailView(rend.Page):

    docFactory = loaders.xmlfile('AgentOutlookMailView.html')

    def __init__(self, IniDict={}, MailCollection=[]):

        self.IniDict = IniDict
        self.MailCollection = MailCollection

    #-------------RENDER SECTION---------------------------------
    # this code section contains the Nevow Rendering Methods
    # for building the page element tree

    def data_displayViewForm(self,context,data):
        return "Detailed view of all collected Outlook Mails. [DEMO]"

    def render_getActiveUserMode(self,context,data):
        return self.IniDict["UserMode"]

    def render_displayOutlookMails(self,ctx,data):

        patternList = []
        gen_pattern = inevow.IQ(ctx).patternGenerator('OutlookMails')

        for elem in self.MailCollection:
            patternList.append(gen_pattern(data=elem))
 
        return patternList
