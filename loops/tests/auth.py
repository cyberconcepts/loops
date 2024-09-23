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
Elements helpful for testing with authenticated users.

$Id$
"""


from zope.cachedescriptors.property import Lazy
from zope.publisher.browser import TestRequest as BaseTestRequest
from zope.security.management import getInteraction, newInteraction, endInteraction


class Participation(object):
    """ Dummy Participation class for testing.
    """

    interaction = None

    def __init__(self, principal):
        self.principal = principal


class TestRequest(BaseTestRequest):

    basePrincipal = BaseTestRequest.principal

    @Lazy
    def principal(self):
        interaction = getInteraction()
        if interaction is not None:
            parts = interaction.participations
            if parts:
                prin = parts[0].principal
                if prin is not None:
                    return prin
        return self.basePrincipal


def login(principal):
    endInteraction()
    newInteraction(Participation(principal))

