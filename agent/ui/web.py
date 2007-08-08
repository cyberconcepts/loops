#------------------------------------------------------
# AgentHome.py
# source file for agent UI
# author: Juergen Menzinger
# version: 0.1
#------------------------------------------------------

import os
from nevow import loaders, rend, static, url, inevow, tags
from nevow.inevow import IRequest
from twisted.internet import defer

from loops.agent.crawl.outlook import MSOutlook
from loops.agent import core

# ---- global definitions and settings ---------------------------------
os.environ['HOME'] = os.path.dirname(core.__file__)
OUTLOOK2000 = 1
JOBCONFIGS = os.path.join(os.path.expanduser('~'),'jobconf.txt')
MAIL_DIR = os.path.join(os.path.expanduser('~'),'mails')
agent = core.Agent()
config = agent.config
resourcesDirectory = 'resources'
templatesDirectory = 'templates'
#----------------------------------------------------------


def template(fn):
    return loaders.xmlfile(os.path.join(templatesDirectory, fn))

def getConfigIndex(index_name, default_value, fn=None):
    iterator = 0
    index_used = True
    #check what crawling jobs exist to create a valid job index
    while index_used == True:
        if config.crawl[iterator].setdefault(index_name,default_value) == default_value:
            index_used = False
        else:
            index_used = True
            iterator = iterator + 1
    return iterator


# AgentHome 
# root page of the Agent UI

class AgentHome(rend.Page):

    """Main class that builds the root ressource for the loops agent ui.

    Instance variables:
    usermode -- can be 'Simple' or 'Advanced'

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Load the initial start-up settings from config

    """
    
    child_resources = static.File(resourcesDirectory)
    docFactory = template('agent.html')
    
    def __init__(self,first_start=1):
        """ Initialize the AgentHome object.

        If first_start = 1 then the initalization procedure is run, which mainly
        loads the stored settings from the agent ini-file into instance variables of the class.

        Keyword arguments:
        first_start -- defaults to 1

        """
        print "[PAGECLASS] AgentHome"
        if first_start == 1:
            self.usermode = config.ui.web.setdefault('usermode','Simple')
            print "[AgentHome] setting self.usermode: ", config.ui.web.usermode
        
    """
    def locateChild(self, ctx, segments):
        return self, ()
    """
    
    # calls to child pages
    
    def child_joboverview(self,context):
        """ User requested page from menue: 'job overview' """
        return JobOverView()

    def child_collectOutlookMails(self,context):
        """Display page for starting Outlook Crawler"""
        return AgentOutlookMailCrawl()

    def child_viewOutlookMails(self,context):
        """Display page that shows all currently collected Outlook Mails."""
        return AgentOutlookMailView()

    # "Startpage" methods (class AgentHome)

    def child_changeUserMode(self,context):
        """Change user mode.

        User has klicked the Change User Mode button, so
        change UserMode from Simple <-> Professional

        """
        print "[child_changeUserMode] UserMode: ", config.ui.web.usermode
        print "[child_changeUserMode] ----retrieving form values----"
        form = IRequest(context).args
        if form != {}:
            for elem in form:
                print "[child_changeUserMode] ", form[elem]
        if config.ui.web.usermode == "Simple":
            config.ui.web.usermode = "Advanced"
        else:
            config.ui.web.usermode = "Simple"
            print "[child_changeUserMode] : ", config.ui.web.usermode
        config.save()
        return AgentHome(first_start=0)

    # "job overview" methods (class JobOverView)

    def child_ViewJobDetails(self,context):
        """Get details for the selected job.

        Reads all information about the selected job from file/ database.
        Returns page object which displays the available information.

        """
        selected_job = ((IRequest(context).uri).split("?"))[1]
        JOBDETAILS = 'joblist.txt'
        file_pointer = open(JOBDETAILS,"r")
        job_details = ""
        job_list = file_pointer.readlines()
        for line in job_list:
            if line.startswith(selected_job):
                job_details = line
                break
        file_pointer.close()
        job_details = job_details.split(";")
        return JobOverViewDetails(job_details)

    # "collect Outlook Mails" methods (class AgentOutlookMailCrawl)

    def child_submitOutlookCrawlJob(self,context):
        """Initiate Outlook crawling job as requested by user."""
        
        ag = core.Agent()
        config2 = ag.config     
        conf = config2
        crawlSubfolder = False
        form = IRequest(context).args
        if form != {}:
            iterator = getConfigIndex('type','unused')     
            #save job configuration
            if form['mailCrawlInterval'][0] == "oneTime":
                conf.load('crawl[%i].state = "completed"' %(iterator))
            else:
                conf.load('crawl[%i].state = "active"' %(iterator))   
            conf.load('crawl[%i].jobid = "outlook%i"' %(iterator, iterator))
            conf.load('crawl[%i].type = "OutlookMail"' %(iterator))
            conf.load('crawl[%i].folder = "%s"'%(iterator,form["searchFolder"][0])) #always Inbox, ev. read from Outlook which folders are available?
            conf.load('crawl[%i].getsubfolder = "%s"'%(iterator,form["selectSubfolder"][0]))
            conf.load('crawl[%i].latest = ""'%(iterator)) #TODO: who does parsing? 
            conf.load('crawl[%i].filter_criteria = "%s"'%(iterator,form["selectFilterCriteria"][0]))
            conf.load('crawl[%i].filter_pattern = "%s"'%(iterator,form["filterPattern"][0]))
            conf.load('crawl[%i].content_format = "%s"'%(iterator,form["selectContentFormat"][0]))
            conf.load('crawl[%i].include_attachements = "%s"'%(iterator,form["selectAttachements"][0]))
            conf.load('crawl[%i].interval = "%s"'%(iterator,form["mailCrawlInterval"][0]))
            conf.save()

            if form["mailCrawlInterval"][0] == 'oneTime':
                if OUTLOOK2000 == 1:
                    #Outlook2000 (= Outlook 9) has different attributes
                    fieldsMail = ['Body',
                                  'HTMLBody',
                                  'CC',
                                  'SenderName',
                                  'Recipients',
                                  'To',
                                  'Attachments',
                                  'Subject'
                                 ]
                else:
                    fieldsMail = ['Body',
                                  'BodyFormat',
                                  'HTMLBody',
                                  'CC',
                                  'SenderEmailAddress',
                                  'Recipients',
                                  'To',
                                  'Attachments',
                                  'Subject'
                                 ]
                if form["selectSubfolder"][0] == 'Yes':
                    crawlSubfolder = True

                OutlookObj = MSOutlook()
                mails = OutlookObj.loadInbox(fieldsMail,crawlSubfolder)
                # currently deferreds are not implemented in outlook.py
                #deferred.addCallback(self.defMailCrawl,context)
                #deferred.addErrback(self.defMailCrawlError,context)
                #return deferred
                return self.defMailCrawl(mails,context)
            else:
                #TODO implement forwarding to next form (scheduler)
                return AgentOutlookMailCrawl("Scheduled Mail Crawling not implemented yet.") 
                
        else:
            return AgentOutlookMailCrawl("An error occurred: form data has been empty.")                  
        return AgentOutlookMailCrawl("Crawl Job settings have been saved.")
        
    def defMailCrawl(self,mail_collection,context):
        """Save and Forward the mail collection to a page view."""
        files = os.listdir(MAIL_DIR)
        filename = "Mail%i" %(len(files))
        print "Writing emails to files."
        for elem in mail_collection:
            fp = open((os.path.join(MAIL_DIR,filename)),'w')
            fp.write(str(elem))
            fp.close()
        return AgentOutlookMailView(mail_collection)

    def defMailCrawlError(self,ErrorMessage,context):
        """Handles errors that ocurred in the MailCrawler."""
        return AgentHome(first_start=0)

    # rendering methods of Startpage

    def render_getActiveUserMode(self,context,data):
        return config.ui.web.usermode

    def render_getAgentVersion(self,context,data):
        return "0.1 alpha"

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]

    
class FooterFragment(rend.Fragment):
    docFactory = template('footer.html')


