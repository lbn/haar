import re
import os
import logging as log

from github_webhook import Webhook
from flask import Flask
from slackclient import SlackClient
import yaml

app = Flask("haar")
webhook = Webhook(app)

valid_branches = (
    re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+"),
    re.compile(r"release/[0-9]+\.[0-9]+"),
    re.compile(r"feature/.+"),
    re.compile(r"bug/.+"),
)

channel = os.getenv("HAAR_CHANNEL")
slack_token = os.getenv("SLACK_API_TOKEN")
sc = SlackClient(slack_token)


def branch_valid(branch):
    for prog in valid_branches:
        if prog.match(branch):
            return True
    return False


def get_username_map():
    with open("github_slack_users.yaml") as f:
        return yaml.load(f)


@app.route("/")
def hello_world():
    return "HAAR"

github_slack_names = get_username_map()


@webhook.hook()
def on_push(data):
    branch = "/".join(data["ref"].split("/")[2:])
    if not branch_valid(branch):
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            icon_url="https://i.imgur.com/vdixHeN.png",
            username="Handsome African-American Referee",
            text="You just pushed to a branch which does not match any of the accepted branch name patterns.",
            attachments=[
                {
                    "title": data["repository"]["name"],
                    "title_link": data["repository"]["url"],
                    "color": "#C40233",
                    "fields": [
                        {
                            "title": "Offender",
                            "value": "@"+github_slack_names.get(data["pusher"]["name"], data["pusher"]["name"]),
                            "short": True
                        },
                        {
                            "title": "Actual",
                            "value": branch,
                            "short": True
                        },
                        {
                            "title": "Expected",
                            "value": "\r\n".join([vb.pattern for vb in valid_branches]),
                            "short": True
                        },
                    ]
                }
            ])


def main():
    log.basicConfig(level=log.INFO)
    app.run(host="0.0.0.0", port=5010)

if __name__ == "__main__":
    main()
