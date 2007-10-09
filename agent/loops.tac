"""
Start with ``twistd -noy loops/agent/loops.tac``.

$Id$
"""

from twisted.application import internet, service
from nevow import appserver

from loops.agent.core import Agent
from loops.agent.ui.web import AgentHome

agent = Agent()
conf = agent.config
port = conf.ui.web.port or 10095

application = service.Application('LoopsAgent')

site = appserver.NevowSite(resource=AgentHome(agent))
webServer = internet.TCPServer(port, site)
webServer.setServiceParent(application)

