#! /usr/bin/env python

import sys, os, wx
from wx.lib.pubsub import pub
from eventconst import PT

def isimage(path):
    imgexts = (".png", ".jpg")
    if not os.path.isfile(path): return False
    if os.path.splitext(path)[1] in imgexts: return True
    else: return False

class SourceTree(wx.TreeCtrl):
    class SourceTreeMenu(wx.Menu):
        def __init__(self, parent, itemID):
            wx.Menu.__init__(self)
            self.parent = parent
            self.itemID = itemID

            reloaditem = self.Append(-1, 'Reload list')
            self.AppendSeparator()
            deleteitem = self.Append(-1, 'Delete from list')

            self.Bind(wx.EVT_MENU, self.OnReload, reloaditem)
            self.Bind(wx.EVT_MENU, self.OnDeleteNode, deleteitem)

        def OnReload(self, evt):
            self.parent.Reload()

        def OnDeleteNode(self, evt):
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

    def OnRightClick(self, evt):
        itemID = evt.GetItem()
        if not itemID.IsOk(): itemID = self.GetSelection()
        menu = self.SourceTreeMenu(self, itemID)
        self.PopupMenu(menu)
        menu.Destroy()

    def OnSelectionChanged(self, evt):
        itemID = evt.GetItem()
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

    def OnExpand(self, evt):
        '''OnExpand is called when the user expands a node on the tree object.
        It checks whether the node has been previously expanded.
        If not, the extendTree function is called to build out the node,
        which is then marked as expanded.'''

        # get the wxID of the entry to expand and check it's validity
        itemID = evt.GetItem()
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
