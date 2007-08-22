#------------------------------------------------------
# AgentHome.py
# source file for agent UI
# author: Juergen Menzinger
# version: 0.1
#------------------------------------------------------

import sys
import os
import tempfile
import cPickle
import traceback
import time
import email

from nevow import loaders, rend, static, url, inevow, tags
from nevow.inevow import IRequest
from twisted.internet import defer

from loops.agent.crawl import outlook
from loops.agent import core
from loops.agent.crawl.outlook import OutlookResource
from loops.agent.crawl.filesystem import FileResource

# ---- global definitions and settings ---------------------------------
os.environ['HOME'] = os.path.dirname(core.__file__)
OUTLOOK2000 = 1
PICKLE_MAILS = 0
DEBUG = 1
resourcesDirectory = 'resources'
templatesDirectory = 'templates'
#----------------------------------------------------------


def template(fn):
    return loaders.xmlfile(os.path.join(templatesDirectory, fn))

def getConfigIndex(agentobj, index_name, default_value, fn=None):
    """get the number of jobs currently in config file"""
    index = len(agentobj.config.crawl)
    return index


# AgentHome 
# root page of the Agent UI

class AgentHome(rend.Page):

    """Main class that builds the root ressource for the loops agent ui.

    Instance variables:
    usermode -- can be 'Simple' or 'Advanced'
    agent -- agent object where config and tempdir attributes can be accessed

    Class methods:
    At the moment all methods of this class except the __init__ although
    public, are intended to be called directly or stand-alone.

    __init__ -- Load the initial start-up settings from config

    """
    
    child_resources = static.File(resourcesDirectory)
    docFactory = template('agent.html')
    
    def __init__(self, agent=None, first_start=1):
        """ Initialize the AgentHome object.

        If first_start = 1 then the initalization procedure is run, which
        mainly loads the stored settings from the agent ini-file into instance
        variables of the class.

        Keyword arguments:
        first_start -- defaults to 1

        """
        print "[PAGECLASS] AgentHome"
        if first_start == 1:
            self.agent = core.Agent()
            self.usermode = self.agent.config.ui.web.setdefault('usermode', 'Simple')
            print "[AgentHome] setting self.usermode: ", self.agent.config.ui.web.usermode
        else:
            self.agent = agent
        
    """
    def locateChild(self, ctx, segments):
        return self, ()
    """
    
    # calls to child pages
    
    def child_joboverview(self, context):
        """ User requested page from menue: 'job overview' """
        return JobOverView(self.agent)

    def child_collectOutlookMails(self, context):
        """Display page for starting Outlook Crawler"""
        return AgentOutlookMailCrawl(self.agent)

    def child_collectFilesystem(self, context):
        """Display page for starting Filesystem Crawler"""
        return AgentFilesystemCrawl(self.agent)

    def child_viewRessources(self, context):
        """Display page that shows all currently collected Outlook Mails."""
        return RessourceView(self.agent)

    # "Startpage" methods (class AgentHome)

    def child_changeUserMode(self, context):
        """Change user mode.

        User has klicked the Change User Mode button, so
        change UserMode from Simple <-> Professional

        """
        if DEBUG:
            print "[child_changeUserMode] UserMode: ", self.agent.config.ui.web.usermode
        form = IRequest(context).args
        if form != {}:
            for elem in form:
                print "[child_changeUserMode] ", form[elem]
        if self.agent.config.ui.web.usermode == "Simple":
            self.agent.config.ui.web.usermode = "Advanced"
        else:
            self.agent.config.ui.web.usermode = "Simple"
        self.agent.config.save()
        if DEBUG:
            print "====> changed UserMode: ", self.agent.config.ui.web.usermode
        return AgentHome(self.agent, first_start=0)

    # "job overview" methods (class JobOverView)

    def child_ViewJobDetails(self, context):
        """Get details for the selected job.

        Reads all information about the selected job from file/ database.
        Returns page object which displays the available information.

        """
        selected_job = ((IRequest(context).uri).split("?"))[1]
        crawl_index = selected_job.split(".")[1]
        
        return JobOverViewDetails(self.agent, crawl_index)

    # "add outlook crawl job" methods (class AgentOutlookMailCrawl)

    def child_submitOutlookCrawlJob(self,context):
        """Initiate Outlook crawling job as requested by user."""
        ag = self.agent
        conf = ag.config
        crawlSubfolder = False
        form = IRequest(context).args
        if form != {}:
            index = getConfigIndex(self.agent, 'type', 'unused')     
            #save job configuration
            if form['mailCrawlInterval'][0] == "oneTime":
                conf.crawl[index].state = 'completed'
            else:
                conf.crawl[index].state = 'active'   
            conf.crawl[index].jobid = 'outlook.%i' %(index)
            conf.crawl[index].type = 'OutlookMail'
            if form.has_key('inbox'):
                conf.crawl[index].getinbox = '%s'%(str(form["inbox"][0]))
            else:
                conf.crawl[index].getinbox = 'False'
            if form.has_key('subfolders'):
                 conf.crawl[index].getsubfolder = '%s'%(str(form["subfolders"][0]))
            else:
                conf.crawl[index].getsubfolder = 'False'
            conf.crawl[index].subfolderpat = '%s'%(str(form["pattern"][0]))
            conf.crawl[index].latest = '%i'%(index)
            #TODO: how to find out what the most actual element is?
            conf.crawl[index].filter_criteria = '%s'%(form["selectFilterCriteria"][0])
            conf.crawl[index].filter_pattern =  '%s'%(form["filterPattern"][0])
            conf.crawl[index].content_format =  '%s'%(form["selectContentFormat"][0])
            conf.crawl[index].include_attachements = '%s'%(form["selectAttachements"][0])
            conf.crawl[index].interval = '%s'%(form["mailCrawlInterval"][0])
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
                # all form fileds in the html template are named according to
                # the dictionary name if expected to be in params,
                # this way it is not necessary to alter the code if another
                # parameter is added
                params = {}
                for elem in form.items():
                    params[elem[0]] = elem[1][0]
                outlook_job = outlook.CrawlingJob()
                outlook_job.params = params
                deferred = outlook_job.collect()
                deferred.addCallback(self.defMailCrawl, index, params, context)
                deferred.addErrback(self.defMailCrawlError,context)
                return deferred
            else:
                #TODO implement forwarding to next form (scheduler)
                return AgentOutlookMailCrawl(self.agent, "Scheduled Mail Crawling not implemented yet.") 
                
        else:
            return AgentOutlookMailCrawl(self.agent, "An error occurred: form data has been empty.")                  
        return AgentOutlookMailCrawl(self.agent, "Crawl Job settings have been saved.")
        
    def defMailCrawl(self, mail_collection, index, params, context):
        """Save and Forward the mail collection to a page view."""
        if DEBUG:
            print "====> seting and saving mails to disk"
            print "====> agent base dir: ",self.agent.tempdir      
        tmpdir =  tempfile.mkdtemp(prefix='mailJob_%i_'%(index), dir=self.agent.tempdir)
        if DEBUG:
            print "====> outlook job dir: ", tmpdir
        files = os.listdir(tmpdir)
        filenum = len(files)
        for elem in mail_collection:
            tmpfile = tempfile.mkstemp(prefix='%i_mail_'%(filenum), dir=tmpdir)
            if PICKLE_MAILS == 0:
                # write data as MIME string into a text file
                os.write(tmpfile[0], elem.data.as_string())
            else:
                # alternatively also writing the list as a whole might be
                # more performant (less disc I/O) but how to store the
                # path so that the user can have a look at the mail view
                # page and the page knows in which directory to look?
                # Idea could be a object that stores all current paths and
                # their crawlIDs
                os.write(tmpfile[0], cPickle.dumps(elem))
            os.close(tmpfile[0])  
            filenum = filenum + 1
        return RessourceView(self.agent, mail_collection, "The collected mails have been saved in %s"%(tmpdir), tmpdir)

    def defMailCrawlError(self, ErrorMessage, context):
        """Handles errors that ocurred in the MailCrawler."""
        #TODO: handle whole exception information
        return traceback.format_exc()

    # "view collected ressources" methods (class RessourceViewView)

    def child_viewRessourceDetails(self,context):
        """Get details for the selected ressource object.

        Reads all information about the selected ressource from file/ or the
        mail_collection list.
        Returns page object which displays the available information.

        """
        selected_item = ((IRequest(context).uri).split("?"))[1]   
        form = IRequest(context).args
        if form != {}:
            requested_file=""
            if DEBUG:
                print "[child_viewRessourceDetails]"
                print "====> selected item: ", selected_item
                print "====> printing items in directory"
            fileslist = os.listdir(form['ressourceObjData'][0])
            for elem in fileslist:
                if DEBUG:
                    print elem
                if elem.startswith(("%i_mail_"%(int(selected_item))), 0):
                    requested_file = elem
            requested_file = os.path.join(form['ressourceObjData'][0], requested_file)
            if requested_file.find("mail") > 0:        
                fp = open(requested_file, "rb")
                mail_parser = email.Parser.Parser()
                mailobj = OutlookResource(mail_parser.parse(fp))
                fp.close()
                mail = []
                for elem in mailobj.data.items():
                    if DEBUG:
                        print "====> building MIMEObject"
                        print "====> appending attribute: ", elem
                    mail.append(elem)
                if hasattr(mailobj.data, 'preamble'):
                    if DEBUG:
                        print "====> copying preamble contents"                    
                    mail.append(['Preamble', mailobj.data.preamble])
                else:
                    mail.append(['Preamble',''])
                if hasattr(mailobj.data,'epilogue'):
                    if DEBUG:
                        print "====> copying epilogue contents"
                    mail.append(['Epilogue', mailobj.data.epilogue])
                else:
                    mail.append(['Epilogue', ''])
                return OutlookMailDetail(agent=self.agent, pagemessage="", mail=mail, filename=requested_file)
            elif requested_file.find("file") > 0:
                #TODO implement file analyzing
                return FileObjectDetail(agent=self.agent, pagemessage="", fileobj=fileobj, filename=requested_file)            
        if os.path.isdir(selected_item):
            # selected item is a folder -> change to that folder
            if DEBUG:
                print "====> selected item is a directory! changing into directory"
            return RessourceView(self.agent, ressource_collection=[], pagemessage="changed to folder %s" %(selected_item), tmpdir=selected_item)
        elif os.path.isfile(selected_item):
            if selected_item.find("mail") > 0:
                fp = open(selected_item, "rb")
                mail_parser = email.Parser.Parser()
                mailobj = OutlookResource(mail_parser.parse(fp))
                fp.close()
                mail = []
                for elem in mailobj.data.items():
                    mail.append(elem)
                if hasattr(mailobj.data,'preamble'):
                    mail.append(['Preamble', mailobj.data.preamble])
                else:
                    mail.append(['Preamble',''])
                if hasattr(mailobj.data,'epilogue'):
                    mail.append(['Epilogue',mailobj.data.epilogue])
                else:
                    mail.append(['Epilogue',''])
                requested_file = selected_item
                return OutlookMailDetail(agent=self.agent, pagemessage="", mail=mail, filename=requested_file)
            elif selected_item.find("file") > 0:
                #TODO implement file analyzing
                return FileObjectDetail(agent=self.agent, pagemessage="", fileobj=fileobj, filename=requested_file)

    # rendering methods of Startpage

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_getAgentVersion(self, context, data):
        return "0.1 alpha"

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
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
    agent -- agent object where config and tempdir attributes can be accessed 

    Class methods:
    At the moment all methods of this class except the __init__
    although public, are intended to be called directly or stand-alone.

    __init__ -- Store the initial settings retrieved from AgentHome.

    """
    
    docFactory = template('joblisting.html')

    def __init__(self, agent=None):
        print "[PAGECLASS] JobOverView"
        self.agent = agent

    # rendering methods of job overview
    
    def data_displayViewForm(self, context, data):
        return "Overview of all running Crawling jobs"

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_fillJobTable(self, ctx, data):
        """Build table which displays all registered jobs."""

        #---- get the registered jobs from the jobfile ----
        joblist = []
        index = 0
        self.agent.config.load()
        while index < len(self.agent.config.crawl):
            joblist.append(dict(self.agent.config.crawl[index].items()))
            index = index + 1
        job_table = []
        for job_details in joblist:
            if job_details['jobid'].split(".")[0] == "outlook":
                job_table.append(tags.tr
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
                                    tags.td["Inbox: %s, Subfolders: %s" %(job_details['getinbox'], job_details['getsubfolder'])]
                                  ]
                                 )
            elif job_details['jobid'].split(".")[0] == "filesystem":
                    job_table.append(tags.tr
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
                                    tags.td["directories"]
                                  ]
                                 )

        return job_table

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
        return context.tag[HeaderFragment(data)]


class JobOverViewDetails(rend.Page):
    
    """Builds page that displays detailed information about a selected job.

    Instance variables:
    jobdetails -- list that contains all available job information
    agent -- agent object where config and tempdir attributes can be accessed

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the selected job in member variable.

    """

    docFactory = template('jobdetail.html')

    def __init__(self, agent=None, selected_jobindex=None):
        print "[PAGECLASS] JobOverViewDetails"
        self.selected_index = selected_jobindex
        self.agent = agent

    # rendering methods of job view details

    def data_displayViewForm(self, context, data):
        return "Detailed view of crawling job."

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_displayJobDetails(self, ctx, data):
        """Build the table containing information about the selected job."""

        print "*******************************************************"
        print "[render_displayJobDetails] received form: ", str(self.selected_index)
        print "[render_displayJobDetails] usermode: ", self.agent.config.ui.web.usermode
        print "*******************************************************"

        if self.selected_index != None:        
            job_detailtable = [tags.tr
                                   [
                                     tags.td[tags.b[parameter[0]]],
                                     tags.td[parameter[1]]
                                    ]
                               for parameter in list(self.agent.config.crawl[int(self.selected_index)].items())
                              ]
        return job_detailtable

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
        return context.tag[HeaderFragment(data)]


class RessourceView(rend.Page):
    
    """Builds page that displays an overview of all collected mails.

    Instance variables:
    page_message -- string that is displayed on the page
    ressource_collection -- collection containing all currently collected ressources.
    temp_dir -- actual directory whose ressources have to be displayed
    agent -- the agent object which holds the config data and temp directory

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the mail collection object and the pagemessage

    """

    mail_collection = None
    docFactory = template('ressourceview.html')

    def __init__(self, agent=None, ressource_collection=[], pagemessage="", tmpdir=""):
        print "[PAGECLASS] RessourceView"
        self.ressource_collection = ressource_collection
        self.page_message = pagemessage
        self.temp_dir = tmpdir
        self.agent = agent

    # rendering methods of view collected ressources

    def data_displayViewForm(self, context, data):
        return "View of all collected ressources."

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_systemMessage(self, context, data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_displayRessourceHeaders(self, context, data):
        """Displays the column headings according to the ressource type"""
        #TODO: switch between different objecttypes
        if DEBUG:
            print "====> creating html columns for Ressource table"
        current_dir=""
        if self.temp_dir == "":
            current_dir = self.agent.tempdir
        else:
            current_dir = self.temp_dir
        if self.ressource_collection == []:
            files_found = 0
            for elem in os.listdir(current_dir):
                if os.path.isfile(os.path.join(current_dir,elem)):
                    files_found = 1
                    break
            if files_found == 0:
                if current_dir.find("mail"):
                    if DEBUG:
                        print "====> just mail subdirs in current directory"
                    return [tags.tr
                              [
                                tags.th["Directory Name"],
                                tags.th["Created"],
                                tags.th["Modified"],
                                tags.th["Mails inside"],
                               ]
                             ]
                elif current_dir.find("file"):
                    if DEBUG:
                        print "====> just file subdirs in current directory"
                    return [tags.tr
                              [
                                tags.th["Directory Name"],
                                tags.th["Created"],
                                tags.th["Modified"],
                                tags.th["Files inside"],
                               ]
                             ]
            if files_found >= 1:
                if current_dir.find("mail"):
                    if DEBUG:
                        print "====> current directory has mails"
                    return [tags.tr
                               [
                                   tags.th["From"],
                                   tags.th["CC"],
                                   tags.th["Subject"],
                                   tags.th["Recipient"],
                                   tags.th["Date"]
                                 ]
                              ]
                elif current_dir.find("file"):
                    if DEBUG:
                        print "====> current directory has files"
                    return [tags.tr
                               [
                                tags.th["Filename"],
                                tags.th["Filesize"],
                                tags.th["Date created"],
                                tags.th["Date modified"],
                                tags.th["Filetype"]
                              ]
                            ] 
        elif isinstance(self.ressource_collection[0], FileResource):
            if DEBUG:
                print "====> instance is a FileResource"
            return [tags.tr
                   [
                       tags.th["Filename"],
                       tags.th["Filesize"],
                       tags.th["Date created"],
                       tags.th["Date modified"],
                       tags.th["Filetype"]
                     ]
                  ] 
        elif isinstance(self.ressource_collection[0], OutlookResource):
            if DEBUG:
                print "====> instance is a OutlookResource"
            return [tags.tr
                   [
                       tags.th["From"],
                       tags.th["CC"],
                       tags.th["Subject"],
                       tags.th["Recipient"],
                       tags.th["Date"]
                     ]
                  ]              
        # raise exception here?
        return "could not find a matching object type"

    def render_displayRessources(self, ctx, data):
        """Builds table containing all currently collected ressources."""
        if self.ressource_collection != []:
            if DEBUG:
                print "====> building ressource with ressource_collection"
            index = 0
            ressource_table = []
            if isinstance(self.ressource_collection[0],OutlookResource):       
                for ressourceObject in self.ressource_collection:
                    ressource_table.append(tags.form(name="ressourceEntry%i"%(index), action="viewRessourceDetails?%i"%(index), method="POST")[
                                       tags.input(name="ressourceObjData", type="hidden", value="%s"%(self.temp_dir)),
                                       tags.tr[
                                       tags.td[
                                           tags.a(href="javascript:document.getElementsByName('ressourceEntry%i')[0].submit()"%(index))[
                                               tags.b[
                                                   "[" + str(ressourceObject.data.get('SenderName')) +"]"
                                                   ]
                                               ]
                                           ],
                                       tags.td[
                                           str(ressourceObject.data.get('CC'))
                                           ],
                                       tags.td[
                                           str(ressourceObject.data.get('Subject'))
                                           ],
                                       tags.td[
                                           #TODO: proper handling of unicode characters
                                           ressourceObject.data.get('To').encode('utf-8')
                                           ],
                                       tags.td['SourceFolder']]])
                    index = index + 1
                return ressource_table

            if isinstance(self.ressource_collection[0],FileResource):
                #TODO: implement building the table for file objects
                return ressource_table
        
        else:
            if DEBUG:
                print "====> building ressource by analyzing submitted dir"
            if self.temp_dir == "":
                current_dir = self.agent.tempdir
            else:
                current_dir = self.temp_dir
            ressource_files= os.listdir(current_dir)
            ressource_table = []
            #check whether there are directories, files or both in the actual directory
            for elem in ressource_files:
                element = os.path.join(current_dir,elem)
                if os.path.isdir(element):
                    files_in_subdir = len(os.listdir(element))
                    ressource_table.append(tags.tr
                                            [
                                             tags.td
                                              [
                                               tags.a(href="viewRessourceDetails?%s" %(element))
                                                  [
                                                   tags.b
                                                     [
                                                       "[" + str(elem) +"]"
                                                     ]
                                                   ]
                                                  ],
                                                  tags.td[time.asctime(time.localtime(os.path.getctime(element)))],
                                                  tags.td[time.asctime(time.localtime(os.path.getmtime(element)))],
                                                  tags.td[files_in_subdir]
                                                 ]
                                           )
                        
                elif os.path.isfile(element):
                    if elem.find("file") > 0:
                        if DEBUG:
                            print "====> %s is of type crawl file" %(elem)
                        ressource_table.append(tags.tr
                                                [
                                                 tags.td
                                                  [
                                                   tags.a(href="viewRessourceDetails?%s" %(element))
                                                      [
                                                       tags.b
                                                         [
                                                           "[" + str(elem) +"]"
                                                         ]
                                                       ]
                                                      ],
                                                      tags.td[os.path.getsize(element)],
                                                      tags.td[time.asctime(time.localtime(os.path.getctime(element)))],
                                                      tags.td[time.asctime(time.localtime(os.path.getmtime(element)))],
                                                      tags.td[str(elem.split(".")[-1])]
                                                ]
                                            )
                    elif elem.find("mail") > 0:
                        if DEBUG:
                            print "====> %s is of type mail" %(elem)
                        fp = open(element,"rb")
                        mail_parser = email.Parser.Parser()
                        mail = OutlookResource(mail_parser.parse(fp))
                        fp.close()
                        mail_from = mail.data.get('From', "not available")
                        mail_cc = mail.data.get('CC', "not available")
                        mail_subject = mail.data.get('Subject', "not available")
                        mail_recipient = mail.data.get('TO', "not available")
                        mail_date = mail.data.get('SENT', "not available")
                        ressource_table.append(tags.tr
                                                    [
                                                     tags.td
                                                      [
                                                       tags.a(href="viewRessourceDetails?%s" %(element))
                                                          [
                                                           tags.b
                                                             [
                                                               "[" + mail_from +"]"
                                                             ]
                                                           ]
                                                          ],
                                                          tags.td[mail_cc],
                                                          tags.td[mail_subject],
                                                          tags.td[mail_recipient],
                                                          tags.td[mail_date]
                                                    ]
                                                )
            return ressource_table

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
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

    def __init__(self, agent=None, pagemessage=""):
        print "[PAGECLASS] AgentOutlookMailCrawl"
        self.page_message = pagemessage
        self.agent  = agent

    # rendering methods of add outlook crawl job

    def data_displayViewForm(self, context, data):
        return "Configure your MailCrawl Job in the form below.\
                 You then can either choose to start it as a\
                 single job, or as scheduled job (further input\
                 for scheduler necessary). For each new collect\
                 procedure a filter will be added, so that just\
                 mails received in Outlook after the recent Crawl\
                 Job has been run, will be collected."

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_displayOutlookMails(self, ctx, data):
        """Currently no implementation"""
        return ""

    def render_systemMessage(self, context, data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
        return context.tag[HeaderFragment(data)]


class AgentFilesystemCrawl(rend.Page):
    
    """Builds page where an Filesystem Crawler can be configured and run.

    Instance variables:
    page_message -- string that is displayed on the page

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- store pagemessage in member variable

    """

    docFactory = template('filecrawl.html')

    def __init__(self, agent=None, pagemessage=""):
        print "[PAGECLASS] AgentFilesystemCrawl"
        self.page_message = pagemessage
        self.agent  = agent

    # rendering methods of ad filesystem crawl job

    def data_displayViewForm(self, context, data):
        return "Configure your FileCrawl Job in the form below.\
                 You then can either choose to start it as a\
                 single job, or as scheduled job (further input\
                 for scheduler necessary). For each new collect\
                 procedure a filter will be applied, so that just\
                 new objects will be collected."

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_displayFiles(self, ctx, data):
        """Currently no implementation"""
        return ""

    def render_systemMessage(self, context, data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
        return context.tag[HeaderFragment(data)]


class OutlookMailDetail(rend.Page):
    
    """Builds page that displays the selected mail in detail.

    Instance variables:
    page_message -- string that is displayed on the page
    mail_elements -- received mailobject as a list.
    agent -- agent object that holds the config data
    mail_file -- filename of the selected mail to view

    Class methods:
    At the moment all methods of this class except the __init__ although public,
    are intended to be called directly or stand-alone.

    __init__ -- Store the mail collection object and the pagemessage

    """
                            
    docFactory = template('mail_detailed.html')

    def __init__(self, agent=None, pagemessage="", mail=[], filename=""):
        print "[PAGECLASS] OutlookMailDetail"
        self.mail_elements = mail
        self.page_message = pagemessage
        self.agent = agent
        self.mail_file = filename

    # rendering methods of Collect Outlook Mails

    def data_displayViewForm(self, context, data):
        return (tags.b["Filename of the selected mail: "], tags.i[self.mail_file])

    def render_getActiveUserMode(self, context, data):
        return self.agent.config.ui.web.usermode

    def render_systemMessage(self, context, data):
        """Displays messages from the system to the user."""
        message = tags.b[self.page_message]
        return message

    def render_displayOutlookMail(self, ctx, data):
        """Builds the layout for the mail."""

        if self.mail_elements != []:
            mail_view = []
            for elem in self.mail_elements:
                mail_view.append(tags.tr[
                                  tags.td[elem[0]],
                                  tags.td[elem[1]]
                                 ]
                                )
            return mail_view
        
    def render_footer_fragment(self, context, data):
        return context.tag[FooterFragment(data)]

    def render_navigation_fragment(self, context, data):
        return context.tag[NavigationFragment(data)]

    def render_top_fragment(self, context, data):
        return context.tag[TopFragment(data)]

    def render_header_fragment(self, context, data):
        return context.tag[HeaderFragment(data)]
    
