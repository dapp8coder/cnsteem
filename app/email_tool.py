import sendgrid
import os
from sendgrid.helpers.mail import *


def send_email(to_email_address, link):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("cnsteem@gmail.com")
    to_email = Email(to_email_address)
    subject = "Steem注册"
    content = Content("text/plain", "注册链接：%s" % link)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())

    return response.status_code


def send_email_partiko(to_email_address, link):
    sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('PARTIKO_EMAIL_KEY'))
    from_email = Email("Partiko Team <signup@partiko.app>")
    to_email = Email(to_email_address)
    subject = 'Partiko Sign Up Link'
    content = Content("text/plain", "Sign up link：%s" % link)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    return response.status_code
