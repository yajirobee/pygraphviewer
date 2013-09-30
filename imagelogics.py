#! /usr/bin/env python

import sys, os, Image

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

def Get_MaxScaledImg(imgpath, maxsize, keepratio):
    img = Image.open(imgpath)
    size = Calc_MaxScaledImgSize(maxsize, img.size, keepratio)
    if size[0] < img.size[0] or size[1] < img.size[1]: flt = Image.ANTIALIAS
    else: flt = Image.NEAREST
    return img.resize(size, flt)

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
