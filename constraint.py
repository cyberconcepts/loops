#
#  Copyright (c) 2004 Helmut Merz helmutm@cy55.de
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
Definition of the ResourceConstraint class.

$Id$
"""

from zope.interface import implements

from interfaces import IResourceConstraint


class ResourceConstraint(object):

    implements(IResourceConstraint)

    explanation = u''
    constraintType = 'require'
    referenceType = 'explicit'
    referenceKey = None


    def __init__(self):
        self.referenceValues = []


    def isResourceAllowed(self, resource, task=None):
        if self.referenceType == 'parent':
            for ref in self.referenceValues:
                m = getattr(ref, self.referenceKey)
                if resource in m():
                    return True
        elif self.referenceType == 'explicit':
            return resource in self.referenceValues
        elif self.referenceType == 'checkmethod':
            m = getattr(resource, self.referenceKey, None)
            if m:
                return m()
        elif self.referenceType == 'selectmethod':
            allowed = self.getAllowedResources(task=task)
            return allowed and resource in allowed or False
        return False


    def getAllowedResources(self, candidates=None, task=None):
        if self.referenceType == 'parent':
            result = []
            for ref in self.referenceValues:
                m = getattr(ref, self.referenceKey)
                result.extend(m())
            return tuple(result)
        elif self.referenceType == 'explicit':
            return tuple(self.referenceValues)
        elif self.referenceType == 'selectmethod':
            m = getattr(self, self.referenceKey)
            return m(candidates, task)
        else:
            if candidates is None:
                return None
            else:
                return tuple([ r for r in candidates if self.isResourceAllowed(r, task) ])

