from flask import Flask, request, jsonify
from pymongo import MongoClient
    
from bson import json_util

import isodate

import os
import datetime
import json


hourly =   {
                '$group': {
                    '_id': { '$dateToString': { 'format': '%Y-%m-%d %H:00:00', 'date': '$timestamp' }},
                    'pool_liquidity': {'$avg': '$pool.liquidity'},
                    'pool_frkt': {'$avg': '$pool.frkt'},
                    'pool_sol': {'$avg': '$pool.sol'},
                    'pool_lp': {'$avg': '$pool.lp'},
                    'pool_h24_volume': {'$avg': '$pool.h24_volume'},
                    'pool_price': {'$avg': '$pool.price'},
                    'pool_apy': {'$avg': '$pool.apy'},
                    'supply_total': {'$avg': '$supply.total'},
                    'supply_burned': {'$avg': '$supply.burned'},
                    'supply_circulating': {'$avg': '$supply.circulating'},
                    'market_cap': {'$avg': '$market.cap'},
                    'market_diluated_cap': {'$avg': '$market.diluated_cap'},
                    'nft_stacked': {'$avg': '$nft.stacked'},
                    'nft_wallets': {'$avg': '$nft.wallets'},
                    'fraktion_lockedNFTs': {'$avg': '$fraktion.lockedNFTs'},
                    'fraktion_issuedTokens': {'$avg': '$fraktion.issuedTokens'},
                    'fraktion_TVL': {'$avg': '$fraktion.TVL'},
                    'holders': {'$avg': '$holders'}
                }
            }
project =   {
                '$project': {
                    'timestamp': '$_id',
                    'pool.liquidity': '$pool_liquidity',
                    'pool.frkt': '$pool_frkt',
                    'pool.sol': '$pool_sol',
                    'pool.lp': '$pool_lp',
                    'pool.h24_volume': '$pool_h24_volume',
                    'pool.price': '$pool_price',
                    'pool.apy': '$pool_apy',
                    'supply.burned': '$supply_burned',
                    'supply.total': '$supply_total',
                    'supply.circulating': '$supply_circulating',
                    'market.cap': '$market_cap',
                    'market.diluated_cap': '$market_diluated_cap',
                    'nft.stacked': '$nft_stacked',
                    'nft.wallets': '$nft_wallets',
                    'fraktion.lockedNFTs': '$fraktion_lockedNFTs',
                    'fraktion.issuedTokens': '$fraktion_issuedTokens',
                    'fraktion.TVL': '$fraktion_TVL',
                    'holders': 1
                }
            }

def create_app():
    app = Flask(__name__)

    db = MongoClient('mongo', 27017, username=os.environ['MONGO_USER'], password=os.environ['MONGO_PASSWORD']).db

    def get_most_recent():
        return db.stats.find().sort([('timestamp', -1)]).limit(1)[0]

    @app.route("/")
    def home():
        start = request.args.get('start', isodate.datetime_isoformat(datetime.datetime.today() - datetime.timedelta(days=10)))
        end = request.args.get('end', None)
        group = request.args.get('group', None)
        match = {'$match': {}}
        agg = []
        if start:
            match['$match'].setdefault('timestamp', {})['$gte'] = isodate.parse_datetime(start)
        if end:
            match['$match'].setdefault('timestamp', {})['$lt'] = isodate.parse_datetime(end)
        if match:
            agg.append(match)
        if group == 'hourly':
            agg.append(hourly)
            agg.append(project)
            agg.append({'$sort': {'timestamp': 1}})
        result = db.stats.aggregate(agg)
        return json.dumps(list(result), default=str)
    
    @app.route("/circulating-supply")
    def circulating_supply():
        return str(get_most_recent()['supply']['circulating'])
    
    @app.route("/total-supply")
    def total_supply():
        return str(get_most_recent()['supply']['total'])


    return app
