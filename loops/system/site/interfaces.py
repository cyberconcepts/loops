#
#  Copyright (c) 2010 Helmut Merz helmutm@cy55.de
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
Interfaces for linking to other pages on a portal page.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.interfaces import IConceptSchema
from loops.util import _


class ILink(IConceptSchema):
    """ A link to a page in another loops site in the same instance.
    """

    site = schema.TextLine(
        title=_(u'Site'),
        description=_(u'Path to the site to link to.'),
        default=u'',
        required=True)

    path = schema.TextLine(
        title=_(u'Path'),
        description=_(u'Path within the view manager. Default: home'),
        default=u'home',
        required=False)

    url = schema.TextLine(
        title=_(u'URL'),
        description=_(u'URL to use for the link. Default: '
                    u'generate from site and path settings.'),
        default=u'',
        required=False)

