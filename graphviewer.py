#! /usr/bin/env python

import sys, os, wx, wx.aui
from wx.lib.pubsub import pub
from wx.lib.splitter import MultiSplitterWindow

class PublisherTopics:
    # event general
    TPC_SIZE = ("size")
    # event on menu
    TPC_OPENDIR = ("opendir")
    TPC_ADDTAB = ("addtab")
    TPC_KEEPRATIO = ("keepratio")
    TPC_SPLIT_VERTICAL = ("splitvertical")
    TPC_SPLIT_HORIZONTAL = ("splithorizontal")
    # event on source tree
    TPC_SRCTREE = ("srctree")
    TPC_SRCTREE_SEL_CHANGED = ("srctree", "selectionchanged")

PT = PublisherTopics

def isimage(path):
    imgexts = (".png", ".jpg")
    if not os.path.isfile(path): return False
    if os.path.splitext(path)[1] in imgexts: return True
    else: return False

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

        windowmenu = wx.Menu()
        addtabitem = wx.MenuItem(windowmenu, -1, 'Add new tab\tCtrl+T')
        windowmenu.AppendItem(addtabitem)
        windowmenu.AppendSeparator()
        splitv = windowmenu.Append(-1, "Split vertical")
        splith = windowmenu.Append(-1, "Split horizontal")

        optionmenu = wx.Menu()
        keepratio = optionmenu.Append(-1, 'Keep original ratio', kind = wx.ITEM_CHECK)

        RootFrame.Bind(wx.EVT_MENU, self.OnOpenDir, openitem)
        RootFrame.Bind(wx.EVT_MENU, RootFrame.OnQuit, quititem)
        RootFrame.Bind(wx.EVT_MENU, self.OnAddTab, addtabitem)
        RootFrame.Bind(wx.EVT_MENU, self.SetKeepRatio, keepratio)
        RootFrame.Bind(wx.EVT_MENU, self.OnSplitVertical, splitv)
        RootFrame.Bind(wx.EVT_MENU, self.OnSplitHorizontal, splith)

        self.Append(filemenu, '&File')
        self.Append(windowmenu, '&Window')
        self.Append(optionmenu, '&Option')

    def OnOpenDir(self, event):
        dlg = wx.DirDialog(self, "Choose a Directory", style = wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            pub.sendMessage(PT.TPC_OPENDIR, path = dlg.GetPath())
        dlg.Destroy()

    def OnAddTab(self, event):
        pub.sendMessage(PT.TPC_ADDTAB)

    def OnSplitVertical(self, event):
        pub.sendMessage(PT.TPC_SPLIT_VERTICAL)

    def OnSplitHorizontal(self, event):
        pub.sendMessage(PT.TPC_SPLIT_HORIZONTAL)

    def SetKeepRatio(self, event):
        pub.sendMessage(PT.TPC_KEEPRATIO, keepratio = event.IsChecked())

class SourceTree(wx.TreeCtrl):
    class SourceTreeMenu(wx.Menu):
        def __init__(self, parent, itemID):
            wx.Menu.__init__(self)
            self.parent = parent
            self.itemID = itemID

            self.Append(1001, 'Reload list')
            self.AppendSeparator()
            self.Append(1002, 'Delete from list')

            self.Bind(wx.EVT_MENU, self.OnReload, id = 1001)
            self.Bind(wx.EVT_MENU, self.OnDeleteNode, id = 1002)

        def OnReload(self, event):
            self.parent.Reload()

        def OnDeleteNode(self, event):
            self.parent.DeleteNode(self.itemID)

    def __init__(self, parent, size = (200, 400)):
        wx.TreeCtrl.__init__(self, parent, size = size,
                             style = wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE |
                             wx.TR_DEFAULT_STYLE | wx.SUNKEN_BORDER)
        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpand, self)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick, self)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged, self)
        pub.subscribe(self.AddRootChild, PT.TPC_OPENDIR)
        self.rootID = self.AddRoot("root")

    def OnRightClick(self, event):
        itemID = event.GetItem()
        if not itemID.IsOk(): itemID = self.GetSelection()
        menu = self.SourceTreeMenu(self, itemID)
        self.PopupMenu(menu)
        menu.Destroy()

    def OnSelectionChanged(self, event):
        itemID = event.GetItem()
        path = ""
        if itemID.IsOk():
            path = self.GetPyData(itemID)
        if path and isimage(path[0]):
            pub.sendMessage(PT.TPC_SRCTREE_SEL_CHANGED, path = path[0])

    def Reload(self):
        child, cookie = self.GetFirstChild(self.rootID)
        while child.IsOk():
            self.DeleteChildren(child)
            self.ExtendTree(child)
            child, cookie = self.GetNextChild(self.rootID, cookie)

    def DeleteNode(self, itemID):
        self.Delete(itemID)

    def OnExpand(self, event):
        '''OnExpand is called when the user expands a node on the tree object.
        It checks whether the node has been previously expanded.
        If not, the extendTree function is called to build out the node,
        which is then marked as expanded.'''

        # get the wxID of the entry to expand and check it's validity
        itemID = event.GetItem()
        if not itemID.IsOk(): itemID = self.GetSelection()

        # only build that tree if not previously expanded
        old_pydata = self.GetPyData(itemID)
        if old_pydata[1] == False:
            # clean the subtree and rebuild it
            self.DeleteChildren(itemID)
            self.SetPyData(itemID, (old_pydata[0], True))
            self.ExtendTree(itemID)

    def AddRootChild(self, path):
        c, cookie = self.GetFirstChild(self.rootID)
        while c.IsOk():
            pydata = self.GetPyData(c)
            if pydata[0] == path: return
            c, cookie = self.GetNextChild(self.rootID, cookie)
        childID = self.AppendItem(self.rootID, os.path.basename(path))
        self.SetPyData(childID, (path, True))
        self.ExtendTree(childID)

    def ExtendTree(self, parentID):
        '''extendTree is a semi-lazy directory tree builder.
        It takes the ID of a tree entry and fills in the tree with its child
        subdirectories and their children - updating 2 layers of the tree.
        This function is called by BuildTree and OnExpand methods'''

        # retrieve the associated absolute path of the parent
        parentDir = self.GetPyData(parentID)[0]

        children = os.listdir(parentDir)
        children.sort()
        dirlist, imglist = [], []
        for child in children:
            child_path = os.path.join(parentDir, child)
            if os.path.isdir(child_path): dirlist.append(child)
            elif isimage(child_path): imglist.append(child)
        for child in dirlist:
            child_path = os.path.join(parentDir, child)
            childID = self.AppendItem(parentID, child)
            if os.access(child_path, os.R_OK):
                self.SetPyData(childID, (child_path, False))
                # Now the child entry will show up, but it current has no
                # known children of its own and will not have a '+' showing
                # that it can be expanded to step further down the tree.
                # Solution is to go ahead and register the child's children,
                # meaning the grandchildren of the original parent
                grandchildren = os.listdir(child_path)
                grandchildren.sort()
                dlist, ilist = [], []
                for grandchild in grandchildren:
                    grandchild_path = os.path.join(child_path, grandchild)
                    if os.path.isdir(grandchild_path): dlist.append(grandchild)
                    elif isimage(grandchild_path): ilist.append(grandchild)
                for grandchild in dlist + ilist:
                    grandchild_path = os.path.join(child_path, grandchild)
                    grandchildID = self.AppendItem(childID, grandchild)
                    self.SetPyData(grandchildID, (grandchild_path, False))
            else:
                self.SetPyData(childID, (child_path + "(Cannot access)", False))
        for child in imglist:
            child_path = os.path.join(parentDir, child)
            childID = self.AppendItem(parentID, child)
            self.SetPyData(childID, (child_path, False))

