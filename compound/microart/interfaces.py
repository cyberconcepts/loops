#
#  Copyright (c) 2011 Helmut Merz helmutm@cy55.de
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
Micro articles (MicroArt / MikroArtikel in German).
"""

from zope.interface import Interface, Attribute
from zope import interface, component, schema

from loops.compound.interfaces import ICompound
from loops.util import _


class HtmlField(schema.Text):

    __typeInfo__ = ('html',)


class IMicroArt(ICompound):
    """ A short article with a few elements, for collecting
        relevant information in a knowledge management environment.
    """

                        # title = Ueberschrift, Thema

    #story = HtmlField(        # Geschichte
    story = schema.Text(        # Geschichte
                title=_(u'Story'),
                description=_(u'The story, i.e. the main text of your '
                        u'micro article. Who did what? What happend?'),
                required=True)

    insight = schema.Text(      # Einsicht
                title=_(u'Insight'),
                description=_(u'What can we learn from the story? What '
                        u'has gone wrong? What was good?'),
                required=True)

    consequences = schema.Text( #(Schluss-) Folgerungen
                title=_(u'Consequences'),
                description=_(u'What we will do next time in a similar '
                        u'situation?'),
                required=True)

    followUps = schema.Text(    #Anschlussfragen
                title=_(u'Follow-up Questions'),
                description=_(u'Questions for helping to solve or avoid '
                        u'similar problems in the future.'),
                required=False)

# ideas, questions:
# could follow-up questions be associated to links to follow-up micro articles?
# re-use story for other MAs, e.g. insight and consequences drawn by others?
