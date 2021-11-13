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
    
    return app
