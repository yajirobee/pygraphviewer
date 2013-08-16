#! /usr/bin/env python

import os, sys, wx, wx.aui
from wx.lib.pubsub import pub
from wx.lib.splitter import MultiSplitterWindow
from eventconst import PT

class ImageBitmap(wx.StaticBitmap):
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
        self.scheduler.SetSelection(evt.GetEventObject())
        self.PopupMenu(self.scheduler.GetParent().imgmenu)

class ImgMultiSplitter(MultiSplitterWindow):
    def __init__(self, parent, orientaion,
                 size = wx.DefaultSize, style = wx.SP_LIVE_UPDATE):
        MultiSplitterWindow.__init__(self, parent, size = size, style = style)
        self.SetOrientation(orientaion)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnChanging)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnChanged)

    def Destroy(self):
        for child in child._windows: child.Destroy()
        MultiSplitterWindow.Destroy(self)

    def CalcRatio(self, sashes):
        length = sum(sashes)
        return [v / float(length) for v in sashes]

    def AddWindow(self, window):
        oldratio = self.CalcRatio(self._sashes)
        oldnwin = len(oldratio)
        length = sum(self._sashes) - self._GetSashSize()
        lenfornew = int(length / (oldnwin + 1.))
        lenforold = length - lenfornew
        self.AppendWindow(window, lenfornew)
        for i, r in enumerate(oldratio): self.SetSashPosition(i, int(lenforold * r))
        self.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def DeleteWindow(self, window):
        if len(self._windows) == 1: return
        newsashes = self._sashes[:]
        newsashes.pop(self._windows.index(window))
        newratio = self.CalcRatio(newsashes)
        length = sum(self._sashes) + self._GetSashSize()
        self.SetSelection(None)
        self.DetachWindow(window)
        window.Destroy()
        for i, r in enumerate(newratio): self.SetSashPosition(i, int(length * r))
        self.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def FitParent(self):
        ratio = self.CalcRatio(self._sashes)
        parent = self.GetParent()
        if isinstance(parent, MultiSplitterWindow):
            if parent.GetOrientation() == wx.HORIZONTAL:
                size = (parent.GetSashPosition(parent._windows.index(self)),
                        parent.GetClientSize()[1])
            else:
                size = (parent.GetClientSize()[0],
                        parent.GetSashPosition(parent._windows.index(self)))
        else:
            size = parent.GetClientSize()
        self.SetSize(size)
        if self.GetOrientation() == wx.VERTICAL:
            length = self.GetSize()[1] - self._GetSashSize() * (len(ratio) - 1)
        else:
            length = self.GetSize()[0] - self._GetSashSize() * (len(ratio) - 1)
        for i, r in enumerate(ratio): self.SetSashPosition(i, int(length * r))

    def OnSize(self, evt):
        self.FitParent()

    def OnChanging(self, evt):
        limit = sum(self._sashes)
        idx = evt.GetSashIdx()
        oldpos = self.GetSashPosition(idx)
        newpos = evt.GetSashPosition()
        if 0 == newpos: newpos = 1
        print oldpos, newpos
        """
        if oldpos > newpos: # slide left or up
            targetsashpos = self.GetSashPosition(idx + 1)
            leftsashes = self._sashes[:idx + 1]
            ratio = self.CalcRatio(leftsashes)
            print "left", idx, ratio
            diff = oldpos - newpos
            newleftlen = sum(leftsashes) - diff
            for i, r in enumerate(ratio):
                self.SetSashPosition(i, int(newleftlen * r))
            self.SetSashPosition(idx + 1, targetsashpos + diff)
        else: # slide right or bottom
            targetsashpos = oldpos
            rightsashes = self._sashes[idx + 1:]
            ratio = self.CalcRatio(rightsashes)
            print "right", idx, ratio
            self.SetSashPosition(idx, newpos)
            diff = newpos - oldpos
            newrightlen = sum(rightsashes) - diff
            for i, r in enumerate(ratio):
                self.SetSashPosition(idx + 1 + i, int(newrightlen * r))
        self.SizeWindows()
        """

    def OnChanged(self, evt):
        pub.sendMessage(PT.TPC_SIZE)

