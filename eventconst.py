class PublisherTopics:
    # event general
    TPC_SIZE = ("size",)
    # event on menu
    TPC_OPENDIR = ("opendir",)
    TPC_KEEPRATIO = ("keepratio",)
    TPC_QUALITY = ("quality",)
    # event for statusbar
    TPC_STATUS = ("statusbar",)
    TPC_STATUS_CONTENTCHANGED = ("statusbar", "contentchanged")
    # event on source tree
    TPC_SRCTREE = ("srctree",)
    TPC_SRCTREE_SEL_CHANGED = ("srctree", "selectionchanged")
    # event on image panel
    TPC_IMG = ("img",)
    TPC_IMG_SEL_CHANGED = ("img", "selectionchanged")
    TPC_IMG_SIZE_CHANGED = ("img", "sizechanged")

PT = PublisherTopics
