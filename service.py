import json
from datetime import datetime
from flask import Flask, request
from flask_restx import Resource, Api, fields, reqparse
from flask_sqlalchemy import SQLAlchemy
import requests
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
# Create the arguments for each api
# --------------------------------------------------------------------------------------------------
q1_name = reqparse.RequestParser()
q1_name.add_argument('name', type=str, help='Actors_name, eg: Brad Pitt', required=True)

q4_payload = api.model('Resource', {
    "name": fields.String(example="Jones Smith"),
    "country": fields.String(example="America"),
    "birthday": fields.String(example="1979-07-17"),
    "deathday": fields.String(example="2021-04-24"),
    "shows": fields.List(fields.String,example=['show1', 'show2', 'show3'])
})

q5_param = reqparse.RequestParser()
q5_param.add_argument('order', type=str, help="Attribute names with signal of + -, eg: +name,+id")
q5_param.add_argument('page', type=int, help="Which page to display, eg: 1")
q5_param.add_argument('size', type=int, help="Shows the number of actors per page, eg: 1")
q5_param.add_argument('filter', type=str, help="Shows what attribute should be shown for each actor, eg: id,name")

q6_param = reqparse.RequestParser()
q6_param.add_argument('format', type=str,
                      help='The expected output format, can be either "json" or "image"', required=True)
q6_param.add_argument('by', type=str,
                      help="Actor's attributes, can only be chosen from the list [country, birthday, gender, and life_status]",
                      required=True)

# --------------------------------------------------------------------------------------------------
# Create actors_info and show table in the db created earlier
# actors_info stores actors information
# --------------------------------------------------------------------------------------------------
class ActorsInfo(db.Model):
    __tablename__ = 'actors_info'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True, index=True)
    tvmaze_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String())
    country = db.Column(db.String())
    birthday = db.Column(db.DateTime())
    deathday = db.Column(db.DateTime())
    gender = db.Column(db.String())
    last_update = db.Column(db.DateTime(), default=datetime.now())
    shows = db.Column(db.String())


# --------------------------------------------------------------------------------------------------
# Utility functions
# --------------------------------------------------------------------------------------------------

def host_port():
    url = request.host_url
    host = re.findall('/([0-9.]+?):', url)
    port = re.findall(':([0-9]+?)/', url)
    return ''.join(host), ''.join(port)

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
    if not show_pack: return None
    show_list = []
    for item in show_pack:
        show_list.append(item['_embedded']['show']['name'])
    return '@%'.join(show_list)

def time_to_str(time_obj, is_Sec=False):
    if not time_obj: return None
    if is_Sec:
        return datetime.strftime(time_obj, "%Y-%m-%d %H:%M:%S")
    return datetime.strftime(time_obj, "%Y-%m-%d")

def str_to_time(str):
    if not str: return None
    return datetime.strptime(str, "%Y-%m-%d")

def create_response(actor):
    show_list = None
    if actor.shows:
        show_list = actor.shows.split('@%')
    host, port = host_port()
    links = {'self':{'href': f"http://{host}:{port}/actors/{actor.id}"}}
    next_link = ActorsInfo.query.order_by('id').filter(ActorsInfo.id > actor.id).first()
    prev_link = ActorsInfo.query.order_by(ActorsInfo.id.desc()).filter(ActorsInfo.id < actor.id).first()
    if prev_link:
        prev = f"http://{host}:{port}/actors/{prev_link.id}"
        links['previous'] = {'href': prev}
    if next_link:
        next = f"http://{host}:{port}/actors/{next_link.id}"
        links['next'] = {'href': next}
    pack = {'id': actor.id, 'last-update': time_to_str(actor.last_update, True),
            'name': actor.name, 'country': actor.country,
            'birthday': time_to_str(actor.birthday), 'deathday': time_to_str(actor.deathday),
            'shows': show_list,
            '_links': links}
    return pack