class ImageBitmap(wx.StaticBitmap):
    def __init__(self, parent):
        wx.StaticBitmap.__init__(self, parent)
        self.imgpath = None
        self.img = None
        self.keepratio = False
        pub.subscribe(self.OnSize, PT.TPC_SIZE)
        pub.subscribe(self.SetKeepratio, PT.TPC_KEEPRATIO)

    def SetImage(self, path):
        self.imgpath = path
        self.img = wx.Image(path)
        self.FitImage()

    def FitImage(self):
        mapw, maph = self.GetSize()
        imgw, imgh = self.img.GetWidth(), self.img.GetHeight()
        print mapw, maph, imgw, imgh
        if self.keepratio:
            mapratio = float(mapw) / maph
            imgratio = float(imgw) / imgh
            if mapratio <= imgratio: rate = float(mapw) / imgw
            else: rate = float(maph) / imgh
            width = int(imgw * rate)
            height = int(imgh * rate)
            img = self.img.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        else:
            img = self.img.Scale(mapw, maph, wx.IMAGE_QUALITY_HIGH)
        self.SetBitmap(img.ConvertToBitmap())

    def SetKeepratio(self, keepratio):
        self.keepratio = keepratio
        self.OnSize()

    def OnSize(self):
        self.SetSize(self.GetParent().GetSize())
        self.FitImage()

