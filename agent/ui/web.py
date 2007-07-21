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

"""
Import could look like this:
from loops.agent.crawl.MailCrawler import MailCrawler
"""

# ---- global definitions ---------------------------------
# THIS SECTION IS USED FOR PROJECT INTERNAL DEBUG ONLY
INIFILE = "usermode.ini"
JOBFILE = "joblist.txt"
#----------------------------------------------------------

resourcesDirectory = 'resources'
templatesDirectory = 'templates'

def template(fn):
    return loaders.xmlfile(os.path.join(templatesDirectory, fn))

# AgentHome 
# root page of the Agent UI

class AgentHome(rend.Page):
    
    child_resources = static.File(resourcesDirectory)
    docFactory = template('agent.html')
    
    def __init__(self,ini_dict={}):

        #TODO: implement automatic reading of default ini file, or one passed via constructor
        #-------- ini settings ------------------------
        # THIS SECTION IS USED FOR PROJECT INTERNAL DEBUG ONLY
        self.ini_file = INIFILE
        self.ini_dict = ini_dict
        #-----------------------------------------------
        #-------- get ini settings from file --------
        if self.ini_dict == {}:

            file_pointer = open(self.ini_file,"r")
            ini_settings = file_pointer.readlines()
            for ini_line in ini_settings:
                elem = ini_line.split(":")
                self.ini_dict[elem[0]] = elem[1]
            file_pointer.close()
        print "[AgentHome] self.UserMode: ", self.ini_dict["UserMode"]

    """
    def locateChild(self, ctx, segments):
        return self, ()
    """
    
    # child pages
    
    def child_joboverview(self,context):
        """ User requested page from menue: 'job overview' """
        return JobOverView(self.ini_dict)

    # "Startpage" methods (class AgentHome)

    def child_ChangeUserMode(self,context):
        """User has klicked the Change User Mode button, so
           change UserMode from Simple <-> Professional"""

        print "[child_ChangeUserMode] UserMode: ", self.ini_dict["UserMode"]
        print "[child_ChangeUserMode] ----retrieving form values----"
        form = IRequest(context).args
        if form != {}:
            for elem in form:
                print "[child_ChangeUserMode] ", form[elem]
        if self.ini_dict["UserMode"] == "Simple":
            self.ini_dict["UserMode"] = "Advanced"
        else:
            self.ini_dict["UserMode"] = "Simple"
            print "[child_ChangeUserMode] : ", self.ini_dict["UserMode"]
        return AgentHome(self.ini_dict)

    def child_collectOutlookMails(self,context):
        """User requested page from menue: "Collect Outlook Mails" """

        """
        deferred = MailCrawler.getOutlookMails()
        deferred.addCallback(self.defMailCrawl,context)
        deferred.addErrback(self.defMailCrawlError,context)
        return deferred
        """
        return AgentOutlookMailView(self.ini_dict)

    def defMailCrawl(self,mail_collection,context):
        """here the returned collection is forwared to the page
        that is displaying it"""     
        return AgentOutlookMailView(self.ini_dict,mail_collection)

    def defMailCrawlError(self,ErrorMessage,context):
        """handles errors that ocurred in the MailCrawler"""
        return AgentHome(self.ini_dict)

    # "job overview" methods (class JobOverView)

    def child_ViewJobDetails(self,context):

        selected_job = ((IRequest(context).uri).split("?"))[1]
        file_pointer = open(JOBFILE,"r")
        job_details = ""
        job_list = file_pointer.readlines()
        for line in job_list:
            if line.startswith(selected_job):
                job_details = line
                break
        file_pointer.close()
        job_details = job_details.split(";")
        return JobOverViewDetails(self.ini_dict, job_details)

    # rendering methods of Startpage

    def render_getActiveUserMode(self,context,data):
        return self.ini_dict["UserMode"]

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

    docFactory = template('joblisting.html')

    def __init__(self, ini_dict):

        self.ini_settings = ini_dict

    # rendering methods of job overview
    
    def data_displayViewForm(self,context,data):
        return "Overview of all running Crawling jobs"

    def render_getActiveUserMode(self,context,data):
        return self.ini_settings["UserMode"]

    def render_fillJobTable(self,ctx,data):

        #---- get the registered jobs from the jobfile ----
        # might later be implemented by reading in a xml file or
        # requesting registered jobs from database
        file_jobfile = open(JOBFILE,"r")
        lines = file_jobfile.readlines()
        file_jobfile.close()
        joblist = []
        for elem in lines:
            joblist.append(elem.split(";"))         
        job_table = [tags.tr
                        [
                          tags.td
                             [
                               tags.a(href="ViewJobDetails?%s" %(job_details[0],))
                                  [
                                    tags.b
                                        [
                                            "[" + job_details[0] +"]"
                                        ]
                                  ]
                             ],
                          tags.td[job_details[1]],
                          tags.td[job_details[2]],
                          tags.td[job_details[3]],
                          tags.td[job_details[4]]
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

    docFactory = template('jobdetail.html')

    def __init__(self, ini_dict={}, selectedJob=[]):

        self.ini_settings = ini_dict
        self.jobdetails = selectedJob

    # rendering methods of job view details

    def data_displayViewForm(self,context,data):
        return "Detailed view of crawling job."

    def render_getActiveUserMode(self,context,data):
        return self.ini_settings["UserMode"]

    def render_displayJobDetails(self,ctx,data):

        print "*******************************************************"
        print "[render_displayJobDetails] received form: ", str(self.jobdetails)
        print "[render_displayJobDetails] received IniForm: ", str(self.ini_settings)
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

    docFactory = template('mail.html')

    def __init__(self, ini_dict={}, mail_collection=[]):

        self.ini_dict = ini_dict
        self.mail_collection = mail_collection

    # rendering methods of Collect Outlook Mails

    def data_displayViewForm(self,context,data):
        return "Detailed view of all collected Outlook Mails. [DEMO]"

    def render_getActiveUserMode(self,context,data):
        return self.ini_dict["UserMode"]

    def render_displayOutlookMails(self,ctx,data):

        pattern_list = []
        gen_pattern = inevow.IQ(ctx).patternGenerator('OutlookMails')
        for elem in self.mail_collection:
            pattern_list.append(gen_pattern(data=elem))
        return pattern_list

    def render_footer_fragment(self,context,data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self,context,data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self,context,data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self,context,data):
        return context.tag[HeaderFragment(data)]
    
