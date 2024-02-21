import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import json


def get_config():
    with open("config.json") as fp:
        data = json.load(fp)
    return data

def send_mail(config=None, filename=None, path=None, comment=None, html=False):
    
    data = get_config() if not config else config
    
    if not comment:
        comment = data['comment']
    
    recipients = data['recipients'] if type(data['recipients']) == list else [data['recipients']]
    
    msg = MIMEMultipart()
    msg['From'] = data['sender_email']
    msg['To'] = ','.join(data['recipients'])
    msg['Subject'] = data['subject']

    # attach the body with the msg instance
    msg.attach(MIMEText(comment, 'plain' if not html else 'html'))

    if filename and path:
        attachment = open(path, "rb")

        # instance of MIMEBase and named as p
        p = MIMEBase('application', 'octet-stream')
        # To change the payload into encoded form
        p.set_payload((attachment).read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(p)
    
    s = smtplib.SMTP(data["smtp_url"], data["smtp_port"])
    s.set_debuglevel(1)
    s.starttls()
    
    # Authentication
    s.login(data['sender_email'], data['password'])
    s.sendmail(data['sender_email'], recipients, msg.as_string())

    print("Email(s) was sent successfully!")

    s.quit()