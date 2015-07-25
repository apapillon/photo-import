#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import logging
import os
import shutil
import sys

from gi.repository import GExiv2

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
    return files

def rename(src, target):
    try:
        exif = GExiv2.Metadata(src)
    except IOError:
        return False

    try:
        exifdate = exif.get_tag_string('Exif.Photo.DateTimeOriginal')
        if exifdate == None:
            return False
        date = datetime.datetime.strptime(exifdate, '%Y:%m:%d %H:%M:%S')
    except KeyError:
        return False

    destination = os.path.join(target, date.strftime('%Y/%m/%d'))
    if not os.path.lexists(destination):
        os.makedirs(destination)

    ext = os.path.splitext(src)[-1]
    for index in xrange(1, 255):
        filename = date.strftime('%Y%m%d_%H%M%S' + '_%03d%s' %(index, ext))
        filename = os.path.join(destination, filename)
        if not os.path.lexists(filename):
            shutil.copy2(src, filename)
            return filename

    return False

for file in get_files(source):
    print 'file:', file
    res = rename(file, target)
    if res:
        logging.debug('%s copied in %s.' % (file, res))
#        os.remove(file)

    elif os.path.splitext(file)[-1].upper() in ('.MOV', '.MP4'):
        mtime = os.stat(file).st_mtime
        date = datetime.datetime.utcfromtimestamp(mtime)
        dst = os.path.join(target, date.strftime('%Y/%m/%d/%Y%m%d_%H%M%S' + '_%s' %(os.path.split(file)[1])))
        shutil.copy2(file, dst)
        logging.debug('%s copied in %s.' % (file, dst))
#        os.remove(file)

    else:
        logging.warn('%s failed.' % (file))

