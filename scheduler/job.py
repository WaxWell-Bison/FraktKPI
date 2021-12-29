from functools import lru_cache
from datetime import date, datetime

from pymongo import MongoClient

import json
import requests
import math
import os
import signal

team_address = [
    "JGPfKwykSgNJoPGSXD39ZxQtptGmHSvAiem7iRjK7sn", #Team locked
    "FGXMsYgfvk8pH6UpG4rNGfQznxYnfA2AjihCc9j1b54p", #Team locked
    "BawTL3vwEc3Aoi5mugwP6b7ZQ5dH5b7hfRKWDG7kZMc5", #Team locked
    "CaGvtrQj71GkY9RXHzDerhp7iKdBD8iVr6uWEhVuMcm", #FRKT-SOL Raydium farm
    "2fWTvWhYDQ7nEhweStAThXzBipDw9RuDw86Wb2R4Mu2c", #NFTs Staking reward
    "8JLnRhwckPfH9kG7LhKu4t3pPg1Y6rZJvuaNyAgC73b2", #Advisors allocation
    "5TPJHNJ4ZeJ6BSbZ83R4ZdA7R3Tsf3icgxQVaWjEExn7",  #FRKT-USDC Raydium farm
    "3NLY7Ww3HWCSogwL4zZmapSJQGrwMWinuMtyFM5vzCDg", #FRKT-USDC Aldrin farm
    "C2XYEYJKaqzqe1acqRmYiwhV3iviDetwUxJ4T3i2PhJM" #FRKT stacking
    ]

burn_address = "2F1r1go71SUK4N2rn4MYQ4N2ifmux8QUAuooHguTfK8S"
fusion_pool = "8inqBe7D12XJ6tMAzpLCGYpjazWFXG1Ue5q3UZ6X1FM3"
token_address = 'ErGB9xa24Szxbk1M28u2Tx8rKPqzL6BroNkkzk5rG4zj'

db = MongoClient('mongo', 27017, username=os.environ['MONGO_USER'], password=os.environ['MONGO_PASSWORD']).db

head = {
'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
}

def get_pool_data():
    to_return = {'h24_volume': 0, 'price': 0}
    markets = ["FRKT-USDC", "FRKT-SOL"]
    for pair in requests.get('https://api.raydium.io/pairs').json():
        if pair.get("market", "") == fusion_pool:
            to_return['price'] = pair['price']
        if pair.get("name","") in markets:
            to_return['h24_volume'] += pair['volume_24h']
    return to_return

def get_supply_data():
    def to_decimal(base, exp):
        return float(base) / math.pow(10, int(exp))

    def get_account_amount(account):
        amount = requests.get(f"https://api.solscan.io/account?address={account}", headers=head).json()['data']['tokenInfo']['tokenAmount']
        return to_decimal(amount['amount'], amount['decimals'])
    
    def get_total_supply(token_address):
        supply = requests.get(f"https://api.solscan.io/account?address={token_address}", headers=head).json()['data']['tokenInfo']
        return to_decimal(supply['supply'], supply['decimals'])

    tech_supply = get_total_supply(token_address)
    burned_supply = get_account_amount(burn_address)
    team_supply = sum([get_account_amount(wallet) for wallet in team_address])

    return {
        'burned': burned_supply,
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

def get_stakers_data():
    data = requests.get("https://frakt-stats.herokuapp.com/frkt-staking").json()
    return {
        'stakers': data['stakedWalletsCount'],
        'staked': data['stakedFRKT']
    }

def populate(sig=None,stack=None):
    data = {'pool':{}, 'supply':{}, 'market': {}, 'nft': {}, 'fraktion':{}, 'frkt': {}, 'timestamp': datetime.now()}

    data['pool'] = get_pool_data()

    data['holders'] = get_holders_data()

    data['nft'] = get_nft_data()
    data['fraktion'] = get_fraktion_data()
    data['frkt'] = get_stakers_data()
    data['supply'] = get_supply_data()
    data['supply']['circulating'] += data['frkt']['staked']
    data['market']['cap'] = data['supply']['circulating']  * data['pool']['price']
    data['market']['diluated_cap'] = data['supply']['total'] * data['pool']['price']

    db.stats.insert_one(data)

    print(f"{data}",flush=True)

if __name__ == "__main__":
    signal.signal(signal.SIGALRM, populate)
    signal.setitimer(signal.ITIMER_REAL, 1, 60)
    while True:
        signal.pause()