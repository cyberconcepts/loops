#
#  Copyright (c) 2008 Helmut Merz helmutm@cy55.de
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
interface definitions for the loops.layout stuff.

$Id$
"""

from zope.app.container.constraints import contains, containers
from zope.interface import Interface

from loops.interfaces import INodeSchema, IBaseNode, INode, IViewManager


class ILayoutView(INodeSchema):
    """ Base interface for view nodes that use the cybertools.composer.layout
        presentation mechanism.
    """


class ILayoutNode(ILayoutView, INode):

    contains(ILayoutView)


class ILayoutNodeContained(Interface):

    containers(ILayoutNode, IViewManager)


