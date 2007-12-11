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
View extension for support of i18n content.

$Id$
"""

from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.negotiator import negotiator

from loops.common import adapted


class LanguageInfo(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def availableLanguages(self):
        for opt in self.loopsRoot.options:
            if opt.startswith('languages:'):
                return opt[len('languages:'):].split(',')
        return []

    @Lazy
    def defaultLanguage(self):
        langs = self.availableLanguages
        return langs and langs[0] or None

    @Lazy
    def language(self):
        lang = self.request.get('loops.language')
        if lang is not None and lang in self.availableLanguages:
            return lang
        return (negotiator.getLanguage(self.availableLanguages, self.request)
                or self.defaultLanguage)


class I18NView(object):
    """ View mix-in class.
    """

    @Lazy
    def languageInfo(self):
        return LanguageInfo(self.context, self.request)

    @Lazy
    def useI18N(self):
        return (self.languageInfo.availableLanguages
            and getattr(self.adapted, 'i18nAttributes', None))

    @Lazy
    def adapted(self):
        return adapted(self.context, self.languageInfo)

    def checkLanguage(self):
        # get language from session
        self.setPreferredLanguage()

    def setLanguage(self, lang=None):
        lang = lang or self.request.form.get('lang')
        if lang:
            upl = IUserPreferredLanguages(self.request)
            upl.setPreferredLanguages([lang])

    def switchLanguage(self, lang=None, keep=False):
        keep = self.request.form.get('keep')
        if keep:
            pass # set in session
        self.setPreferredLanguage(lang)
        return self()