class NavigationFragment(rend.Fragment):
    docFactory = template('navigation.html')


class TopFragment(rend.Fragment):
    docFactory = template('top.html')


class HeaderFragment(rend.Fragment):
    docFactory = template('header.html')

   
# subpages of AgentHome

class JobOverView(rend.Page):

    """Builds page that lists all currently registered jobs.

    Instance variables:
    currently none in use

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the initial settings retrieved from AgentHome.

    """
    
    docFactory = template('joblisting.html')

    def __init__(self):
        print "[PAGECLASS] JobOverView"

    # rendering methods of job overview
    
    def data_displayViewForm(self,context,data):
        return "Overview of all running Crawling jobs"

    def render_getActiveUserMode(self,context,data):
        return config.ui.web.usermode

    def render_fillJobTable(self,ctx,data):
        """Build table which displays all registered jobs."""

        #---- get the registered jobs from the jobfile ----
        joblist = []
        iterator = 0
        config.load()
        while iterator < len(config.crawl):
            joblist.append(dict(config.crawl[iterator].items()))
            iterator = iterator + 1
        for elem in joblist:
            print elem
        job_table = [tags.tr
                        [
                          tags.td
                             [
                               tags.a(href="ViewJobDetails?%s" %(job_details['jobid']))
                                  [
                                    tags.b
                                        [
                                            "[" + job_details['jobid'] +"]"
                                        ]
                                  ]
                             ],
                          tags.td[job_details['state']],
                          tags.td[job_details['interval']],
                          tags.td[job_details['filter_criteria']],
                          tags.td[job_details['folder']]
                        ]
                     for job_details in joblist
                     ]
        return job_table

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]


