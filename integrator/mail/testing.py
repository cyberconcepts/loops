#
#  Copyright (c) 2009 Helmut Merz helmutm@cy55.de
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
Fake access to system libraries for testing.

$Id$
"""

data = [('1 (RFC822 {7785}', 'Return-Path: <ceo-bounces@mailman.cy55.de>\r\nMessage-ID: <20081208171745.e4ce2xm96cco80cg@cy55.de>\r\nDate: Mon,  8 Dec 2008 17:17:45 +0100\r\nFrom: ceo@cy55.de\r\nTo: ceo@example.org\r\n\r\nThis message is in MIME format.\r\n\r\n--===============0371775080==\r\nContent-Type: multipart/alternative;\r\n\tboundary="=_gtkn1bgzg6g"\r\nContent-Transfer-Encoding: 7bit\r\n\r\nThis message is in MIME format.\r\n\r\n--=_gtkn1bgzg6g\r\nContent-Type: text/plain;\r\n\tcharset=ISO-8859-1;\r\n\tDelSp="Yes";\r\n\tformat="flowed"\r\nContent-Description: Plaintext Version of Message\r\nContent-Disposition: inline\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n\r\n\r\n   BLOGGING FROM ...\r\n.\r\n\r\n\r\n--=_gtkn1bgzg6g\r\nContent-Type: text/html;\r\n\tcharset=ISO-8859-1\r\nContent-Description: HTML Version of Message\r\nContent-Disposition: inline\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n<p><b>Blogging from ...</b><br />\r\n\r\n'), ')']


class IMAP4(object):

    def __init__(self, host=None):
        pass

    def login(self, user, password):
        pass

    def select(self, mailbox):
        return 1

    def search(self, charset, criterion):
        return 'OK', ['1']

    def fetch(self, idx, parts):
        return 'OK', data


from loops.integrator.mail import system
system.IMAP4 = IMAP4
