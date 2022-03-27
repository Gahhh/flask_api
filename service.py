import json

from flask import Flask, request, jsonify
from flask_restx import Resource, Api, fields
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import re


# --------------------------------------------------------------------------------------------------
# Initialise the flask framework
# Create a new db with sqlAlchemy track notification disabled
# --------------------------------------------------------------------------------------------------
default_host = '127.0.0.1'
default_port = 5000
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

# ------Utility Functions---------------------------------------------------------------------------
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
                'responses': {200: 'OK', 201: 'Created', 403: 'Forbidden', 404: 'Not Found'}
})
# ------------------------------------------------------------------------------------------------

# -----Main API function--------------------------------------------------------------------------

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
                            'href': f"http://{default_host}:{default_port}/actors/{ac_info['id']}"
                        }}}
                return pack, 201
            else:
                return {'message': 'Actor already in database'}, 200
        else:
            return {'message': 'The actor is not found'}, 404

# --------------------------------------------------------------------------------------------------
# API for Q2
# --------------------------------------------------------------------------------------------------
resource_fields = api.model('Resource', {
    "name": fields.String(example="Jones Smith"),
    "country": fields.String(example="America"),
    "birthday": fields.String(example="1979-07-17"),
    "deathday": fields.String(example="2021-04-24"),
    "shows": fields.List(fields.String,example=['show1', 'show2', 'show3'])
})

def create_response(actor):
    show_list = list(json.loads(actor.show).values())
    links = {'self':{'href': f"http://{default_host}:{default_port}/actors/{actor.id}"}}
    if ActorsInfo.query.get(int(actor.id) - 1):
        prev = f"http://{default_host}:{default_port}/actors/{int(actor.id)-1}"
        links['previous'] = {'href': prev}
    if ActorsInfo.query.get(int(actor.id) + 1):
        next = f"http://{default_host}:{default_port}/actors/{int(actor.id)+1}"
        links['next'] = {'href': next}
    pack = {'id': actor.id, 'last-update': actor.last_update,
            'name': actor.name, 'country': actor.country,
            'birthday': actor.birthday, 'deathday': actor.deathday,
            'shows': show_list,
            '_links': links}
    return pack

@api.route('/actors/<int:id>', methods=['DELETE', 'GET', 'PATCH'],
           doc={'params': {'id': "Actor's id, eg: 2"},
                'responses': {200: 'OK', 400: 'Bad Request', 404: 'Not Found'}
})
class Actors(Resource):
    def get(self, id):
        try:
            int(id)
            actor = ActorsInfo.query.get(id)
            if not actor:
                return {'message': 'The actor is not found'}, 404
            pack = create_response(actor)
            return pack, 200
        except Exception:
            return {'message': 'id can only be a number'}, 400

    def delete(self, id):
        try:
            int(id)
            actor = ActorsInfo.query.get(id)
            if not actor:
                return {'message': 'The actor is not in database'}, 404
            db.session.delete(actor)
            db.session.commit()
            return {'message': f'The actor with id {id} was removed from the database!',
                    'id': id}, 200
        except Exception:
            return {'message': 'id can only be a number'}, 400

    @api.doc(body=resource_fields)
    def patch(self, id):
        try:
            int(id)
            actor = ActorsInfo.query.get(id)
            if not actor:
                return {'message': 'The actor is not found'}, 404
            pack = create_response(actor)
            return pack, 200
        except Exception:
            return {'message': 'id can only be a number'}, 400




if __name__ == '__main__':
    db.create_all()
    app.run(host=default_host, port=default_port, debug=True)