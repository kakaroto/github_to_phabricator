Github to Phabricator migration tool
---

# Requirements
You will need python (of course) and a version of phabricator-python that supports the new token-based authentication of Phabricator. 
Until it is merged upstream, you can use this version instead : https://github.com/gnoronha/python-phabricator/commits/new-style-auth
You will also need to have 'curl' installed.
For better results, you should have local access to the phabricator installation as well as database access, but it is not mandatory.

# Fetching from github
This tool has two parts, the first is what fetches all of data from github,
you can configure it in github_issues.py by setting the username, api token (that you generate in settings->personal access token), the project's org and repository name.
You can also set a minimum and maximum issue id to fetch for the migration. 
The data that gets downloaded from github is cached, so you must create a cache directory before use. If you want to refresh the issues, simply delete its content.
The script uses the external command 'curl' to fetch all the data, so make sure curl is installed. You can run ./github_issues.py to get it to fetch the issues and comments and print out the title and id of all the issues it found.


# Importing into Phabricator
The second part is what uploads the data to Phabricator. It can be configured in wmfphablib/config.py file. It will need a dedicated user for the migration (by default "github-migration"), so you must create such a user (add -> User Account) and set it as a bot.
You will then need to generate a conduit API token for that user, by accessing the user's profile (you can search for the user github-migration, then Edit settings, then Conduit API token).
Once you generate the token, you can set the phabricator URL, install path, databaser user/password and the Conduit token in the config.py file.

# Remote vs. Local
You can import into Phabricator either with local access to the phabricator server and access to its database, or by using only the remote API. Using the remote API will not allow you to preserve author and timestamp of issues and their comments (But that information is still retained as part of the description or comment itself).
If you do not have access to the Phabricator database, you can set the `have_db_access` to `False` in the config.py file.

Access to the phabricator database is required in order to force the task IDs to match the github issue id, as well as to be able to set the author and date of the task and comments. If database access is disabled, only the Conduit API will be used.
Note that forcing the phabricator task id to match github issue id will only be possible if there are no tasks in Phabricator. This feature can be disabled or enabled with the `force_ids` configuration variable.
Setting the phabricator_path is only necessary if you want to delete the existing tasks before importing. If `delete_existing_issues` is set to `False`, then the phabricator_path and access to the server is not required. Deleting existing tasks will only delete the tasks for the selected project, to avoid any potential mistakes.

# License
The wmfphablib code was copied from the wikimedia phabricator tools repository (https://gerrit.wikimedia.org/r/#/admin/projects/phabricator/tools) and modified to suit our needs.
This tool is therefore released under the same license as wikimedia's phabricator tools : GPL v2. See the LICENSE file for more information.
