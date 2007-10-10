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
Standard implementations of classifier components.

$Id$
"""

import re

from zope.cachedescriptors.property import Lazy
from zope.component import adapts

from loops.classifier.base import Analyzer, Extractor
from loops.classifier.base import InformationSet
from loops.classifier.base import Statement
from loops.interfaces import IExternalFile
from loops.query import ConceptQuery


class FilenameExtractor(Extractor):

    adapts(IExternalFile)

    def __init__(self, context):
        self.context = context

    def extractInformationSet(self):
        filename = self.context.externalAddress
        return InformationSet(filename=filename)


class PathExtractor(Extractor):

    adapts(IExternalFile)

    def __init__(self, context):
        self.context = context

    def extractInformationSet(self):
        params = self.context.storageParams
        if 'subdir' in params:
            return InformationSet(path=params['subdir'])
        else:
            return InformationSet()


class WordBasedAnalyzer(Analyzer):

    @Lazy
    def query(self):
        return ConceptQuery(self.context)

    def extractStatements(self, informationSet):
        result = []
        for key, value in informationSet.items():
            words = self.split(value)
            for w in words:
                result.extend([Statement(c) for c in self.findConcepts(w)])
        return result

    def split(self, text):
        return re.split('\W+', text)

    def findConcepts(self, word):
        return self.query.query(word, 'loops:concept:*')

