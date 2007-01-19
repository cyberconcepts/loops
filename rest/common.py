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
Common stuff for REST (REpresentational State Transfer) views.

$Id$
"""

from zope.interface import implements
from zope.component import adapts
from zope.publisher.interfaces.browser import IBrowserRequest, IBrowserPublisher

from loops.interfaces import IConcept

# interfaces

class IRESTView(IBrowserPublisher):
    """ The basic interface for all REST views.
    """

    def __call__():
        """ Render the representation.
        """


class ConceptView(object):
    """ A REST view for a concept.
    """

    implements(IRESTView)
    adapts(IConcept, IBrowserRequest)

    def __init__(self, context, request):
        self.context = self.__parent__ = context
        self.request = request

    def __call__(self):
        return 'Hello REST'

    def browserDefault(self, request):
        """ Make the publisher happy.
        """
        return self, ()
