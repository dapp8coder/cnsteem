import os
import requests


def send_to_slack(name, email, confirm_code):
    data = "Name: %s \n Email: %s \n ConfirmID: %s \n Platform: CNsteem" % (name, email, confirm_code)
    requests.post(os.environ.get('SLACK_URL'), json={"text": data})

