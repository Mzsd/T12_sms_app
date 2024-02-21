from src.mlog import Mlog
from glob import glob
from src.filter import Filter

import os
import requests
import pandas as pd


class SmsSender(Mlog):
    
    def __init__(self, *args, config_file:str=None) -> None:
        super().__init__(*args)
        if config_file:
            self.config = self.get_json_data(config_file)

    def __fetch_orders(self, orders_filter_payload:Filter) -> pd.DataFrame:
        
        query = "ch.logobject.dart.unitymedia.taskManagement.QrUMOrderOverview"
        url = f'https://mlog.unitymedia.de/queryExecution/queryExecution;{query}'
        orders_request = requests.post( url,
            headers=self.headers['headers'],
            data=orders_filter_payload,
            verify=False
        )

        order_columns = [colid['name'] for colid in orders_request.json()['metadata']]
        order_data = orders_request.json()['data']

        orders = self.generate_records({col: [] for col in order_columns}, order_data)
        orders_df = pd.DataFrame(orders)

        return orders_df

    def __request_api(self, query:str, payload:str, headers:dict) -> requests.models.Response:
        params = {
            'timeout': '60000',
        }
        url = f'https://mlog.unitymedia.de/jmsbridge/jms/{query}'
        request = requests.post( url,
            headers=headers,
            data=payload.encode(),
            params=params,
        )
        
        return request
    
    def fetch_data(self):
        
        self.filter_folder = "filters"
        self.output_folder = "Output_Files"
        
        filters = [os.path.split(f)[-1] for f in glob(os.path.join(self.filter_folder, "*.xml"))]
        filters_to_select = self.config['filters'] if 'filters' in self.config else None
        common_filters = list(set(filters) & set(filters_to_select)) if filters_to_select else filters
        
        order_login_details = {
            "username": self.config['user'],
            "token": self.session,
            "profile": self.profile,
        }
        
        login_details = {
            "username": self.config['user'],
            "token": self.session,
            "userprofile": self.profile,
        }
        
        for filter in common_filters:
            filter_payload = self.load_request_payload(os.path.join(self.filter_folder, filter))
            orders_filter_payload = Filter(order_login_details, filter_payload).get_filter()
            
            self.orders_df = self.__fetch_orders(orders_filter_payload)            
            
            for _, row in self.orders_df.iterrows():
                print("\n")
                print("[+] TaskID:", row['TASKID'])
                print("[+] Phone:", row['PHONE2'])
                for k, stage in enumerate(self.config['stages_sms']):
                    
                    stage_payload = self.load_request_payload(os.path.join(self.filter_folder, stage))
                    
                    sms_stage_obj = Filter(login_details, stage_payload)
                    sms_stage_payload = sms_stage_obj.get_filter(orders_flag=False)
                    
                    query = sms_stage_obj.get_tag_value({"type"}).string
                    
                    phone_field = sms_stage_obj.get_tag_value(
                        {
                            'name': 'field', 
                            'attrs': {
                                'name': 'mobileNumbers'
                            }
                        }
                    )
                    
                    taskid_field = sms_stage_obj.get_tag_value(
                        {
                            'name': 'field', 
                            'attrs': {
                                'name': 'taskId'
                            }
                        }
                    )
                    
                    if phone_field:
                        phone_field.attrs['value'] = f"{{{row['PHONE2']}}}"
                        
                    taskid_field.attrs['value'] = f"{row['TASKID']}"
                    
                    sms_req = self.__request_api(query, 
                                    str(sms_stage_payload), 
                                    self.headers['headers'])

                    if k == 1 and sms_req.status_code == 200:
                        print(f"[+] SMS Sent Successfully!")

                    if sms_req.status_code != 200:
                        print(f"[-] SMS Sending Stage {k+1}: Failed!")
                        
                    