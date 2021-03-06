#!/usr/bin/env python

from __future__ import print_function

import datetime
import json

import yaml

from helpers import paginated_get
from pulls import get_pulls
from repos import Repo


LABELS_URL = "https://api.github.com/repos/{owner_repo}/labels"

def get_labels(repo):
    url = LABELS_URL.format(owner_repo=repo.name)
    return paginated_get(url)

def get_teams(repo):
    for label in get_labels(repo):
        if label["name"].startswith("waiting on "):
            yield label["name"][len("waiting on "):]

def pull_summary(issue):
    """Create a jsonable summary of a pull request."""
    keys = [
        "number", "title", "labels",
        "id", "repo", "intext", "org",
        "pull_request.html_url",
        "user.login",
        "user.html_url",
        "created_at", "updated_at",
        "assignee.login",
        "pull.base.ref",
        #"pull.comments", "pull.comments_url",
        #"pull.commits", "pull.commits_url",
        #"pull.additions", "pull.deletions",
        #"pull.changed_files",
    ]
    summary = { k.replace("pull.", "").replace(".","_"):issue[k] for k in keys }
    return summary


class WallMaker(object):
    def __init__(self):
        self.pulls = {}

    def show_wall(self, repos):

        self.team_names = set(get_teams(repos[0]))

        for repo in repos:
            self.one_repo(repo)

        wall_data = {
            "pulls": self.pulls,
            "updated": datetime.datetime.utcnow().isoformat(),
        }
        return wall_data

    def add_pull(self, issue):
        self.pulls[issue['id']] = pull_summary(issue)

    def one_repo(self, repo):
        issues = get_pulls(repo.name, state="open", org=True, pull_details="list")
        for issue in issues:
            issue["repo"] = repo.nick
            for label in issue['labels']:
                if label in self.team_names:
                    self.add_pull(issue)
                    break
            else:
                # Didn't find a blocking label, include it if external.
                if issue['intext'] == "external":
                    self.add_pull(issue)


def get_wall_data(pretty=False):
    """Returns a JSON string of aging data for the wall display."""
    repos = [ r for r in Repo.from_yaml() if r.track_pulls ]
    wall_data = WallMaker().show_wall(repos)
    return json.dumps(wall_data, indent=4 if pretty else None)

def main():
    print(get_wall_data())

if __name__ == "__main__":
    main()
