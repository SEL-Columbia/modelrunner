# -*- coding: utf-8 -*-
import os
import logging
import urllib2
import zipfile
import shutil
import psutil
from datetime import datetime
import json
from zipfile import ZipFile

# setup log
logger = logging.getLogger('modelrunner')

def fetch_file_from_url(url, destination_dir, file_name=None):
    """
    Utility function for retrieving a remote file from a url

    Args:
        url (str):  http based url for file to retrieve
        destination_dir (str):  local dir to place file in
        file_name (str):  name of local copy of file (if None glean from url)

    Exceptions:  will propagate any exception occuring during copy
    """

    dest_file_name = file_name
    if(not dest_file_name):
        dest_file_name = url.split('/')[-1]

    destination_file = os.path.join(destination_dir, dest_file_name)
    logger.info("Downloading from url {}".format(url))
    source = urllib2.urlopen(url)
    dest = open(destination_file, 'wb')
    try:
        shutil.copyfileobj(source, dest)
    except:
        logger.error("Failed to retrieve file from url {}".format(url))
        raise
    finally:
        source.close()
        dest.close()

    logger.info("Finished retrieving file from url {}".format(url))


def zipdir(path, zip_file_name):
    """
    Recursively zip up a directory

    Args:
        path (str):  local path of dir to be zipped
        zip_file_name (str):  name of zip to be created
    """

    output_zip = ZipFile(zip_file_name, 'w')
    for root, dirs, files in os.walk(path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), path)
            output_zip.write(
                os.path.join(root, file),
                arcname=rel_path,
                compress_type=zipfile.ZIP_DEFLATED)

    output_zip.close()


def kill_process_tree(pid):
    """
    Kill the process id'd by pid and all of its children
    """
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        logger.info("Killing child pid {}".format(child.pid))
        try:
            child.kill()
        except Exception as e:
            # if killing child fails, log it
            logger.warning(
                "exception occurred while killing pid {}: {}".\
                format(child.pid, e))

    # if killing parent fails, exception will be raised
    logger.info("Killing parent pid {}".format(parent.pid))
    parent.kill()


#<json helpers>
# mainly from:  http://stackoverflow.com/a/14996040
def json_dumps_datetime(obj):
    """
    json.dumps where datetime type is dumped as isoformat string
    """
    def obj_hook(d):
        if hasattr(d, 'isoformat'):
            return d.isoformat()
        else:
            return d

    return json.dumps(obj, default=obj_hook)

def json_loads_datetime(dump):
    """
    json.loads where isoformat string is loaded as datetime
    """
    def load_with_datetime(pairs, format='%Y-%m-%dT%H:%M:%S.%f'):
        """Load with datetimes"""
        d = {}
        for k, v in pairs:
            if isinstance(v, basestring):
                try:
                    d[k] = datetime.strptime(v, format)
                except ValueError:
                    d[k] = v
            else:
                d[k] = v
        return d

    return json.loads(dump, object_pairs_hook=load_with_datetime)