# --------------------------------------------------------------------------------------------------
# API for Q1 and Q5
# --------------------------------------------------------------------------------------------------
@api.route('/actors')
class Actors(Resource):

    @api.expect(q1_name)
    @api.doc(responses={200: 'OK', 201: 'Created', 403: 'Forbidden', 404: 'Not Found'},
             description='create an actor data in database, return the id of the actor and its link,\n'
                         'sample return: \n{"id" : 123,  "last-update": "2021-04-08-12:34:40", '
                         '"_links": {"self": {"href": "http://[HOST_NAME]:[PORT]/actors/123"}} }')
    def post(self):
        """Question 1 Create an Actor in database
        """
        actor = q1_name.parse_args()['name']
        actor_name = re.sub('-|_', ' ', actor)
        req_dict = request_data(f'https://api.tvmaze.com/search/people?q={actor_name}')
        if not req_dict: return  {'message': 'The actor is not found'}, 404
        if check_vaild_name(actor_name,req_dict):
            ac_info = req_dict[0]['person']
            show_list = get_show_list(ac_info['id'])
            birthday, deathday = None, None
            if ac_info['birthday']:
                birthday = datetime.strptime(ac_info['birthday'], '%Y-%m-%d')
            if ac_info['deathday']:
                deathday = datetime.strptime(ac_info['deathday'], '%Y-%m-%d')
            if ac_info['country']:
                country = ac_info['country']['name']
            else:
                country = None
            now = datetime.now()
            try:
                data = ActorsInfo(tvmaze_id=ac_info['id'],
                                  name=ac_info['name'],
                                  country=country,
                                  birthday=birthday,
                                  deathday=deathday,
                                  gender=ac_info['gender'],
                                  last_update=now,
                                  shows=show_list)
                db.session.add(data)
                db.session.commit()
                host, port = host_port()
                pack_id = ActorsInfo.query.filter(ActorsInfo.tvmaze_id==ac_info['id']).first().id
                pack = {'id': pack_id,
                        'last-update': str(datetime.strftime(now, "%Y-%m-%d %H:%M:%S")),
                        '_links': {'self': {
                            'href': f"http://{host}:{port}/actors/{pack_id}"
                        }}}
                return pack, 201
            except:
                return {'message': 'Actor already in database'}, 200
        else:
            return {'message': 'The actor is not found'}, 404

    @api.expect(q5_param)
    @api.doc(responses={200: 'OK', 400: 'Bad Request', 404: 'Not Found'},
             description='The inputs of order and filter can be only chosen from the following list: '
                         ' {id, name, country, birthday, deathday, last-update}')
    def get(self):
        """Question 5 Retrieve the list of available Actors
        """
        try:
            data = q5_param.parse_args()
            order = ['+id']
            page = 1
            size = 10
            db_finder = {'id': 'ActorsInfo.id', 'name': 'ActorsInfo.name',
                         'country': 'ActorsInfo.country', 'birthday': 'ActorsInfo.birthday',
                         'deathday': 'ActorsInfo.deathday', 'last-update': 'ActorsInfo.last_update',
                         'last_update': 'ActorsInfo.last_update', 'shows': 'ActorsInfo.shows'}
            order_map = {'+': '.asc()', '-': '.desc()'}
            filter = ['id', 'name']
            if data['order']:
                order = data['order'].replace(' ', '').split(',')
            order_list = []
            for i in order:
                order_list.append(eval(db_finder[i[1:]] + order_map[i[0]]))
            if data['page']:
                page = data['page']
            if data['size']:
                size = data['size']
            if data['filter']:
                filter = data['filter'].replace(' ', '').split(',')
            filter_list = []
            for j in filter:
                filter_list.append(eval(db_finder[j]))
            db_result = ActorsInfo.query.with_entities(*filter_list).order_by(*order_list).paginate(page, size)
            actors_list = []
            for item in db_result.items:
                item_set = {}
                i = 0
                while i < len(filter):
                    item_set[filter[i]] = item[i]
                    if filter[i] == 'shows' and item[i]:
                        item_set[filter[i]] = item[i].split('@%')
                    if re.search('last[-_]update', filter[i]) and item[i]:
                        item_set[filter[i]] = time_to_str(item[i], True)
                    if filter[i] == 'deathday' and item[i]:
                        item_set[filter[i]] = time_to_str(item[i])
                    if filter[i] == 'birthday' and item[i]:
                        item_set[filter[i]] = time_to_str(item[i])
                    i+=1
                actors_list.append(item_set)
            host, port = host_port()
            link = {
                "self": {"href":
                             f"http://{host}:{port}/actors?order={','.join(order)}&page={page}&size={size}&filter={','.join(filter)}"},
                "next": {"href":
                             f"http://{host}:{port}/actors?order={','.join(order)}&page={page+1}&size={size}&filter={','.join(filter)}"}
            }
            if page > 1:
                link['previous'] = {"href":
                             f"http://{host}:{port}/actors?order={','.join(order)}&page={page-1}&size={size}&filter={','.join(filter)}"}
            pack = {"page": page, "page-size": size, "actors": actors_list, "_links": link}
            return pack, 200
        except:
            return {'message': 'Inputs is invalid'}, 400

