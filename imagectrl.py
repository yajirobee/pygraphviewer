#! /usr/bin/env python

import os, sys, wx, wx.aui
from wx.lib.pubsub import pub
from wx.lib.splitter import MultiSplitterWindow
from eventconst import PT

class ImageBitmap(wx.StaticBitmap):
    class ImagePanelMenu(wx.Menu):
        def __init__(self, parent):
            wx.Menu.__init__(self)
            self.parent = parent

            deleteitem = self.Append(-1, "Delete panel")
            deleterowitem = self.Append(-1, "Delete Row")

            self.Bind(wx.EVT_MENU, self.OnDelete, deleteitem)
            self.Bind(wx.EVT_MENU, self.OnDeleteRow, deleterowitem)

        def OnDelete(self, evt):
            self.parent.scheduler.DeleteChild(self.parent)

        def OnDeleteRow(self, evt):
            self.parent.scheduler.DeleteChild(self.parent.GetParent())

    def __init__(self, parent, scheduler):
        wx.StaticBitmap.__init__(self, parent)
        self.scheduler = scheduler
        self.imgpath = None
        self.img = None
        self.keepratio = False
        self.Bind(wx.EVT_LEFT_DOWN, scheduler.OnSetSelection)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        pub.subscribe(self.OnSize, PT.TPC_SIZE)
        pub.subscribe(self.SetKeepratio, PT.TPC_KEEPRATIO)

    def Destroy(self):
        pub.unsubscribe(self.OnSize, PT.TPC_SIZE)
        pub.unsubscribe(self.SetKeepratio, PT.TPC_KEEPRATIO)
        wx.StaticBitmap.Destroy(self)

    def SetImage(self, path):
        self.imgpath = path
        self.img = wx.Image(path)
        self.FitPanel()

    def SetKeepratio(self, keepratio):
        self.keepratio = keepratio
        self.FitPanel()

    def OnSize(self, evt = None):
        self.FitPanel()

    def GetParentSize(self):
        parent = self.GetParent()
        idx = parent._windows.index(self)
        width = parent.GetSashPosition(idx)
        height = parent.GetSize()[1]
        return width, height

    def FitPanel(self):
        if self.img: self.FitImage()
        self.SetSize(self.GetParentSize())
        pub.sendMessage(PT.TPC_IMG_SIZE_CHANGED, id = self.GetId())

    def FitImage(self):
        quality = wx.IMAGE_QUALITY_NORMAL
        #quality = wx.IMAGE_QUALITY_HIGH
        mapw, maph = self.GetParentSize()
        imgw, imgh = self.img.GetWidth(), self.img.GetHeight()
        if self.keepratio:
            mapratio = float(mapw) / maph
            imgratio = float(imgw) / imgh
            if mapratio <= imgratio: rate = float(mapw) / imgw
            else: rate = float(maph) / imgh
            width = int(imgw * rate)
            height = int(imgh * rate)
            img = self.img.Scale(width, height, quality)
        else:
            img = self.img.Scale(mapw, maph, quality)
        self.SetBitmap(img.ConvertToBitmap())

    def OnRightClick(self, evt):
        menu = self.ImagePanelMenu(self)
        self.PopupMenu(menu)
        menu.Destroy()

