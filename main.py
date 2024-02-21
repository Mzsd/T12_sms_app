import sys
import os

from src.sms_sender import SmsSender


def main():

    # Start fetching orders
    orders_object_created = False
    if len(sys.argv) > 1:
        config_path = os.path.join("configs", sys.argv[1])
        if os.path.exists(config_path):
            sms_orders = SmsSender(config_file=config_path)
            orders_object_created = True
            
    if not orders_object_created:
        sms_orders = SmsSender()

    sms_orders.fetch_data()


if __name__ == '__main__':
    main()