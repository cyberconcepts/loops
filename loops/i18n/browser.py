#
#  Copyright (c) 2015 Helmut Merz helmutm@cy55.de
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
"""

from datetime import date, datetime
from zope import interface, component
from zope.app.pagetemplate import ViewPageTemplateFile
from zope.app.session.interfaces import ISession
from zope.cachedescriptors.property import Lazy
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.negotiator import negotiator

from cybertools.meta.interfaces import IOptions
from cybertools.util import format
from loops.common import adapted


packageId = 'loops.i18n.browser'

i18n_macros = ViewPageTemplateFile('i18n_macros.pt')


class LanguageInfo(object):

    def __init__(self, context, request, allowDefault=True):
        self.context = context
        self.request = request
        self.allowDefault = allowDefault

    @Lazy
    def loopsRoot(self):
        return self.context.getLoopsRoot()

    @Lazy
    def availableLanguages(self):
        return IOptions(self.loopsRoot).languages

    @Lazy
    def defaultLanguage(self):
        langs = self.availableLanguages
        return langs and langs[0] or None

    @Lazy
    def language(self):
        available = self.availableLanguages or ('en', 'de')
        if len(available) == 1:
            return available[0]
        lang = self.request.get('loops.language')
        if lang is not None and lang in available:
            return lang
        session = ISession(self.request)[packageId]
        lang = session.get('language')
        if lang is not None and lang in available:
            return lang
        return (negotiator.getLanguage(available, self.request)
                or self.defaultLanguage)


class I18NView(object):
    """ View mix-in class.
    """

    timeStampFormat = 'short'

    @Lazy
    def languageInfo(self):
        return LanguageInfo(self.context, self.request)

    @Lazy
    def languageInfoForUpdate(self):
        return LanguageInfo(self.context, self.request, False)

    @Lazy
    def useI18NForEditing(self):
        return (self.languageInfo.availableLanguages
            and getattr(self.adapted, 'i18nAttributes', None))

    @Lazy
    def adapted(self):
        return adapted(self.context, self.languageInfo)

    def checkLanguage(self):
        #session = ISession(self.request)[packageId]
        #lang = session.get('language') or self.languageInfo.language
        lang = self.languageInfo.language
        if lang:
            self.setLanguage(lang)

    def setLanguage(self, lang=None):
        lang = lang or self.request.form.get('lang')
        if lang and lang in self.languageInfo.availableLanguages:
            upl = IUserPreferredLanguages(self.request)
            upl.setPreferredLanguages([lang])

    def switchLanguage(self):
        lang = self.request.form.get('loops.language')
        keep = self.request.form.get('keep')
        if keep:
            session = ISession(self.request)[packageId]
            session['language'] = lang
        self.setLanguage(lang)
        return self()

    def formatTimeStamp(self, ts, f='dateTime'):
        if not ts:
            return u''
        value = datetime.fromtimestamp(ts)
        return format.formatDate(value, f, self.timeStampFormat,
                                 self.languageInfo.language)

