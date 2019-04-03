import datetime
from email.mime.text import MIMEText
import smtplib


def send(config):
    smtp_server = config['smtp_server']
    smtp_user = config['smtp_user']
    smtp_pass = config['smtp_pass']
    addr_from = config['addr_from']
    recipients = config['recipients']
    try:
        s = smtplib.SMTP(smtp_server)
        s.starttls()
        s.login(smtp_user, smtp_pass)
        for recipient in recipients:
            time = datetime.datetime.now().strftime("%H:%M:%S")
            msg = MIMEText('Es hat gerade jemand geklingelt ({}).'.format(time))
            msg['From'] = addr_from
            msg['To'] = recipient
            msg['Subject'] = 'Klingeling'
            s.sendmail(addr_from, recipient, msg.as_string())
        s.quit()
    except Exception as e:
        logger.error(
            "There was an error sending the email. Check the smtp settings."
        )
        logger.error(str(e))
