#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import logging
import os
import pyexiv2
import shutil
import sys

source = sys.argv[1]
target = sys.argv[2]
log_file = 'eos_digital_import.log'

logging.basicConfig(filename=log_file, level=logging.DEBUG)

def get_files(path):
    files = list()
    for filename in os.listdir(path):
        filename = os.path.abspath(os.path.join(path, filename))
        if os.path.isdir(filename):
            files.extend(get_files(filename))
        else:
            files.append(filename)
    files.sort()
    return files

def cmp_file(x, y, bufSize=512):
    """Compare les 2 fichiers et renvoie True seulement s'ils ont un contenu identique"""
    f1 = f2 = None
    res = False
    try:
        if os.path.getsize(x) == os.path.getsize(y):
            f1 = open(x, "rb")
            f2 = open(y, "rb")
            while True:
                buf1 = f1.read(bufSize)
                if len(buf1) == 0:
                    res = True
                    break
                buf2 = f2.read(bufSize)
                if buf1 != buf2:
                    break
            f1.close()
            f2.close()
    except:
        if f1 != None: f1.close()
        if f2 != None: f2.close()
        raise
    return res

def getdate(src):
    res = False

    try:
        img = pyexiv2.metadata.ImageMetadata(src)
        img.read()
    except IOError:
        img = False

    if img:
        for k in ['Exif.Photo.DateTimeOriginal', 'Exif.Photo.DateTimeDigitized',
                  'Exif.Image.DateTime', 'Xmp.exif.DateTimeOriginal']:
            if k in img:
                date = img[k]
                res = date.value
                break

    if res == False:
        spFilename = os.path.splitext(src)
        infoFile = '%s.%s' % (spFilename[0], 'THM')
        if os.path.lexists(infoFile) and spFilename[1].upper() != '.THM':
            res = getdate(infoFile)
            print res

    if res == False:
        bnFilename = os.path.splitext(os.path.basename(src))[0]
        if bnFilename.startswith('VID_') or bnFilename.startswith('IMG_'):
            bnFilename = bnFilename[4:]
        try:
            res = datetime.datetime.strptime(bnFilename[:15], '%Y%m%d_%H%M%S')
        except ValueError:
            res = False

    if res == False:
        res = datetime.datetime.utcfromtimestamp(os.stat(src).st_mtime)
        r = raw_input('file %s date = %s ? [Y/n]' % (src, res))
        if r and r.upper() != 'Y':
            r_date = raw_input('Enter date file (format: 2000-12-31 12:00:00): ')
            res = datetime.datetime.strptime(r_date, '%Y-%m-%d %H:%M:%S')
        elif not r:
            res = False

    return res

def cpy(src, outpath, date):
    destination = os.path.join(target, date.strftime('%Y/%m/%d'))
    if not os.path.lexists(destination):
        os.makedirs(destination)

    ext = os.path.splitext(src)[-1]
    for index in xrange(1, 255):
        filename = date.strftime('%Y%m%d_%H%M%S' + '_%03d%s' %(index, ext))
        filename = os.path.join(destination, filename.upper())
        if not os.path.lexists(filename):
            shutil.copy2(src, filename)
            return filename

        elif cmp_file(src, filename):
            return filename

    return False

for file in get_files(source):
    print 'file:', file
    date = getdate(file)

    if date:
        newname = cpy(file, target, date)
        logging.debug('%s copied in %s.' % (file, newname))
        os.remove(file)
        
    else:
        logging.warn('%s failed.' % (file))

