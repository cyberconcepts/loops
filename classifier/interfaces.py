#
#  Copyright (c) 2007 Helmut Merz helmutm@cy55.de
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
Classifier interfaces.

$Id$
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.util import _


class IClassifier(Interface):
    """
    """

    providerName = schema.TextLine(
            title=_(u'Provider name'),
            description=_(u'The name of a utility that provides the '
                           'external objects; default is a directory '
                           'collection provider'),
            required=False)

