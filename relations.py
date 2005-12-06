#
#  Copyright (c) 2005 Helmut Merz helmutm@cy55.de
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
Definition of relation classes.

$Id$
"""

from zope.app import zapi
from zope.interface import implements

from cybertools.relation import DyadicRelation


class ConceptRelation(DyadicRelation):
    """ A relation between concept objects.
    """


class ConceptResourceRelation(DyadicRelation):
    """ A relation between a concept and a resource object.
    """


class ViewConceptRelation(DyadicRelation):
    """ A relation between a view and a concept object.
    """


class ViewResourceRelation(DyadicRelation):
    """ A relation between a view and a resource object.
    """

