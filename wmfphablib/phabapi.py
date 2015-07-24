import base64
import config
import phabricator
from phabricator import Phabricator
import phabdb
from util import log
from util import vlog
from util import errorlog as elog

class phabapi:
    """wrapper for phab api"""

    def __init__(self):
        self.con = Phabricator(host=config.phab_host, token=config.phab_token)

    def blog_update(self, botname, title, body):
        blogphid = phabdb.get_bot_blog(botname)
        if blogphid is None:
            elog('blogphid is none')
            return
        return self.con.phame.createpost(blogPHID=blogphid,
                                         body=body,
                                         title=title,
                                         phameTitle=title)

    def sync_assigned(self, userphid, id, prepend):
        refs = phabdb.reference_ticket('%s%s' % (prepend, id))
        if not refs:
            log('reference ticket not found for %s' % ('%s%s' % (prepend, id),))
            return
        current = self.con.maniphest.query(phids=[refs[0]])
        if current[current.keys()[0]]['ownerPHID']:
            log('current owner found for => %s' % (str(id),))
            return current
        log('assigning T%s to %s' % (str(id), userphid))
        return phabdb.set_issue_assigned(refs[0], userphid)

    def synced_authored(self, phid, id, ref):
        refs = phabdb.reference_ticket('%s%s' % (ref, id))
        if not refs:
            log('reference ticket not found for %s' % ('%s%s' % (ref, id),))
            return
        log('reference ticket found for %s' % ('%s%s' % (ref, id),))
        newid = self.ticket_id_by_phid(refs[0])
        log("Updating author for %s to %s" % (refs, phid))
        phabdb.set_task_author(phid, newid)

        descript = phabdb.get_task_description(refs[0])
        try:
            clean_description = descript.split('**Description:**\n', 1)[1]
            phabdb.set_task_description(refs[0], clean_description)
        except:
            phabdb.set_task_description(refs[0], descript)

    def task_comment(self, task, msg):
        out = self.con.maniphest.update(id=task, comments=msg)
        return out

    def set_status(self, task, status):
        out = self.con.maniphest.update(id=task, status=status)
        return out

    def task_create(self, title, desc, id, priority, ownerPhid=None, projects=[]):
        return self.con.maniphest.createtask(title=title,
                                        description="%s" % desc,
                                        projectPHIDs=projects,
                                        priority=priority,
                                        ownerPHID=ownerPhid,
                                        auxiliary={"std:maniphest:external_reference":"%s" % (id,)})

    def get_project_phid(self, name):
        result = self.con.project.query(names=[name])
        if result:
            return result['data'].keys()[0]
        return None

    def get_phid_by_username(self, username):
        result = self.con.user.query(usernames=[username])
        if len(result.response):
            return result[0]['phid']
        return None

if config.have_db_access:
    def ensure_project(self, project_name,
                             pmembers=[],
                             view='public',
                             edit='public'):
        """make sure project exists
        :param project_name: str
        :param pmembers: list
        :param view: str
        :param edit str"""
        existing_proj = phabdb.get_project_phid(project_name)
        #print "EXISTING PROJ: ", existing_proj
        #print "EXISTING PROJ TYPE: ", type(existing_proj)
        #existing_proj = self.con.project.query(names=[project_name])
        if not existing_proj:
            log('need to create project(s) ' + project_name)
            try:
                new_proj = self.con.project.create(name=project_name, members=pmembers)
            #XXX: Bug where we have to specify a members array!
            except phabricator.APIError:
                pass
            phid = phabdb.get_project_phid(project_name)
            if not phid:
                raise Exception("Project %s does not exist still." % (project_name,))
            #existing_proj = self.con.project.query(names=[project_name])
            #log(str(existing_proj))
            #phid = existing_proj['data'][existing_proj['data'].keys()[0]]['phid']
            phabdb.set_project_policy(phid, view, edit)
        else:
            phid = existing_proj
            #phid = existing_proj['data'][existing_proj['data'].keys()[0]]['phid']
            log(project_name + ' exists')
        return phid

    def upload_file(self, name, data, viewPolicy, dump=False):

        if dump:
            with open(name, 'wb') as f:
                f.write(data)

        log("upload policy for %s is %s" % (name, viewPolicy))
        out = {}
        self.con.timeout = config.file_upload_timeout
        encoded = base64.b64encode(data)
        uploadphid = self.con.file.upload(name=name,
                                          data_base64=encoded,
                                          viewPolicy=viewPolicy)
        out['phid'] = uploadphid
        log("%s upload response: %s" % (name, uploadphid.response))
        fileid = phabdb.get_file_id_by_phid(uploadphid.response)
        out['id'] = int(fileid)
        out['name'] = name
        out['objectName'] = "F%s" % (fileid,)
        log("Created file id: %s" % (fileid,))
        self.con.timeout = 5
        return out

    def ticket_id_by_phid(self, phid):
         tinfo = self.con.maniphest.query(phids=[phid])
         if not tinfo:
             return ''
         if not tinfo.keys():
             return ''
         return tinfo[tinfo.keys()[0]]['id']
