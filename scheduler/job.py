from functools import lru_cache
from datetime import date, datetime

from pymongo import MongoClient

from ftx import Client

import json
import requests
import math
import os
import signal

team_wallet = [
    "DRHLza6iRbcFqujosgwnHiVxr2AMYdSaRHyFV4XVfG4c",
    "Ec93KxGJjwW6PBhiZQbVJrFst8mYbzBZ6embKf4Pxqus",
    "4BNZzYqB4M2oHTvWnn8ww8u5aosgjRTMQnv5WNikXLAf",
    "GwXKptwrXvFQ2VjcjXc9JwVzmAeGvPH9ogtq54AaDZcm",
    "BtgqY3wS4QiFVETAN3vQidPawaYweyGcrGmA9CcYDr4r",
    "4hMdAptCtcB3unnX1ucL6epVnpsCayGArg2iKPqCgohf",
    ]

burn_wallet = "1nc1nerator11111111111111111111111111111111"
fusion_pool = "FE5nRChviHFXnUDPRpPwHcPoQSxXwjAB5gdPFJLweEYK"
token_address = 'ErGB9xa24Szxbk1M28u2Tx8rKPqzL6BroNkkzk5rG4zj'

f_client = Client(os.environ['FTX_KEY'], os.environ['FTX_SECRET'])
db = MongoClient('mongo', 27017, username=os.environ['MONGO_USER'], password=os.environ['MONGO_PASSWORD']).db

head = {
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
}

def get_pool_data():
    for pair in requests.get('https://api.raydium.io/pairs').json():
        if pair.get("name","") == "FRKT-SOL" and pair.get("market","") == fusion_pool:
            return {
                'liquidity': pair['liquidity'],
                'frkt': pair['token_amount_coin'],
                'sol': pair['token_amount_pc'],
                'lp': pair['token_amount_lp'],
                'h24_volume': pair['volume_24h'],
                'price': pair['price'] * f_client.get_price_pair('SOL/USDT'),
                'apy': pair['apy']
            }

def get_supply_data():
    supply = requests.get(f"https://api.solscan.io/account?address={token_address}", headers=head).json()['data']['tokenInfo']
    tech_supply = float(supply['supply']) / math.pow(10, int(supply['decimals']))
    burned_supply = 0
    team_supply = 0

    for holder in requests.get(f"https://api.solscan.io/token/holders?token={token_address}&offset=0&size=20", headers=head).json()['data']['result']:
        if holder['owner'] in team_wallet:
            team_supply += float(holder['amount']) / math.pow(10,int(holder['decimals']))
        if holder['owner'] == burn_wallet:
            burned_supply = float(holder['amount']) / math.pow(10,int(holder['decimals']))

    return {
        'total': tech_supply - burned_supply,
        'circulating': tech_supply - burned_supply - team_supply
    }

def get_holders_data():
    return requests.get(f"https://api.solscan.io/token/meta?token={token_address}", headers=head).json()['data']['holder']

def get_nft_data():
    data = requests.get("http://frakt-stats.herokuapp.com/staking").json()
    return {
        'stacked': data['stakedNfts'],
        'wallets': data['uniqueWallets']
    }

def get_fraktion_data():
    return requests.get("http://frakt-stats.herokuapp.com/fraktion").json()


def populate(sig=None,stack=None):
    data = {'pool':{}, 'supply':{}, 'market': {}, 'nft': {}, 'fraktion':{}, 'timestamp': datetime.now()}

    data['pool'] = get_pool_data()
    data['supply'] = get_supply_data()

    data['holders'] = get_holders_data()
    data['market']['cap'] = data['supply']['circulating']  * data['pool']['price']
    data['market']['diluated_cap'] = data['supply']['total'] * data['pool']['price']

    data['nft'] = get_nft_data()
    data['fraktion'] = get_fraktion_data()

    db.stats.insert_one(data)

    print(f"{data}",flush=True)

signal.signal(signal.SIGALRM, populate)
signal.setitimer(signal.ITIMER_REAL, 1, 60)
while True:
    signal.pause()