# --------------------------------------------------------------------------------------------------
# API for Q2, Q3, Q4
# --------------------------------------------------------------------------------------------------

@api.route('/actors/<int:id>', methods=['DELETE', 'GET', 'PATCH'],
           doc={'params': {'id': "Actor's id, eg: 2"},
                'responses': {200: 'OK', 400: 'Bad Request', 404: 'Not Found'}
})
class Actors(Resource):
    @api.doc(description='This operation retrieves an actor by their ID (given in question 1 return).\n'
                         "The response of this operation will show an actor's details")
    def get(self, id):
        """Question 2 Retrieve an Actor
        """
        try:
            int(id)
            actor = ActorsInfo.query.get(id)
            if not actor:
                return {'message': 'The actor is not found'}, 404
            pack = create_response(actor)
            return pack, 200
        except Exception:
            return {'message': 'id can only be a number'}, 400

    @api.doc(description="This operation deletes an existing actor from the database.")
    def delete(self, id):
        """Question 3 Deleting an Actor
        """
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
            return {'message': 'Bad Request'}, 400

    @api.doc(description="This operation partially updates the details of a given Actor.\n"
                         "Sample output:\n"
                         '{"name": "Some One", \n"country": "Australia",\n"birthday": "1987-05-22",\n"deathday": null}')
    @api.expect(q4_payload, validate=True)
    def patch(self, id):
        """Question 4 Update an Actor
        """
        try:
            data = json.loads(request.data)
            actor = ActorsInfo.query.filter_by(id=id)
            isChanged = False
            for i in ['name', 'country', 'birthday', 'deathday', 'shows']:
                if data.get(i):
                    if i == 'birthday' or i == 'deathday':
                        actor.update({i: str_to_time(data[i])})
                        isChanged = True
                    elif i == 'shows':
                        actor.update({i: "@%".join(data[i])})
                        isChanged = True
                    else:
                        actor.update({i: data[i]})
                        isChanged = True
            if isChanged:
                now = datetime.now()
                actor.update({'last_update': now})
                db.session.commit()
                host, port = host_port()
                pack = {'id': id,
                        'last-update': str(datetime.strftime(now, "%Y-%m-%d %H:%M:%S")),
                        '_links': {'self': {
                            'href': f"http://{host}:{port}/actors/{id}"
                        }}}
                return pack, 200
            else:
                return {'message': 'No changes have been made.'}, 200
        except:
            return {'message': 'Input data is invalid'}, 400

# --------------------------------------------------------------------------------------------------
# API for Q6
# --------------------------------------------------------------------------------------------------

@api.route('/actors/statistics', doc={'responses': {200: 'OK', 400: 'Bad Request', 404: 'Not Found'}})
class Actors(Resource):
    @api.expect(q6_param)
    def get(self):
        """ Question 6  Get the statistics of the existing Actors
        """
        args = q6_param.parse_args()
        print(args)
        pass



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)