import json

from flask import Flask, request, jsonify
from flask_restx import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import re


# --------------------------------------------------------------------------------------------------
# Initialise the flask framework
# Create a new db with sqlAlchemy track notification disabled
# --------------------------------------------------------------------------------------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///z3457800.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app, title='Assignemnt2', default ='Api list for questions', default_label='')
db = SQLAlchemy(app)

# --------------------------------------------------------------------------------------------------
# Create actors_info and show table in the db created earlier
# actors_info stores actors information
# --------------------------------------------------------------------------------------------------
class ActorsInfo(db.Model):
    __tablename__ = 'actors_info'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, index=True)
    tvmaze_id = db.Column(db.Integer)
    name = db.Column(db.String(), unique=True, index=True)
    country = db.Column(db.String())
    birthday = db.Column(db.String())
    deathday = db.Column(db.String())
    gender = db.Column(db.String())
    last_update = db.Column(db.String())
    show = db.Column(db.String())


# --------------------------------------------------------------------------------------------------
# API for Q1
# --------------------------------------------------------------------------------------------------
def request_data(url):
    try:
        data = requests.get(url).json()
    except Exception:
        data = None
    return data

def check_vaild_name(input_name ,name_list):
    if not len(name_list):
        return False
    first_name = ''.join(re.findall('[A-Za-z0-9]', name_list[0]['person']['name'])).lower()
    input_name = ''.join(re.findall('[A-Za-z0-9]', input_name)).lower()
    return first_name == input_name

def get_show_list(id):
    show_pack = request_data(f'https://api.tvmaze.com/people/{id}/castcredits?embed=show')
    if not show_pack: return {}
    show_list = {}
    for item in show_pack:
        show_list[item['_embedded']['show']['id']] = item['_embedded']['show']['name']
    return show_list

@api.route('/actors',
           doc={'params': {'name': 'Actors_name, eg: Brad Pitt'},
                'responses': {200: 'OK', 201: 'Created',
                              400: 'Bad Request', 403: 'Forbidden',
                              404: 'Not Found'}
})
class Actors(Resource):
    def post(self):
        actor = request.args.get('name')
        actor_name = re.sub('-|_', ' ', actor)
        req_dict = request_data(f'https://api.tvmaze.com/search/people?q={actor_name}')
        if not req_dict: return  {'message': 'The actor is not found'}, 404
        if check_vaild_name(actor_name,req_dict):
            ac_info = req_dict[0]['person']
            if not ActorsInfo.query.get(ac_info['id']):
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                show_list = json.dumps(get_show_list(ac_info['id']))
                if ac_info['country']:
                    country = ac_info['country']['name']
                else:
                    country = None
                try:
                    data = ActorsInfo(tvmaze_id=ac_info['id'],
                                      name=ac_info['name'],
                                      country=country,
                                      birthday=ac_info['birthday'],
                                      deathday=ac_info['deathday'],
                                      gender=ac_info['gender'],
                                      last_update=now,
                                      show=show_list)
                    db.session.add(data)
                    db.session.commit()
                except Exception:
                    return {'message': 'Database Error'}, 403
                pack = {'id': ac_info['id'],
                        'last-update': str(now),
                        '_links': {'self': {
                            'href': 'http://127.0.0.1:5000/actors/{}'.format(ac_info['id'])
                        }}}
                return pack, 201
            else:
                return {'message': 'Actor already in database'}, 200
        else:
            return {'message': 'The actor is not found'}, 404


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)