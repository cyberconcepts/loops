#Boa:Frame:ShowWindows

# Author     : Tim Couper - tim@tizmoi.net
# Date       : 1 August 2004
# Copyright  : Copyright TAC Software Ltd, under Python-like licence.
#              Provided as-is, with no warranty.
# Notes      : Requires watsup, wxPython

from wxPython.wx import *
from wxPython.lib.anchors import LayoutAnchors

from watsup.tools.showWindows import findAll,findNew,readPickle
from watsup.winGuiAuto import dumpWindow
from watsup.utils import tupleHwnd
import pprint

def create(parent):
    return ShowWindows(parent)

[wxID_SHOWWINDOWS, wxID_SHOWWINDOWSFINDNEW, wxID_SHOWWINDOWSNEWWINDOWS, 
 wxID_SHOWWINDOWSPANEL1, wxID_SHOWWINDOWSREGISTER, wxID_SHOWWINDOWSREGISTERED, 
 wxID_SHOWWINDOWSTEXT, 
] = map(lambda _init_ctrls: wxNewId(), range(7))

class ShowWindows(wxFrame):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wxFrame.__init__(self, id=wxID_SHOWWINDOWS, name='ShowWindows',
              parent=prnt, pos=wxPoint(424, 184), size=wxSize(456, 433),
              style=wxMINIMIZE_BOX | wxSTATIC_BORDER | wxCAPTION | wxSYSTEM_MENU,
              title='ShowWindows 1.0')
        self.SetClientSize(wxSize(448, 399))
        self.SetToolTipString('ShowWindow')
        self.Center(wxBOTH)
        self.Enable(True)
        self.SetSizeHints(-1, -1, -1, -1)
        self.SetThemeEnabled(False)

        self.panel1 = wxPanel(id=wxID_SHOWWINDOWSPANEL1, name='panel1',
              parent=self, pos=wxPoint(0, 350), size=wxSize(450, 50),
              style=wxTAB_TRAVERSAL)
        self.panel1.SetConstraints(LayoutAnchors(self.panel1, True, True, False,
              False))

        self.Register = wxButton(id=wxID_SHOWWINDOWSREGISTER, label='Register',
              name='Register', parent=self.panel1, pos=wxPoint(32, 13),
              size=wxSize(75, 23), style=0)
        self.Register.SetToolTipString('Register all windows info')
        EVT_BUTTON(self.Register, wxID_SHOWWINDOWSREGISTER,
              self.OnRegisterButton)

        self.FindNew = wxButton(id=wxID_SHOWWINDOWSFINDNEW, label='Find New',
              name='FindNew', parent=self.panel1, pos=wxPoint(304, 13),
              size=wxSize(75, 23), style=0)
        EVT_BUTTON(self.FindNew, wxID_SHOWWINDOWSFINDNEW, self.OnFindNewButton)

        self.Text = wxTextCtrl(id=wxID_SHOWWINDOWSTEXT, name='Text',
              parent=self, pos=wxPoint(0, 0), size=wxSize(450, 350),
              style=wxRAISED_BORDER | wxTE_WORDWRAP | wxTE_MULTILINE, value='')

        self.Registered = wxTextCtrl(id=wxID_SHOWWINDOWSREGISTERED,
              name='Registered', parent=self.panel1, pos=wxPoint(110, 16),
              size=wxSize(40, 16), style=wxTE_CENTER | wxTE_READONLY, value='')
        self.Registered.SetToolTipString('No of windows registered on system')
        self.Registered.SetBackgroundColour(wxColour(175, 175, 175))

        self.NewWindows = wxTextCtrl(id=wxID_SHOWWINDOWSNEWWINDOWS,
              name='NewWindows', parent=self.panel1, pos=wxPoint(382, 16),
              size=wxSize(40, 16), style=wxTE_CENTER | wxTE_READONLY, value='')
        self.NewWindows.SetToolTipString('No of new windows found')
        self.NewWindows.SetBackgroundColour(wxColour(175, 175, 175))

    def __init__(self, parent):
        self._init_ctrls(parent)
        #load up the last value for your info
        ws=readPickle()
        if ws:
            self.Registered.SetValue(str(len(ws)))
            
    def OnRegisterButton(self, event):
        ws=findAll()
        self.Registered.SetBackgroundColour(wxColour(255, 255, 255))
        self.Registered.SetValue(str(len(ws)))

    def OnFindNewButton(self, event):
        ws=findNew()
        self.NewWindows.SetBackgroundColour(wxColour(255, 255, 255))        
        # write the details to the text box
        withControls=self.writeNewWindows(ws)
        self.NewWindows.SetValue('%s/%d' % (withControls,len(ws)))
        
    def writeNewWindows(self,ws):
        noControls=0
        withControls=0
        txt=[]
        for w in ws:
           
            dw=dumpWindow(w) 
            if not dw: 
                noControls+=1
                continue
                     
            t=tupleHwnd(w)
            # don't bother with ShowWindows application:    
                
            wclass=t[2]
            wtext=t[1]
            if  wclass=='wxWindowClass' and wtext.startswith('ShowWindows'):
                noControls+=1
                continue
                      
            if wtext:
                wtext="%s" % wtext
            else:
                wtext='' 
                
            withControls+=1   
            # write the heading window
            #txt.append('%d. %s %s' % (withControls,wclass,wtext))                
            txt.append('%d. %s' % (withControls,str(list(t))))
            txt.append(pprint.pformat(dw))
            txt.append('')
                 
        self.Text.SetValue('\n'.join(txt))
        
        return withControls
     
