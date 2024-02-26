from bs4 import BeautifulSoup as bs4

import xmltodict
import requests
import json
import os


class Mlog():

    def __init__(self) -> None:
        config_path = os.path.join(os.getcwd(), "configs", "config.json")
        self.config = self.get_json_data(config_path)
        self.headers = self.get_json_data("payload_data.json")
        self.authenticate()

    # Load xml file into beautifulSoup object
    def load_request_payload(self, filename):
        with open(filename) as f:
            data = bs4(f.read(), 'xml')
        return data

    def make_path(self, folder):
        if not os.path.exists(folder):
            os.mkdir(folder)

    # Return json dictionary
    def get_json_data(self, filename):
        with open(filename) as fp:
            json_dict = json.load(fp)
        return json_dict

    def generate_records(self, order_dict, data):
        for row in data:
            idx = 0
            for k, col in enumerate(order_dict):
                if idx + 1 >= len(row):
                    order_dict[col].append('')
                elif int(row[idx]['colid']) == k+1:
                    order_dict[col].append(row[idx]['value'])
                    idx += 1
                elif int(row[idx]['colid']) > k+1:
                    order_dict[col].append('')

        return order_dict

    def authenticate(self):

        data =  {
            "username": self.config['user'],
            "password": self.config['passw'],
            "client": "mRIC"
        }

        auth_requests = requests.post(  "https://mlog.unitymedia.de/getprofiles/ajax-getprofiles", 
                                        data=data, 
                                        headers=self.headers['headersAuthentication'],
                                        verify=False)
        
        text_dict = xmltodict.parse(auth_requests.text)
        self.session = text_dict['profiles']['session']
        self.profile =  text_dict['profiles']['profile'][-1] \
                        if type(text_dict['profiles']['profile']) == list \
                        else text_dict['profiles']['profile']

    def fetch_data(self):
        pass