class JobOverViewDetails(rend.Page):
    
    """Builds page that displays detailed information about a selected job.

    Instance variables:
    jobdetails -- list that contains all available job information

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the selected job in member variable.

    """

    docFactory = template('jobdetail.html')

    def __init__(self, selectedJob=[]):
        print "[PAGECLASS] JobOverViewDetails"
        self.jobdetails = selectedJob

    # rendering methods of job view details

    def data_displayViewForm(self,context,data):
        return "Detailed view of crawling job."

    def render_getActiveUserMode(self,context,data):
        return config.ui.web.usermode

    def render_displayJobDetails(self,ctx,data):
        """Build the table containing information about the selected job."""

        print "*******************************************************"
        print "[render_displayJobDetails] received form: ", str(self.jobdetails)
        print "[render_displayJobDetails] usermode: ", config.ui.web.usermode
        print "*******************************************************"
        job_detail = []
        job_detail = [tags.tr
                          [
                              tags.td["PID"],
                              tags.td[self.jobdetails[0]]
                          ],
                       tags.tr
                          [
                              tags.td["State"],
                              tags.td[self.jobdetails[1]]
                          ],
                      tags.tr
                         [
                              tags.td["Interval"],
                              tags.td[self.jobdetails[2]]
                         ],
                      tags.tr
                          [
                              tags.td["Search Criteria"],
                              tags.td[self.jobdetails[3]]
                          ],
                      tags.tr
                          [
                              tags.td["Job Scope"],
                              tags.td[self.jobdetails[4]]
                            ],
                      tags.tr
                          [
                              tags.td["Filter"],
                              tags.td[self.jobdetails[5]]
                            ],
                      tags.tr
                          [
                              tags.td["Follow Up Tasks"],
                              tags.td[self.jobdetails[6]]
                            ]
                      ]
        return job_detail

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]


class AgentOutlookMailView(rend.Page):
    
    """Builds page that displays an overview of all collected mails.

    Instance variables:
    page_message -- string that is displayed on the page
    mail_collection -- collection containing all currently collected mails.

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the mail collection object and the pagemessage

    """

    docFactory = template('mail.html')

    def __init__(self, mail_collection=[], pagemessage=""):
        print "[PAGECLASS] AgentOutlookMailView"
        self.mail_collection = mail_collection
        self.page_message = pagemessage

    # rendering methods of Collect Outlook Mails

    def data_displayViewForm(self,context,data):
        return "Detailed view of all collected Outlook Mails."

    def render_getActiveUserMode(self,context,data):
        return config.ui.web.usermode

    def render_systemMessage(self,context,data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_displayOutlookMails(self,ctx,data):
        """Builds table containing all currently collected mails."""
        if self.mail_collection != []:        
            mail_table = [tags.tr
                         [
                          tags.td
                             [
                               tags.a(href="ViewMailDetails?%s" %(str(mailObject.get('SenderName'))))
                                  [
                                    tags.b
                                        [
                                            "[" + str(mailObject.get('SenderName')) +"]"
                                        ]
                                  ]
                             ],
                          tags.td[str(mailObject.get('CC'))],
                          tags.td[str(mailObject.get('Subject'))],
                          tags.td[str(mailObject.get('To'))],
                          tags.td['SourceFolder']
                        ]
                     for mailObject in self.mail_collection
                     ]
            return mail_table
        else:
            mailFiles = os.listdir(MAIL_DIR)
            #TODO: read mail data from files
            mail_table = [tags.tr
                         [
                          tags.td
                             [
                               tags.a(href="ViewMailDetails?%s" %(str(mail)))
                                  [
                                    tags.b
                                        [
                                            "[" + str(mail) +"]"
                                        ]
                                  ]
                             ],
                          tags.td[str(mail)],
                          tags.td[str(mail)],
                          tags.td[str(mail)],
                          tags.td[str(mail)]
                        ]
                     for mail in mailFiles
                     ]                
            return mail_table
            

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]


class AgentOutlookMailCrawl(rend.Page):
    
    """Builds page where an Outlook Mail Crawler can be configured and run.

    Instance variables:
    page_message -- string that is displayed on the page

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- store pagemessage in member variable

    """

    docFactory = template('mailcrawl.html')

    def __init__(self, pagemessage=""):
        print "[PAGECLASS] AgentOutlookMailCrawl"
        self.page_message = pagemessage

    # rendering methods of Collect Outlook Mails

    def data_displayViewForm(self,context,data):
        return "Configure your MailCrawl Job in the form below.\
                 You then can either choose to start it as a\
                 single job, or as scheduled job (further input\
                 for scheduler necessary). For each new collect\
                 procedure a filter will be added, so that just\
                 mails received in Outlook after the recent Crawl\
                 Job has been run, will be collected."

    def render_getActiveUserMode(self,context,data):
        return config.ui.web.usermode

    def render_displayOutlookMails(self,ctx,data):
        """Currently no implementation"""
        return ""

    def render_systemMessage(self,context,data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]
    
