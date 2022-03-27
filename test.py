
import json

from flask import Flask, request, jsonify
from flask_restx import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import requests
import time
import re

people_list = requests.get('https://api.tvmaze.com/people').json()
for people in people_list:
    requests.post(f'http://127.0.0.1:5000/actors?name={people["name"]}')