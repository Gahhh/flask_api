import requests
import numpy as np
import json


def add_database(route):
    actor_id_list = np.random.choice(300000, 500, replace=False)
    for actor_id in actor_id_list:
        print(actor_id)
        actor_url = 'https://api.tvmaze.com/people/' + str(actor_id)
        actor_info = requests.get(actor_url)
        if actor_info.status_code == 200:
            show_list_info = json.loads(actor_info.text)
            response = requests.post(route, {"name": show_list_info["name"]})
            print(response.json())


if __name__ == '__main__':
    # set url to your own route
    url = "http://192.168.50.204:8000/actors"
    add_database(url)