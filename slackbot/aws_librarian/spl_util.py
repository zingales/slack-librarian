from bs4 import BeautifulSoup
import requests
import re
import lambda_util

spli = None

params = lambda_util.load_params("/spl/")
email = params["hold_email"]
username = params["username"]
password = params["password"]


def get_spli():
    global spli
    if spli is None:
        spli = SplInterface(email)
        spli.login(username, password)
        return spli, True

    # TODO check if still logged in if not re-login
    return spli, False


class SplInterface(object):

    def __init__(self, email):
        self.email = email

    def login(self, user_name, password):
        self.session = requests.Session()

        login_url = "https://seattle.bibliocommons.com/user/login?destination=/"

        r = self.session.get(login_url)
        soup = BeautifulSoup(r.text, 'html.parser')
        input = soup.find_all("input", {"name": "authenticity_token"})[0]
        auth_token = input["value"]

        # doc = html.fromstring(r.text)
        #
        # input = doc.xpath('//input[@name="authenticity_token"]')[0]
        # auth_token = input.value

        form_data = {
            "utf8": "✓",
            "authenticity_token": auth_token,
            "name": user_name,
            "user_pin": password,
            "local": "false"
        }

        r = self.session.post(login_url, data=form_data)

    def place_hold(self, book_id):
        # step 1 is we have to get the auth_token
        auth_token_url = "https://seattle.bibliocommons.com/holds/request_digital_title/{0}?hold_button_bundle=block_button".format(
            book_id)

        r = self.session.get(auth_token_url)

        soup = BeautifulSoup(r.json()['html'], 'html.parser')
        input = soup.find_all("input", {"name": "authenticity_token"})[0]
        auth_token = input["value"]

        placeHold_url = "https://seattle.bibliocommons.com/holds/place_digital_hold/{book_id}?utf8=✓&authenticity_token={auth_token}=&service_type=OverDriveAPI&auto_checkout=1&digital_email={email}&hold_button_bundle=block_button"

        url = placeHold_url.format(
            book_id=book_id, auth_token=auth_token, email=self.email)

        r = self.session.get(url)
        return r


def get_book_id_from_url(url):
    regex = r"https:\/\/seattle.bibliocommons.com\/item\/show\/(\d+)\S*"
    match = re.search(regex, url)
    if match:
        return match.group(1)

    return None