class ImgPanel(wx.Panel):
    borderwidth = 6

    def __init__(self, parent, size = (760, 570)):
        wx.Panel.__init__(self, parent, size = size)

        self.vsplitter = vsplitter = MultiSplitterWindow(self, size = (720, 540),
                                                         style = wx.SP_LIVE_UPDATE)
        vsplitter.SetOrientation(wx.VERTICAL)
        hsplitter = MultiSplitterWindow(self.vsplitter, style = wx.SP_LIVE_UPDATE)
        hsplitter.SetOrientation(wx.HORIZONTAL)
        vsplitter.AppendWindow(hsplitter, self.GetSize()[1])
        hsplitter.AppendWindow(wx.Panel(hsplitter, style = wx.BORDER_SUNKEN),
                               vsplitter.GetSize()[0])
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnChanging)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnChanged)
        self.Bind(wx.EVT_SIZE, self.OnSize)

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

    def AddVertical(self):
        hsplitter = MultiSplitterWindow(self.vsplitter, style = wx.SP_LIVE_UPDATE)
        hsplitter.SetOrientation(wx.HORIZONTAL)
        hsplitter.AppendWindow(wx.Panel(hsplitter, style = wx.BORDER_SUNKEN),
                               self.vsplitter.GetSize()[0])
        self.AddChild(self.vsplitter, hsplitter)

    def AddHorizontal(self, idx):
        hsplitter = self.vsplitter.GetWindow(idx)
        self.AddChild(hsplitter, wx.Panel(hsplitter, style = wx.BORDER_SUNKEN))

    def OnChanging(self, event):
        eobj = event.GetEventObject()
        if eobj.GetOrientation() == wx.HORIZONTAL:
            print "horizontal", event.GetSashPosition()
            #eobj.SetSize((event.GetSashPosition(), eobj.GetSize()[1]))
        else:
            print "vertical", event.GetSashPosition()
            #eobj.SetSize((eobj.GetSize()[0], event.GetSashPosition()))
        print eobj._sashes

    def OnChanged(self, event):
        if event.GetId() == self.vsplitter.GetId():
            win = self.vsplitter.GetWindow(event.GetSashIdx())
            win.SetSize((win.GetSize()[0], event.GetSashPosition()))
            win.SizeWindows()

    def OnSize(self, event):
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
        pub.subscribe(self.AddTab, PT.TPC_ADDTAB)
        pub.subscribe(self.SetImage, PT.TPC_SRCTREE_SEL_CHANGED)
        pub.subscribe(self.SplitVertical, PT.TPC_SPLIT_VERTICAL)
        pub.subscribe(self.SplitHorizontal, PT.TPC_SPLIT_HORIZONTAL)

    def AddTab(self):
        self.ntab += 1
        self.AddPage(ImgPanel(self), "tab{0}".format(self.ntab), True)

    def SetImage(self, path):
        activeidx = self.GetSelection()
        if activeidx != -1:
            activepage = self.GetPage(activeidx)
            activepage.bitmap.SetImage(path)

    def SplitVertical(self):
        activeidx = self.GetSelection()
        if activeidx != -1:
            activepage = self.GetPage(activeidx)
            activepage.AddVertical()

    def SplitHorizontal(self):
        activeidx = self.GetSelection()
        if activeidx != -1:
            activepage = self.GetPage(activeidx)
            activepage.AddHorizontal(0)

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
        self.SetMenuBar(MainMenuBar(self))

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.Show(True)

    def OnSize(self, event):
        self.Refresh()
        pub.sendMessage(PT.TPC_SIZE)
        print "window", self.GetSize(), self.srcview.GetSize(), self.imgnotebook.GetSize(), self.imgnotebook.GetPage(0).GetSize()

    def OnQuit(self, event):
        self._mgr.UnInit()
        self.Destroy()

if __name__ == "__main__":
    app = wx.App()
    MainFrame(None, -1, 'graphviewer')
    app.MainLoop()
