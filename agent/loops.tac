from twisted.application import internet, service
from nevow import appserver

from loops.agent.agent import startAgent
from loops.agent.ui.web import AgentHome

port = 10095

application = service.Application('LoopsAgent')

site = appserver.NevowSite(resource=AgentHome(startAgent()))
webServer = internet.TCPServer(port, site)
webServer.setServiceParent(application)

