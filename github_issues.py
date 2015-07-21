#!/usr/bin/python

import sys
import subprocess
import json
import operator
from datetime import datetime
import os

USERNAME="github username"
TOKEN="github access token"
USER="organization"
PROJECT="repository"
MIN_ID=None
MAX_ID=None

BASE_URL="https://api.github.com/"
CACHE_DIR="cache/"

def fetch_cached_json(suffix):
    path = CACHE_DIR + suffix.replace("/", "_")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return None

def write_cached_json(suffix, data):
    path = CACHE_DIR + suffix.replace("/", "_")
    with open(path, 'w') as f:
        f.write(data)

def fetch_json(suffix):
    cached = fetch_cached_json(suffix)
    if cached is None:
        url = BASE_URL + "repos/" + USER + "/" + PROJECT + suffix

        process = subprocess.Popen(['curl', '-i', '-s', '-u', USERNAME + ":" + TOKEN, url],
                               stdout=subprocess.PIPE)
        result = process.communicate()[0]
        write_cached_json(suffix, result)
    else:
        result = cached
    return result.split("\r\n\r\n", 1)

class Issue(object):
    def __init__(self, github_dict):
        self.json = github_dict
        self.id = self.json['number']
        self.url = self.json['html_url']
        self.state = self.json['state']
        self.title = self.json['title']
        self.description = self.json['body']
        self.author = self.json['user']['login']
        if self.json['assignee']:
            self.assignee = self.json['assignee']['login']
        else:
            self.assignee = None
        self.labels = []
        for l in self.json['labels']:
            self.labels.append(l['name'])
        self.created_at = datetime.strptime(self.json['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        self.updated_at = datetime.strptime(self.json['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
        if self.json['closed_at']:
            self.closed_at = datetime.strptime(self.json['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            self.closed_at = None
        self.comments = []

    def AddComment(self, author, date, content):
        self.comments.append((author, datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ'), content))

def FetchGithubIssues():
    page = 1
    num_pages = 1
    issues = []
    github_issues = []

    while page <= num_pages:
        (headers, issues_json) = fetch_json("/issues?state=all&per_page=100&page=%d" % page)
        page = page + 1
        issues.extend(json.loads(issues_json))
        headers = headers.split('\r\n')
        for header in headers[1:]:
            (key, value) = header.split(":", 1)
            if key == "Link":
                try:
                    value.index('rel="next"')
                    num_pages = page
                except:
                    pass
                break

    for i in issues:
        issue = Issue(i)
        if MIN_ID and MAX_ID:
            if issue.id < MIN_ID or issue.id > MAX_ID:
                continue
        github_issues.append(issue)
        if issue.json['comments'] > 0:
            (headers, comments_json) = fetch_json("/issues/%d/comments?per_page=100" % issue.id)
            comments = json.loads(comments_json)
            for c in comments:
                issue.AddComment(c['user']['login'], c['created_at'], c['body'])

    return sorted(github_issues, key=operator.attrgetter('id'))


if __name__ == '__main__':
    issues = FetchGithubIssues()
    for issue in issues:
        print "%d (%s): %s" % (issue.id, issue.state, issue.title)
