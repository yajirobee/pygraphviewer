#! /usr/bin/env python

import os, sys, wx
import imagelogics
from eventconst import PT
import wx.lib.agw.aui as aui
from wx.lib.pubsub import pub
from wx.lib.splitter import MultiSplitterWindow

'''
class ImgMultiSplitter(MultiSplitterWindow):
    def __init__(self, parent, orientaion,
                 size = wx.DefaultSize, style = wx.SP_LIVE_UPDATE):
        MultiSplitterWindow.__init__(self, parent, size = size, style = style)
        self.SetOrientation(orientaion)

    def Destroy(self):
        for child in self._windows: child.Destroy()
        MultiSplitterWindow.Destroy(self)

    def CalcRatio(self, sashes):
        return [v / float(sum(sashes)) for v in sashes]

    def AddWindow(self, window):
        ratio = imagelogics.Calc_Ratio_WindowCommission(self.CalcRatio(self._sashes))
        length = sum(self._sashes) - self._GetSashSize()
        self.AppendWindow(window, int(length * ratio[-1]))
        for i, r in enumerate(ratio[:-1]): self.SetSashPosition(i, int(length * r))
        self.SizeWindows()
        pub.sendMessage(PT.TPC_SIZE)

    def DeleteWindow(self, window):
        if len(self._windows) == 1: return
        ratio = imagelogics.Calc_Ratio_WindowDecommission(self.CalcRatio(self._sashes),
                                                          self._windows.index(window))
        length = sum(self._sashes) + self._GetSashSize()
        parent = self.GetParent()
        while not isinstance(parent, ImgSchedulerPanel): parent = parent.GetParent()
        parent.SetSelection(None)
        self.DetachWindow(window)
        window.Destroy()
        for i, r in enumerate(ratio): self.SetSashPosition(i, int(length * r))
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
        pub.sendMessage(PT.TPC_SIZE)

    def OnSize(self, evt):
        self.FitParent()

    def OnChanging(self, evt):
        limit = sum(self._sashes)
        idx = evt.GetSashIdx()
        oldpos = self.GetSashPosition(idx)
        newpos = evt.GetSashPosition()
        if 0 == newpos: newpos = 1
        #print oldpos, newpos
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
'''

class ImagePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.bitmap = wx.StaticBitmap(self)
        self.imgpath = None
        self.keepratio = False
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.bitmap.Bind(wx.EVT_LEFT_DOWN, self.OnClick)
        self.bitmap.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        pub.subscribe(self.SetKeepratio, PT.TPC_KEEPRATIO)

    def Destroy(self):
        #pub.unsubscribe(self.OnSize, PT.TPC_SIZE)
        pub.unsubscribe(self.SetKeepratio, PT.TPC_KEEPRATIO)
        wx.Panel.Destroy(self)

    def SetImage(self, path):
        self.imgpath = path
        self.FitPanel()

    def SetKeepratio(self, keepratio):
        self.keepratio = keepratio
        self.FitPanel()

    def OnSize(self, evt = None):
        self.FitPanel()

    def FitPanel(self):
        if self.imgpath: self.FitImage()
        pub.sendMessage(PT.TPC_IMG_SIZE_CHANGED, id = self.GetId())

    def FitImage(self):
        size, scaledimg = imagelogics.Get_MaxScaledImg(self.imgpath,
                                                       self.GetSize(),
                                                       self.keepratio)
        wximg = wx.EmptyImage(size[0], size[1])
        wximg.SetData(scaledimg)
        self.bitmap.SetBitmap(wximg.ConvertToBitmap())

    def OnClick(self, evt):
        if isinstance(evt.GetEventObject(), wx.StaticBitmap):
            evt.SetEventObject(evt.GetEventObject().GetParent())
            self.GetParent().OnSelectionChanged(evt)
        else: self.GetParent().OnSelectionChanged(evt)

    def OnRightClick(self, evt):
        self.OnClick(evt)
        # This is very messy implementation because we cannot reconstruct menubar
        # for each menubar open (EVT_MENU_OPEN event does not work on Unity).
        menu = self.GetParent().GetParent().imgmenu
        menubar = self.GetTopLevelParent().GetMenuBar()
        for i, vals in enumerate(menubar.GetMenus()):
            if menu == vals[0]: break
        menubar.Remove(i)
        self.PopupMenu(menu)
        menubar.Insert(i, vals[0], vals[1])

