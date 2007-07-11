#-------------------------------------------------
# StartUpAgentUI.tac.py
# start the twisted webserver and initialize the
# nevow framework/application
# author: Juergen Menzinger
# version: 01.alpha
# start with twistd.py -noy StartUpAgentUI.tac.py
# requires AgentStart.html
#          AgentJobView.html
#          AgentJobViewDetail.html
#          AgentOutlookMailView.html
#-------------------------------------------------


from twisted.application import internet
from twisted.application import service
from nevow import appserver
import web
import sys, os, socket


application = service.Application('loops agent')
site = appserver.NevowSite(web.AgentHome())
webServer = internet.TCPServer(8080, site)
webServer.setServiceParent(application)