class ImgSchedulerPanel(wx.Panel):
    def __init__(self, parent, size = (760, 570)):
        wx.Panel.__init__(self, parent, size = size)

        self.vsplitter = vsplitter = ImgMultiSplitter(self, wx.VERTICAL, size = (720, 540))
        hsplitter = ImgMultiSplitter(vsplitter, wx.HORIZONTAL)
        vsplitter.AppendWindow(hsplitter, self.GetSize()[1])
        imgmap = ImageBitmap(hsplitter, self)
        hsplitter.AppendWindow(imgmap, vsplitter.GetSize()[0])
        self.selectedpanel = imgmap
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def GetSelection(self):
        return self.selectedpanel

    def SetSelection(self, selection):
        self.selectedpanel = selection
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

    def OnSetSelection(self, evt):
        self.SetSelection(evt.GetEventObject())

    def AddVertical(self):
        hsplitter = ImgMultiSplitter(self.vsplitter, wx.HORIZONTAL)
        imgmap = ImageBitmap(hsplitter, self)
        hsplitter.AppendWindow(imgmap, self.vsplitter.GetSize()[0])
        self.vsplitter.AddWindow(hsplitter)

    def AddHorizontal(self):
        if not self.selectedpanel: return
        hsplitter = self.selectedpanel.GetParent()
        imgmap = ImageBitmap(hsplitter, self)
        hsplitter.AddWindow(imgmap)

    def DeleteWindow(self, window):
        if len(window.GetParent()._windows) == 1: return
        window.GetParent().DeleteWindow(window)

    def OnSize(self, evt):
        self.vsplitter.FitParent()
        for child in self.vsplitter._windows: child.FitParent()

class ImageNotebook(wx.aui.AuiNotebook):
    def __init__(self, parent, size = (800, 600)):
        wx.aui.AuiNotebook.__init__(self, parent, size = size)
        self.imgmenu = ImageControlMenu(self)
        self.ntab = 0
        self.AddTab()
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        pub.subscribe(self.AddTab, PT.TPC_ADDTAB)
        pub.subscribe(self.SetImage, PT.TPC_SRCTREE_SEL_CHANGED)

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

    def OnPageChanged(self, evt):
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

class ImageControlMenu(wx.Menu):
    def __init__(self, imgnotebook):
        wx.Menu.__init__(self)
        self.imgnotebook = imgnotebook

        addtabitem = wx.MenuItem(self, -1, 'Add new tab\tCtrl+T')
        self.AppendItem(addtabitem)
        self.AppendSeparator()
        keepratio = self.Append(-1, 'Keep original ratio', kind = wx.ITEM_CHECK)
        self.AppendSeparator()
        splitvitem = self.Append(-1, "Split vertical")
        splithitem = self.Append(-1, "Split horizontal")
        deleteitem = self.Append(-1, "Delete panel")
        deleterowitem = self.Append(-1, "Delete Row")

        self.Bind(wx.EVT_MENU, self.OnAddTab, addtabitem)
        self.Bind(wx.EVT_MENU, self.SetKeepRatio, keepratio)
        self.Bind(wx.EVT_MENU, self.OnSplitVertical, splitvitem)
        self.Bind(wx.EVT_MENU, self.OnSplitHorizontal, splithitem)
        self.Bind(wx.EVT_MENU, self.OnDelete, deleteitem)
        self.Bind(wx.EVT_MENU, self.OnDeleteRow, deleterowitem)

    def OnAddTab(self, evt):
        self.imgnotebook.AddTab()

    def SetKeepRatio(self, evt):
        pub.sendMessage(PT.TPC_KEEPRATIO, keepratio = evt.IsChecked())

    def OnSplitVertical(self, evt):
        activepage = self.imgnotebook.GetActivePage()
        if activepage: activepage.AddVertical()

    def OnSplitHorizontal(self, evt):
        activepage = self.imgnotebook.GetActivePage()
        if activepage: activepage.AddHorizontal()

    def OnDelete(self, evt):
        activepage = self.imgnotebook.GetActivePage()
        if activepage: activepage.DeleteWindow(activepage.GetSelection())

    def OnDeleteRow(self, evt):
        activepage = self.imgnotebook.GetActivePage()
        if activepage: activepage.DeleteWindow(activepage.GetSelection().GetParent())
