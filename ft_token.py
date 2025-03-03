# import json, os
import datetime
import json
from time import sleep

# import request_code
import requests
from hashlib import sha256
import request_code
from pathlib import Path
from api_helper import NorenApiPy


SCRIPT_PATH = str(Path(__file__).parent) + '/cred.json'


class FTToken:
    def __init__(self):
        self.api_key = ""
        self.api_url = ""
        self.token_url = ""
        self.redirected_url = ""
        self.request_code = ""
        self.user_id = ""
        self.passwd = ""
        self.secret_key = ""
        self.totp_key = ""
        self.get_cred()

    def get_cred(self):
        with open(SCRIPT_PATH) as f:
            data = json.load(f)
        self.api_key = str(data['flattrade']['api_key'])
        self.api_url = str(data['flattrade']['api_url'])
        self.token_url = str(data['flattrade']['token_url'])
        self.user_id = str(data['flattrade']['user_id'])
        self.passwd = str(data['flattrade']['password'])
        self.secret_key = str(data['flattrade']['secret_key'])
        self.totp_key = str(data['flattrade']['totp_key'])

    def generate_new_token(self):

        print("Please wait...Generating New Token")
        self.get_cred()

        self.redirected_url = request_code.get_redirect_url(self.api_url, self.user_id, self.passwd, self.totp_key)
        # print(self.redirected_url)

        self.request_code = self.redirected_url[self.redirected_url.find('=', 0) + 1:self.redirected_url.find("&", 0)]

        api_secret = self.api_key + self.request_code + self.secret_key
        encoded_api_secret = sha256(api_secret.encode('utf-8')).hexdigest()

        payload = {"api_key": self.api_key, "request_code": self.request_code, "api_secret": encoded_api_secret}
        response = requests.post(url=self.token_url, json=payload)

        # saving token for today.
        today = datetime.datetime.now()
        new_data = {'date': str(today.date()), 'token': response.json()['token']}

        return new_data

    def verify_token(self, token):
        api = NorenApiPy()
        _ = api.set_session(userid=self.user_id, password=self.passwd, usertoken=token)
        ret = api.get_limits()
        # print(ret)
        if "Not_Ok" in ret['stat']:
            return False
        else:
            return True


    def generate_token(self):
        try:
            with open("./session.json", "r") as f:
                data = json.load(f)
            today = datetime.datetime.now()
            if data['date'] != str(today.date()):
                data = self.generate_new_token()
                while not self.verify_token(data['token']):
                    print("Invalid Token... Generating New Token")
                    sleep(2)
                    data = self.generate_new_token()
                with open("./session.json", "w") as f:
                    json.dump(data, f, indent=4)
                return data['token']
            else:
                # print(data['token'])
                while not self.verify_token(data['token'].strip()):
                    print("Invalid Token... Generating New Token")
                    sleep(2)
                    data = self.generate_new_token()
                return data['token']

        except FileNotFoundError:
            data = self.generate_new_token()
            while not self.verify_token(data['token']):
                print("Invalid Token... Generating New Token")
                sleep(2)
                data = self.generate_new_token()
            # save new token
            with open("./session.json", "w") as f:
                json.dump(data, f, indent=4)
            return data['token']


# ft = FTToken()
# ft.generate_token()
# print(ft.user_id)
