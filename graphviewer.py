#! /usr/bin/env python

import sys, os, wx, wx.aui
from wx.lib.pubsub import pub
from eventconst import PT
from sourcetree import SourceTree
from imagectrl import ImageNotebook, ImageControlMenu

class MainMenuBar(wx.MenuBar):
    def __init__(self, RootFrame):
        self.RootFrame = RootFrame
        wx.MenuBar.__init__(self)

        filemenu = wx.Menu()
        openitem = wx.MenuItem(filemenu, -1, 'Open\tCtrl+O')
        quititem = wx.MenuItem(filemenu, -1, 'Quit\tCtrl+Q')
        filemenu.AppendItem(openitem)
        filemenu.AppendSeparator()
        filemenu.AppendItem(quititem)

        filemenu.Bind(wx.EVT_MENU, self.OnOpenDir, openitem)
        filemenu.Bind(wx.EVT_MENU, RootFrame.OnQuit, quititem)

        self.Append(filemenu, '&File')

    def OnOpenDir(self, evt):
        dlg = wx.DirDialog(self, "Choose a Directory", style = wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            pub.sendMessage(PT.TPC_OPENDIR, path = dlg.GetPath())
        dlg.Destroy()

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title,
                 pos = wx.DefaultPosition, size = (1280, 720),
                 style = wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self._mgr = wx.aui.AuiManager(self)

        # create controls
        self.srcview = srcview = SourceTree(self, size = (200, 400))
        self.imgnotebook = imgnotebook = ImageNotebook(self, size = (800, 600))

        # add the panes to the manger
        self._mgr.AddPane(srcview, wx.LEFT, "source view")
        self._mgr.AddPane(imgnotebook, wx.CENTER)

        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()

        # set menubar
        mainmenubar = MainMenuBar(self)
        mainmenubar.Append(imgnotebook.imgmenu, "&ImageView")
        self.SetMenuBar(mainmenubar)

        # set statusbar
        self.CreateStatusBar(2)
        self.OnPanelChanged()

        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        pub.subscribe(self.OnPanelChanged, PT.TPC_IMG_SEL_CHANGED)
        pub.subscribe(self.OnPanelSizeChanged, PT.TPC_IMG_SIZE_CHANGED)

        self.Show(True)

    def OnQuit(self, evt):
        self._mgr.UnInit()
        self.Destroy()

    def OnPanelChanged(self):
        activepage = self.imgnotebook.GetActivePage()
        if activepage: self.activepanel = activepage.GetSelection()
        else: self.activepanel = None
        if self.activepanel:
            parent = self.activepanel.GetParent()
            gparent = parent.GetParent()
            tabname = self.imgnotebook.GetPageText(self.imgnotebook.GetSelection())
            x = parent._windows.index(self.activepanel)
            y = gparent._windows.index(parent)
            imgpath = self.activepanel.imgpath if self.activepanel.imgpath else "Empty Image Panel"
            statusstr = "{0} ({1},{2}) {3}".format(tabname, x, y, imgpath)
        else: statusstr = "No panel choosen"
        self.SetStatusText(statusstr, 0)
        self.OnPanelSizeChanged(self.activepanel.GetId() if self.activepanel else None)

    def OnPanelSizeChanged(self, id):
        if self.activepanel and self.activepanel.GetId() == id:
            x, y = self.activepanel.GetSize()
            statusstr = "Window size : ({0}x{1})".format(x, y)
            bitmap = self.activepanel.GetBitmap()
            if bitmap != wx.NullBitmap:
                statusstr += " Image size : ({0}x{1})".format(bitmap.GetWidth(), bitmap.GetHeight())
            self.SetStatusText(statusstr, 1)
        elif self.activepanel == None and id == None:
            statusstr = ""
            self.SetStatusText(statusstr, 1)

if __name__ == "__main__":
    app = wx.App()
    MainFrame(None, -1, 'graphviewer')
    app.MainLoop()
