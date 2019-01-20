from urllib.parse import parse_qs
import logging
import spl_util
import json


def handle_slash_command(body):
    logging.info("==== Hold my book event ======")
    params = parse_qs(body)
    text = params["text"][0]

    spli, neededPriming = spl_util.get_spli()
    if neededPriming:
        return {
            "statusCode": 200,
            "body": "command needed to be primed please retry"
        }

    book_id = spl_util.get_book_id_from_url(text)
    print(book_id)

    if book_id is None:
        return {
            "statusCode": 200,
            "body": "invalid url"
        }
    logging.info("got book id " + book_id)

    print("started response")
    response = spli.place_hold(book_id)
    print(response.content)

    responsJson = json.loads(response.text)
    return {
        "statusCode": 200,
        "body": "{0}\n{1}".format(responsJson["messages"][0]["key"], response.text)
    }
