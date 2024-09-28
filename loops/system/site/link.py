# loops.system.site.link

""" Interfaces for linking to other pages on a portal page.
"""

from zope.interface import implementer
from zope import interface, component, schema

from loops.common import AdapterBase
from loops.system.site.interfaces import ILink
from loops.type import TypeInterfaceSourceList
from loops.util import _


TypeInterfaceSourceList.typeInterfaces += (ILink,)


@implementer(ILink)
class Link(AdapterBase):

    _contextAttributes = list(ILink)
