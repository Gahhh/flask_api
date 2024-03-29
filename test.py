
import json

from flask import Flask, request, jsonify
from flask_restx import Resource, Api
from flask_sqlalchemy import SQLAlchemy
# import requests
# import time
# import re
#
# people_list = requests.get('https://api.tvmaze.com/people').json()
# for people in people_list:
#     requests.post(f'http://127.0.0.1:5000/actors?name={people["name"]}')
import requests
import numpy as np
import json


def add_database(route):
    actor_id_list = np.random.choice(2000, 500, replace=False)
    for actor_id in actor_id_list:
        actor_url = 'https://api.tvmaze.com/people/' + str(actor_id)
        actor_info = requests.get(actor_url)
        if actor_info.status_code == 200:
            show_list_info = json.loads(actor_info.text)
            response = requests.post(route, {"name": show_list_info["name"]})
            print(response.json())


if __name__ == '__main__':
    # set url to your own route
    url = "http://127.0.0.1:5000/actors"
    add_database(url)