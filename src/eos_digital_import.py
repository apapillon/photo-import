#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import datetime
import filecmp
import glob
import logging
import os
import re
import shutil

from gi.repository import GExiv2

NUM_ARGS = 0

log_file = 'eos_digital_import.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG)

def getting_listing(path):
    """return list with all file into path and subpath"""
    res = list()
    for f in glob.glob(os.path.join(path,'*')):
        if os.path.isdir(f):
            res.extend(getting_listing(f))
        elif os.path.isfile(f):
            res.append(f)
    return res

def get_datetime(filename):
    """Return datetime from EXIF, filename or modification time (in this order)."""
    # Get datetime from EXIF
    try:
        exif = GExiv2.Metadata(filename)
        exifdate = exif.get_tag_string('Exif.Photo.DateTimeOriginal')
        if exifdate:
            return datetime.datetime.strptime(exifdate, '%Y:%m:%d %H:%M:%S')
    except IOError:
        return None
    except KeyError:
        pass

    # Get datetime from filename
    try:
        fname = os.path.splitext(filename)[0]
        return datetime.datetime.strptime(fname[-15:], '%Y%m%d_%H%M%S')
    except ValueError:
        pass

    # Get datetime from mtime
    return datetime.datetime.utcfromtimestamp(os.stat(filename).st_mtime)

def get_timedelta(dtime):
    """Extract timedelta for dtime argument """
    try:
        m = re.match(r'([+-]?)(\d{1,2}):(\d{2})', dtime or '')
        sens, hours, minutes = m.group(1, 2, 3)
    except AttributeError, TypeError:
        return datetime.timedelta()

    tdelta = datetime.timedelta(hours=int(hours), minutes=int(minutes))
    if sens == '-':
        tdelta = -tdelta
    return tdelta

def search_newfilename(outpath, dfile, ext):
    """Search new filename doesn't use. If file exist return None."""
    for i in xrange(1,255):
        newfname = dfile.strftime('%Y%m%d_%H%M%S' + '_{:03d}{}'.format(i, ext))
        
        newf = os.path.join(outpath, newfname)
        if not os.path.exists(newf):
            return newf

        if filecmp.cmp(f, newf):
            # file already exist identicaly
            return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='Path from import files')
    parser.add_argument('outpath', type=str, help='Path to export files')
    parser.add_argument('--log', type=str, help='log file')
    parser.add_argument('--dtime', type=str, help='Correct datetime EXIF (Format: +HH:MM)')
    parser.add_argument('--remove', help='Remove file after transfert',
                        action="store_true")

    args = parser.parse_args()
    tdelta = get_timedelta(args.dtime)

    for f in getting_listing(args.input):
        dfile = get_datetime(f) + tdelta

        # Make path destination
        outpath = os.path.join(args.outpath, dfile.strftime('%Y/%m/%d'))
        if not os.path.lexists(outpath):
            os.makedirs(outpath)

        # Search new filename
        froot, fext = os.path.splitext(f)
        newfilename = search_newfilename(outpath, dfile, fext)
        if not newfilename:
            logging.debug('{} already exist in new path.'.format(f))
            if args.remove:
                os.remove(f)
                logging.debug('{} removed.'.format(f))
            continue

        # Copy file to new path
        shutil.copy2(f, newfilename)
        logging.debug('{} copied in {}.'.format(f, newfilename))
        if args.remove:
            os.remove(f)
            logging.debug('{} removed.'.format(f))

