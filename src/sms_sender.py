from glob import glob
from src.mlog import Mlog
from src.filter import Filter

import os
import logging
import requests
import datetime
import pandas as pd
import src.email_sender as es


class SmsSender(Mlog):
    
    def __init__(self, *args, config_file:str=None) -> None:
        super().__init__(*args)
        if config_file:
            self.config = self.get_json_data(config_file)

        # Create a logs directory if it doesn't exist
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Set up logging configuration
        log_file = os.path.join(logs_dir, f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

        # Create a console handler and set its level to INFO
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create a formatter and add it to the console handler
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        # Add the console handler to the root logger
        logging.getLogger().addHandler(console_handler)

        
    def fetch_orders(self, orders_filter_payload:Filter) -> pd.DataFrame:
        logging.info("[+] Fetching Orders...")
        query = "ch.logobject.dart.unitymedia.taskManagement.QrUMOrderOverview"
        url = f'https://mlog.unitymedia.de/queryExecution/queryExecution;{query}'
        
        orders_request = requests.post(url, headers=self.headers['headers'], data=str(orders_filter_payload))

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
            
            filename = f'{datetime.datetime.utcnow().strftime("%y-%m-%d %H_%M_%S")}.xlsx'
            output_file_path = os.path.join(os.getcwd(), self.output_folder, filename)
            
            self.orders_df = self.fetch_orders(orders_filter_payload)            
            
            for _, row in self.orders_df.iterrows():
                logging.info("\n")
                logging.info(f"[+] TaskID: {row['TASKID']}")
                logging.info(f"[+] Phone: {row['PHONE2']}")
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
                        logging.info(f"[+] SMS Sent Successfully!")

                    if sms_req.status_code != 200:
                        logging.info(f"[-] SMS Sending Stage {k+1}: Failed!")
            
            output_folder_path = os.path.join(os.getcwd(), self.output_folder)
            if not os.path.exists(output_folder_path):
                os.makedirs(output_folder_path)
            
            self.orders_df.to_excel(output_file_path)
            
            es.send_mail(
                config=self.config,
                filename=filename + '.xlsx',
                path=os.path.join(os.getcwd(), output_file_path)
            )