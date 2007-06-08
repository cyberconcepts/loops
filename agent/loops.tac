from twisted.application import internet, service
from nevow import appserver

from loops.agent.core import startAgent
from loops.agent.ui.web import AgentHome
from loops.agent.config import conf

port = conf.ui.web.port or 10095

application = service.Application('LoopsAgent')

site = appserver.NevowSite(resource=AgentHome(startAgent()))
webServer = internet.TCPServer(port, site)
webServer.setServiceParent(application)

