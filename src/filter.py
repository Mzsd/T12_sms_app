from bs4 import BeautifulSoup as bs4


class Filter():

    def __init__(self, login_details:dict, payload:bs4) -> None:
        self.login_details = login_details
        self._payload = payload

    # Helper function - Modify tag values
    def modify_tag(self, tag, tag_string):
        if type(tag) == dict:
            self._payload.find(**tag).string = tag_string 
        else:
            self._payload.find(tag).string = tag_string

    # Helper function - Get tag value
    def get_tag_value(self, tag):
        return self._payload.find(**tag) if type(tag) == dict else self._payload.find(tag)

    ### PAYLOAD DATA ###
    def add_login_details(self, orders_flag:bool):
        if not orders_flag:    
            properties = self._payload.find("properties")
        
        for key, val in self.login_details.items():
            if orders_flag:
                self.modify_tag(key, val)
            else:
                property_elem = properties.find("property", {"name": key})
                if property_elem:
                    property_elem.attrs['value'] = val

    def remove_max_record_limit(self):
        m_rec = self._payload.find('maxRecord')
        if m_rec:
            m_rec.replaceWith('')

    # Return adjusted request payload
    def get_filter(self, orders_flag:bool=True):
        self.add_login_details(orders_flag)
        self.remove_max_record_limit()
        return self._payload