#! /usr/bin/env python

import sys, os, Image, gtk

def Calc_MaxScaledImgSize(maxsize, imgsize, keepratio):
    maxw, maxh = maxsize
    imgw, imgh = imgsize
    if keepratio:
        maxratio = float(maxw) / maxh
        imgratio = float(imgw) / imgh
        if maxratio <= imgratio: rate = float(maxw) / imgw
        else: rate = float(maxh) / imgh
        return int(imgw * rate), int(imgh * rate)
    else:
        return maxw, maxh

def Get_MaxScaledImgold(imgpath, maxsize, keepratio):
    img = Image.open(imgpath)
    size = Calc_MaxScaledImgSize(maxsize, img.size, keepratio)
    if size[0] < img.size[0] or size[1] < img.size[1]: flt = Image.ANTIALIAS
    else: flt = Image.NEAREST
    scaledimg = img.resize(size, flt)
    return size, scaledimg.convert('RGB').tostring()

def Get_MaxScaledImg(imgpath, maxsize, keepratio):
    pb = gtk.gdk.pixbuf_new_from_file(imgpath)
    imgsize = (pb.get_width(), pb.get_height())
    size = Calc_MaxScaledImgSize(maxsize, imgsize, keepratio)
    interptype = gtk.gdk.INTERP_BILINEAR
    scaledpb = pb.scale_simple(size[0], size[1], interptype)

    # Each row of pixbuf has padding at end. They should be removed.
    rowstride = scaledpb.get_rowstride()
    nchannels = scaledpb.get_n_channels()
    paddingsize = rowstride - size[0] * nchannels
    pixels = scaledpb.get_pixels()
    if paddingsize > 0:
        pixels = ''.join([pixels[rowstride * i:rowstride * (i + 1) - paddingsize]
                          for i in range(size[1])])
    # remove alpha channel
    if nchannels != 3:
        pixels = ''.join([pixels[nchannels * i:nchannels * (i + 1) - (nchannels - 3)]
                          for i in range(size[0] * size[1])])
    return size, pixels


def Calc_Ratio_WindowCommission(oldratio):
    noldwin = len(oldratio)
    ratiofornew = 1. / (noldwin + 1)
    ratioforolds = 1 - ratiofornew
    ratio = [r * ratioforolds for r in oldratio]
    ratio.append(ratiofornew)
    return ratio

def Calc_Ratio_WindowDecommission(oldratio, index):
    ratio = list(oldratio)
    ratio.pop(index)
    return [r / float(sum(ratio)) for r in ratio]
