from flask import Flask, request, jsonify
from pymongo import MongoClient
    
from bson import json_util

import isodate

import os
import datetime
import json

def create_app():
    app = Flask(__name__)

    db = MongoClient('mongo', 27017, username=os.environ['MONGO_USER'], password=os.environ['MONGO_PASSWORD']).db

    def get_most_recent():
        return db.stats.find().sort([('timestamp', -1)]).limit(1)[0]

    @app.route("/")
    def home():
        start = request.args.get('start', isodate.datetime_isoformat(datetime.datetime.today() - datetime.timedelta(days=7)))
        end = request.args.get('end', None)
        filter = {}
        if start:
            filter.setdefault('timestamp', {})['$gte'] = isodate.parse_datetime(start)
        if end:
            filter.setdefault('timestamp', {})['$lt'] = isodate.parse_datetime(end)
        result = db.stats.find(filter)
        return json.dumps([r for r in result], default=str)
    
    @app.route("/circulating-supply")
    def circulating_supply():
        return str(get_most_recent()['supply']['circulating'])
    
    @app.route("/total-supply")
    def total_supply():
        return str(get_most_recent()['supply']['total'])


    return app
