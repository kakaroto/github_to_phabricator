#!/usr/bin/python

import sys
from github_issues import FetchGithubIssues
from wmfphablib import phabdb
from wmfphablib import phabapi
from wmfphablib import util
from wmfphablib import config


github_issues = FetchGithubIssues()
api = phabapi.phabapi()
project_phid = api.get_project_phid(config.project_name)

if project_phid is None:
    print "Could not find the project '%s' in Phabricator" % config.project_name
    sys.exit(-1)

if config.have_db_access is False and (config.delete_existing_issues or config.force_ids):
    print "You cannot delete existing taks or force task IDs if you do not have DB access"
    sys.exit(-1)

if config.delete_existing_issues:
    tasks = phabdb.get_task_list()
    for task in tasks:
        projects = phabdb.get_task_projects(task)
        if project_phid in projects:
            print "Deleting %s" % task
            util.destroy_issue(task)

if config.force_ids and len(phabdb.get_task_list()) > 0:
    print "You should not force task ID if there are still existing tasks in maniphest"
    sys.exit(-1)

for issue in github_issues:
    print "Creating issue %d" % issue.id
    author_phid = api.get_phid_by_username(issue.author)
    assignee_phid = None if issue.assignee is None else api.get_phid_by_username(issue.assignee)
    description = "= Task migrated from github issue #%d which was available at %s =\n\n%s" % (issue.id, issue.url, issue.description)
    if config.have_db_access is False or author_phid is None:
        description = "> Issue originally made by **%s** on //%s//\n\n%s" % (issue.author, issue.created_at, description)
    new_task = api.task_create(issue.title, description, issue.id, 90, assignee_phid, [project_phid])
    phid = new_task['phid']
    if config.force_ids:
        phabdb.set_task_id(issue.id, phid)
        id = issue.id
    else:
        id = new_task['id']

    if config.have_db_access:
        if author_phid:
            phabdb.set_task_author(author_phid, id)
        phabdb.set_task_ctime(phid, issue.created_at.strftime("%s"))
        phabdb.set_task_mtime(phid, issue.updated_at.strftime("%s"))

    if issue.state != "open":
        api.set_status(id, "resolved")
        if config.have_db_access:
            if issue.closed_at:
                tphid = phabdb.last_state_change(phid)
                phabdb.set_transaction_time(tphid, issue.closed_at.strftime("%s"))
    for (author, date, comment) in issue.comments:
        print "Adding comment from %s" % author
        author_phid = api.get_phid_by_username(author)
        if author_phid is None or config.have_db_access is False:
            comment = "> Comment originaly made by **%s** on //%s//\n\n%s" % (author, date, comment)
        api.task_comment(id, comment)
        if config.have_db_access:
            tphid = phabdb.last_comment(phid)
            phabdb.set_comment_time(tphid, date.strftime("%s"))
            if author_phid:
                phabdb.set_comment_author(tphid, author_phid)

util.purge_cache()
