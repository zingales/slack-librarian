from urllib.parse import parse_qs

import spl_util


def handle_slash_command(body):
    params = parse_qs(body)
    text = params["text"][0]

    book_id = spl_util.get_book_id_from_url(text)

    spli = spl_util.get_spli()
    response = spli.place_hold(book_id)

    return {
        "statusCode": 200,
        "body": "[{0}] - {1}".format(response.status_code, response.text)
    }