class ImagePerspective(aui.AuiNotebook):
    def __init__(self, parent, size = (760, 570)):
        IMAGEPERSPECTIVE_AGW_STYLE = (aui.AUI_NB_TOP |
                                      aui.AUI_NB_TAB_SPLIT |
                                      aui.AUI_NB_TAB_MOVE |
                                      aui.AUI_NB_TAB_EXTERNAL_MOVE |
                                      aui.AUI_NB_SCROLL_BUTTONS |
                                      aui.AUI_NB_CLOSE_ON_ALL_TABS |
                                      aui.AUI_NB_DRAW_DND_TAB)
        aui.AuiNotebook.__init__(self, parent, size = size,
                                 agwStyle = IMAGEPERSPECTIVE_AGW_STYLE)
        self.ntab = 0
        self.AddTab()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AddTab(self, direction = None):
        self.ntab += 1
        newpanel = ImagePanel(self)
        self.AddPage(newpanel, "Tab{0}".format(self.ntab), True)
        if direction:
            idx = self.GetPageIndex(newpanel)
            self.Split(idx, direction)

    def OnSelectionChanged(self, evt):
        self.SetSelectionToWindow(evt.GetEventObject())
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

class ImageView(aui.AuiNotebook):
    def __init__(self, parent, size = (800, 600)):
        IMAGEVIEW_AGW_STYLE = (aui.AUI_NB_BOTTOM |
                               aui.AUI_NB_TAB_MOVE |
                               aui.AUI_NB_SCROLL_BUTTONS |
                               aui.AUI_NB_CLOSE_ON_ALL_TABS |
                               aui.AUI_NB_SMART_TABS)
        aui.AuiNotebook.__init__(self, parent, size = size,
                                 agwStyle = IMAGEVIEW_AGW_STYLE)
        self.imgmenu = ImageControlMenu(self)
        self.ntab = 0
        self.AddTab()
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        pub.subscribe(self.SetImage, PT.TPC_SRCTREE_SEL_CHANGED)

    def AddTab(self):
        self.ntab += 1
        self.AddPage(ImagePerspective(self), "Perspectiv{0}".format(self.ntab), True)

    def SetImage(self, path):
        activeperspective = self.GetCurrentPage()
        if activeperspective:
            activepanel = activeperspective.GetCurrentPage()
            if activepanel:
                activepanel.SetImage(path)
                pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

    def OnPageChanged(self, evt):
        pub.sendMessage(PT.TPC_IMG_SEL_CHANGED)

class ImageControlMenu(wx.Menu):
    keepratio = False

    def __init__(self, imgview):
        wx.Menu.__init__(self)
        self.imgview = imgview

        addtabitem = wx.MenuItem(self, -1, 'Add new Perspective\tCtrl+T')
        splitvitem = wx.MenuItem(self, -1, 'Split vertical\tCtrl+V')
        splithitem = wx.MenuItem(self, -1, 'Split horizontal\tCtrl+H')
        self.AppendItem(addtabitem)
        self.AppendSeparator()
        keepratioitem = self.Append(-1, 'Keep original ratio', kind = wx.ITEM_CHECK)
        keepratioitem.Check(ImageControlMenu.keepratio)
        self.AppendSeparator()
        self.AppendItem(splitvitem)
        self.AppendItem(splithitem)
        delperspectiveitem = self.Append(-1, "Delete Perspective")
        delpanelitem = self.Append(-1, "Delete Panel")

        self.Bind(wx.EVT_MENU, self.OnAddTab, addtabitem)
        self.Bind(wx.EVT_MENU, self.SetKeepRatio, keepratioitem)
        self.Bind(wx.EVT_MENU, self.OnSplitVertical, splitvitem)
        self.Bind(wx.EVT_MENU, self.OnSplitHorizontal, splithitem)
        self.Bind(wx.EVT_MENU, self.OnDeletePerSpective, delperspectiveitem)
        self.Bind(wx.EVT_MENU, self.OnDeletePanel, delpanelitem)

    def OnAddTab(self, evt):
        self.imgview.AddTab()

    def SetKeepRatio(self, evt):
        ImageControlMenu.keepraio = evt.IsChecked()
        pub.sendMessage(PT.TPC_KEEPRATIO, keepratio = evt.IsChecked())

    def OnSplitVertical(self, evt):
        activeperspective = self.imgview.GetCurrentPage()
        if activeperspective: activeperspective.AddTab(wx.BOTTOM)

    def OnSplitHorizontal(self, evt):
        activeperspective = self.imgview.GetCurrentPage()
        if activeperspective: activeperspective.AddTab(wx.RIGHT)

    def OnDeletePerSpective(self, evt):
        activeperspective = self.imgview.GetCurrentPage()
        if activeperspective: self.imgview.DeletePage(activeperspective)

    def OnDeletePanel(self, evt):
        activeperspective = self.imgview.GetCurrentPage()
        if activeperspective:
            activepanel = activepanel.GetCurrentPage()
            if activepanel: activeperspective.DeletePage(activepanel)