class ImgSchedulerPanel(wx.Panel):
    borderwidth = 6

    def __init__(self, parent, size = (760, 570)):
        wx.Panel.__init__(self, parent, size = size)

        self.vsplitter = vsplitter = MultiSplitterWindow(self, size = (720, 540),
                                                         style = wx.SP_LIVE_UPDATE)
        vsplitter.SetOrientation(wx.VERTICAL)
        hsplitter = MultiSplitterWindow(self.vsplitter, style = wx.SP_LIVE_UPDATE)
        hsplitter.SetOrientation(wx.HORIZONTAL)
        vsplitter.AppendWindow(hsplitter, self.GetSize()[1])
        imgmap = ImageBitmap(hsplitter, self)
        hsplitter.AppendWindow(imgmap, vsplitter.GetSize()[0])
        self.selectedpanel = imgmap
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnChanging)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnChanged)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def GetSelection(self):
        return self.selectedpanel

    def SetSelection(self, selection):
        self.selectedpanel = selection
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

    def OnSetSelection(self, evt):
        self.SetSelection(evt.GetEventObject())

    def AddChild(self, splitter, child):
        length = sum(splitter._sashes)
        oldratio = [v / float(length) for v in splitter._sashes]
        oldnwin = len(oldratio)
        splitter.AppendWindow(child)
        splitter.SizeWindows()
        length -= self.borderwidth
        lenforold = int(length * oldnwin / (oldnwin + 1.))
        for i, r in enumerate(oldratio):
            splitter.SetSashPosition(i, int(lenforold * r))
            splitter.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def AddVertical(self):
        hsplitter = MultiSplitterWindow(self.vsplitter, style = wx.SP_LIVE_UPDATE)
        hsplitter.SetOrientation(wx.HORIZONTAL)
        imgmap = ImageBitmap(hsplitter, self)
        hsplitter.AppendWindow(imgmap, self.vsplitter.GetSize()[0])
        self.AddChild(self.vsplitter, hsplitter)

    def AddHorizontal(self):
        hsplitter = self.GetSelection().GetParent()
        imgmap = ImageBitmap(hsplitter, self)
        self.AddChild(hsplitter, imgmap)

    def DeleteChild(self, child):
        if len(child.GetParent()._windows) == 1: return
        parent = child.GetParent()
        length = sum(parent._sashes)
        idx = parent._windows.index(child)
        newwins = parent._sashes[:]
        newwins.pop(idx)
        l = sum(newwins) + self.borderwidth
        newratio = [v / float(l) for v in newwins]
        parent.DetachWindow(child)
        self.SetSelection(None)
        if isinstance(child, MultiSplitterWindow):
            for gchild in child._windows:
                gchild.Destroy()
        child.Destroy()
        for i, r in enumerate(newratio):
            parent.SetSashPosition(i, int(length * r))
            parent.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def OnChanging(self, evt):
        eobj = evt.GetEventObject()
        pos = evt.GetSashPosition()
        if eobj.GetOrientation() == wx.HORIZONTAL:
            print "horizontal", pos
            #eobj.SetSize((evt.GetSashPosition(), eobj.GetSize()[1]))
        else:
            print "vertical", pos
            #eobj.SetSize((eobj.GetSize()[0], evt.GetSashPosition()))
        print eobj._sashes

    def OnChanged(self, evt):
        if evt.GetId() == self.vsplitter.GetId():
            win = self.vsplitter.GetWindow(evt.GetSashIdx())
            win.SetSize((win.GetSize()[0], evt.GetSashPosition()))
            win.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def OnSize(self, evt):
        ratiodict = {}
        for win in [self.vsplitter] + self.vsplitter._windows:
            length = float(sum(win._sashes))
            ratio = [v / length for v in win._sashes]
            ratiodict[win.GetId()] = ratio
        self.vsplitter.SetSize(self.GetSize())
        ratio = ratiodict[self.vsplitter.GetId()]
        length = self.GetSize()[1] - self.borderwidth * (len(ratio) - 1)
        for i, r in enumerate(ratio):
            self.vsplitter.SetSashPosition(i, int(length * r))
        length = self.GetSize()[0]
        for win in self.vsplitter._windows:
            ratio = ratiodict[win.GetId()]
            l = length - self.borderwidth * (len(ratio) - 1)
            for i, r in enumerate(ratio):
                win.SetSashPosition(i, int(length * r))

class ImageNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, size = (800, 600)):
        wx.aui.AuiNotebook.__init__(self, parent, size = size)
        self.ntab = 0
        self.AddTab()
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        pub.subscribe(self.AddTab, PT.TPC_ADDTAB)
        pub.subscribe(self.SetImage, PT.TPC_SRCTREE_SEL_CHANGED)
        pub.subscribe(self.SplitVertical, PT.TPC_SPLIT_VERTICAL)
        pub.subscribe(self.SplitHorizontal, PT.TPC_SPLIT_HORIZONTAL)

    def AddTab(self):
        self.ntab += 1
        self.AddPage(ImgSchedulerPanel(self), "tab{0}".format(self.ntab), True)

    def GetActivePage(self):
        activeidx = self.GetSelection()
        if activeidx != -1: return self.GetPage(activeidx)
        else: return None

    def SetImage(self, path):
        activepage = self.GetActivePage()
        if activepage:
            selection = activepage.GetSelection()
            if selection:
                selection.SetImage(path)
                pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

    def SplitVertical(self):
        activepage = self.GetActivePage()
        if activepage: activepage.AddVertical()

    def SplitHorizontal(self):
        activepage = self.GetActivePage()
        if activepage: activepage.AddHorizontal()

    def OnPageChanged(self, evt):
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)
