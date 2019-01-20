"""
Slack chat-bot Lambda handler.
"""

import logging
import traceback

import bot
import slash_commands

logging.getLogger().setLevel(logging.INFO)


# Define the URL of the targeted Slack API resource.
# We'll send our replies there.


def lambda_handler(data, context):
    """Handle an incoming HTTP request from a Slack chat-bot.
    """

    print("Data", data)

    body = data["body"]
    path = data["requestContext"]["resourcePath"]
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
            return bot.handle_bot_event(body)
        elif path == '/holdthisbook':
            return slash_commands.handle_slash_command(body)
        else:
            return {
                "statusCode": 400,
                "body": "path <{0}> not found".format(path)
            }
    except Exception as e:
        logging.exception("message")
        return {
            "statusCode": 500,
            "body": "Error: " + repr(e) + traceback.format_exc()
        }
