import os
import sys
import syslog
import datetime
import time
from util import log
from util import notice
from util import vlog
from util import errorlog
from util import datetime_to_epoch
from util import epoch_to_datetime
from phabapi import phabapi as Phab
from phabdb import phdb
from phabdb import mailinglist_phid
from phabdb import set_project_icon

def now():
    return int(time.time())

def tflatten(t_of_tuples):
    return [element for tupl in t_of_tuples for element in tupl]

#import priority status meanings
ipriority = {'creation_failed': 6,
             'creation_success': 7,
             'fetch_failed': 5,
             'fetch_success': 4,
             'na': 0,
             'denied': 2,
             'missing': 3,
             'update_success': 8,
             'update_success_comments': 10,
             'update_failed': 9,
             'update_failed_comments': 11,
             'unresolved': 1}

def save_attachment(name, data):
    f = open(name, 'wb')
    f.write(data)
    f.close()
