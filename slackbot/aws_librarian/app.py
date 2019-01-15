"""
Slack chat-bot Lambda handler.
"""

import os
import logging
import urllib
import json
import boto3
import traceback
import re

from rds_util import *
from requests_toolbelt.multipart import decoder

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

client = boto3.client('ssm')

# Define the URL of the targeted Slack API resource.
# We'll send our replies there.
SLACK_URL = "https://slack.com/api/chat.postMessage"


def load_params(path):
    param_details = client.get_parameters_by_path(
        Path=path,
        Recursive=False,
        WithDecryption=True
    )

    toReturn = {}

    for param_info in param_details["Parameters"]:
        toReturn[param_info["Name"][len(path):]] = param_info["Value"]

    return toReturn


params = load_params("/librarian/")

BOT_TOKEN = params["bot_token"]
slack_signing_secret = params["slack_signing_key"]

params = load_params("/rds/devdb/")
rds_host = params["host_url"]
user = params["username"]
password = params["password"]
db_name = params["aws_librarian_db_name"]


try:
    rdsi = RDSInterface(rds_host, user,
                        password, db_name)
except Exception as e:
    logger.error(e)
    logger.error(
        "ERROR: Unexpected error: Could not connect to MySql instance.")
logger.info("SUCCESS: Connection to RDS mysql instance succeeded")


def formatQueryOutput(books):
    if books is None or len(books) == 0:
        return ["no books found"]

    by_series = {}
    for book in books:
        if book.series not in by_series:
            by_series[book.series] = list()
        by_series[book.series].append(book)

    output = list()

    for series, books_list in by_series.items():
        if series == "":
            formated_series = "Not Part of a series \n"
        else:
            formated_series = "Series {0}\n".format(series)

        for book in books_list:
            formated_series += "\t{0} - {1}".format(
                book.name, book.dropbox_link)
        output.append(formated_series)

    return output


def send_slack_message(channel_id, text):
    # We need to send back three pieces of information:
    #     1. The reversed text (text)
    #     2. The channel id of the private, direct chat (channel)
    #     3. The OAuth token required to communicate with
    #        the API (token)
    # Then, create an associative array and URL-encode it,
    # since the Slack API doesn't not handle JSON (bummer).
    data = urllib.parse.urlencode(
        (
            ("token", BOT_TOKEN),
            ("channel", channel_id),
            ("text", text)
        )
    )
    data = data.encode("ascii")

    # Construct the HTTP request that will be sent to the Slack API.
    request = urllib.request.Request(
        SLACK_URL,
        data=data,
        method="POST"
    )
    # Add a header mentioning that the text is URL-encoded.
    request.add_header(
        "Content-Type",
        "application/x-www-form-urlencoded"
    )

    # Fire off the request!
    urllib.request.urlopen(request).read()


def handle_bot_event(body):
    data = json.loads(body)
    # Grab the Slack event data.
    slack_event = data['event']

    # We need to discriminate between events generated by
    # the users, which we want to process and handle,
    # and those generated by the bot.
    if "bot_id" in slack_event:
        logging.warn("Ignore bot event")
    else:
        # Get the text of the message the user sent to the bot,
        # and reverse it.
        text = slack_event["text"]
        series = formatQueryOutput(rdsi.query_name(text))

        # Get the ID of the channel where the message was posted.
        channel_id = slack_event["channel"]

        for serie in series:
            send_slack_message(channel_id, serie)

    # Everything went fine.
    return {
        "statusCode": 200,
    }


def parse_form_into_dict(body, content_type):
    multipart_data = decoder.MultipartDecoder(
        body.encode('utf-8'), content_type, "utf-8")

    def parse_headers(headers):
        regex = r"form-data; name=\"(.*)\""
        match = re.search(
            regex, headers["Content-Disposition".encode("utf-8")].decode('utf-8'))
        if match:
            return match.group(1)

        return None

    values = dict()
    for part in multipart_data.parts:
        # Alternatively, part.text if you want unicode
        key = parse_headers(part.headers)
        value = part.text
        values[key] = value

    return values


def handle_slash_command(body, content_type):
    form_data = parse_form_into_dict(body, content_type)
    print(form_data)
    return {
        "statusCode": 500,
        "body": "finished slash command"
    }


def lambda_handler(data, context):
    """Handle an incoming HTTP request from a Slack chat-bot.
    """

    print("Data", data)
    print(type(data))

    body = data["body"]
    path = data["path"]
    pathParameters = data["pathParameters"]
    queryStringParameters = data["queryStringParameters"]

    print(body, path)

    if "challenge" in data:
        return {
            "statusCode": 200,
            "body": data["challenge"]
        }

    print("=================================")
    try:
        if path == '/slack-bot-event-handler':
            return handle_bot_event(body)
        elif path == '/holdthisbook':
            return handle_slash_command(body, data['headers']['Content-Type'])
        else:
            return {
                "statusCode": 400,
                "body": "path <{0}> not found".format(path)
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": "Error: " + repr(e) + traceback.format_exc()
        }
