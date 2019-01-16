import boto3
import urllib


client = boto3.client('ssm')


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
slack_signing_secret = params["slack_signing_key"]
BOT_TOKEN = params["bot_token"]
SLACK_URL = "https://slack.com/api/chat.postMessage"


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
