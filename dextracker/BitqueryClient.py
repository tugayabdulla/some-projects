import asyncio
import json
import math
import os
import re
from json import JSONDecodeError

import time
import httpx
import random

from bs4 import BeautifulSoup
from pyrogram.types import Message
from requests import get

from Web3Client import Web3Client
from dextools_client import DextoolsClient


class BitqueryClient:
    def __init__(self):
        self.API_KEYS = ['BQY1dHiCM958aOaSqyqUki3CLiKOg7zv', 'BQYEipjkQTB8wPX7fTVENFVhqHjmA2mi',
                         'BQYOThvDWpxDPaUwHs87ZC4DPksJ2Nmu', 'BQYLsLf591LNRhPguyIlfasRXyo8YyPw',
                         'BQY4pogPwLbjFObxeYApzAiO7OKiY7VJ', 'BQYtBdXk8vRBMiDnbCrFgZgHW2BSr6yc',
                         'BQYuCzOWqj1t4S2Yyba1H1Rlk00LWZGl', 'BQYgwNNR55Svz3xxjkazRXDxBjSZODUn',
                         'BQYMlAQcRc4YY4yU7VuLfa0SVVynLHo0', 'BQY153yo3W9yCUDaEYn1habkUdka82a9',
                         'BQYHcDzXjo3ujgsL3tEc8THAt42siSin', 'BQYZG4IzURqWJuDKwo9BTefRyK744MM5',
                         'BQYGEKp8i4pCFuMSHVDI9vdAVs2hol1S', 'BQYY87emllk8wmTAzass1FVJzWnouhfZ',
                         'BQYlt8y7QZOtq0aFWP7mqc4xVKzvMtlf', 'BQYlVJomjb659nUaZMzANKYP6W8hxhm8',
                         'BQYsQQMZddMQ8k95K6NAzrKSOQJ8PZvX', 'BQY9N6XN9MDNOQonYgwJSjicCdszEhEC',
                         'BQYyipbOqimouHBw9ER7e9SUVwkO0Kdm', 'BQYOyGrDHp7lhN2YlzwursoiES2kKAZV']

        self.async_http_client = httpx.AsyncClient(timeout=30)
        proxy_url = 'https://proxy.webshare.io/proxy/list/download/drklsfqyxfklvdorcvuutcxfczlketipwlksxhlh/-/http/username/direct/'
        r = get(proxy_url)
        proxies = r.text.strip().split('\r\n')
        proxy_list = []
        for p in proxies:
            ip, port, username, password = p.split(':')
            proxy_list.append(f'http://{username}:{password}@{ip}:{port}')
        self.proxy_list = proxy_list
        self.dxt = DextoolsClient()
        self.web3 = Web3Client()

    async def make_request_grapql(self, query: str, variables=None, API_KEY=None):
        if API_KEY is None:
            API_KEY = random.choice(self.API_KEYS)

        headers = {'X-API-KEY': API_KEY}
        if variables is None:
            variables = {}
        while True:
            try:
                request = await self.async_http_client.post('https://graphql.bitquery.io/',
                                                            json={'query': query, 'variables': variables},
                                                            headers=headers, timeout=120)
                return request.json()
            except JSONDecodeError:
                print(query)
                await asyncio.sleep(1)
            except KeyError:
                print(query)
                await asyncio.sleep(1)

    async def fetch_trade_info(self, token_address: str, message: Message, chain: str, API_KEY=None):
        self.bnb_price = self.dxt.get_bnb_price()
        self.ether_price = self.dxt.get_ether_price()
        if chain == 'eth':
            chain = 'ethereum'
        balance_dict = await self.get_buy_trades(token_address, chain, API_KEY)
        # with open('buy_trades.json', 'w') as f:
        #     json.dump(balance_dict, f)
        try:
            await message.edit_text('Fetching sell trades...')
        except:
            pass
        balance_dict = await self.get_sell_trades_new(token_address, balance_dict, chain, API_KEY)
        # with open('sell_trades.json', 'w') as f:
        #     json.dump(balance_dict, f)
        try:
            await message.edit_text('Fetching price...')
        except:
            pass
        token_price, token_name, token_symbol, decimals, pair_str, liq_main = self.dxt.get_price(token_address, chain)
        pair_address, liquidity, mcap = self.dxt.get_pair_address(token_address, chain)
        image_path = self.dxt.create_chart(token_address, chain, pair_address)
        if image_path is None:
            image_pathes = []
        else:
            image_pathes = [image_path]
        try:
            await message.edit_text('Fetching holders...')
        except:
            pass
        holders = self.get_holders_count(token_address, chain, decimals)
        # with open('holders.json', 'w') as f:
        #     json.dump(holders, f)
        # holders = await self.get_holders(token_address, chain, API_KEY)

        try:
            await message.edit_text('Calculating...')
        except:
            pass
        base_currency_price = self.bnb_price if chain == 'bsc' else self.ether_price
        # holders = {k: v for k, v in holders.items() if v > 0}
        new_balance_dict = {}
        for address in balance_dict:
            if holders.get(address, 0) == 0:
                continue
            new_balance_dict[address] = balance_dict[address] + holders[address] * token_price / base_currency_price
        balance_dict = new_balance_dict

        if chain == 'bsc':
            chart_url = f'https://www.dextools.io/app/bsc/pair-explorer/{pair_address}'
            token_url = f'https://bscscan.com/token/{token_address}'
        else:
            chart_url = f'https://www.dextools.io/app/ether/pair-explorer/{pair_address}'
            token_url = f'https://etherscan.io/token/{token_address}'

        winners = losers = 0
        profit = loss = 0
        # with open('balance.json', 'w') as f:
        #     json.dump(balance_dict, f)
        for address in balance_dict:
            if balance_dict[address] > 0:
                winners += 1
                profit += balance_dict[address]
            else:
                loss -= balance_dict[address]
                losers += 1
        await message.delete()

        base_currency = 'BNB' if chain == 'bsc' else 'ETH'
        profit_factor = (winners / losers if losers != 0 else 1) * 100

        addition = self.dxt.get_tg_or_web(token_address, chain)

        with open('ads.json', 'r', encoding='utf-8') as f:
            ads_dict = json.load(f)
        if len(ads_dict) > 0:
            promotion = '🚀 <b>Promoted:</b>'
            for ad_ind in ads_dict:
                ad_text = ads_dict[ad_ind]['text']
                ad_image = ads_dict[ad_ind]['file_path']
                promotion += f' {ad_text}, '
            promotion += '\nContact @BuyHighSellLowQQ for promotions'
        else:
            promotion = '🚀 Promoted: Contact @BuyHighSellLowQQ'
        promotion = promotion.strip().strip(',')
        files = os.listdir('gifs')
        if len(files) == 1:
            file_path = 'ad.gif'
        else:
            for file in files:
                if file != 'default.mp4':
                    file_path = file
                    break

        try:
            supply = self.dxt.get_token_info(pair_address, chain)
            mcap = int(supply * token_price)
            mcap = f'${mcap:,}'
        except:
            mcap = f'${mcap:,}'
        honeypot_text, buy_sell_text = self.dxt.check_honeypot(token_address, chain)
        average_buy = await self.get_average_buy(token_address, chain, API_KEY)

        is_liqudity_locked = await self.check_liquidity_locked(pair_address, chain)
        if is_liqudity_locked:
            liquidity_locked_text = '🔒 Liquidity is locked'
        else:
            liquidity_locked_text = '🔓 Liquidity is not locked, be aware'
        text = f"""
<a href="http://dextrackerad.live/{file_path}">$</a>{token_symbol} ({token_name})

💵Price:  ${token_price:.10f} 
💎🤲Total # of Holders:    {len(balance_dict)}
💚{winners} are at profit with   {profit:.3f} {base_currency}
❤{losers} are at loss with     {loss:.3f} {base_currency}
💸Profit factor:                  {profit_factor:.2f}%
👨Trader/holder ratio:      {(winners + losers) / len(holders) * 100:.2f}%
💰Average Purchase:       ${average_buy:,.2f}
💦Liq {pair_str}:          ${liquidity:,} 
💎Market Cap:                    {mcap}  
{buy_sell_text}
{liquidity_locked_text}
<a href={token_url}>Token</a> | <a href={chart_url}>Chart</a> {addition}
{honeypot_text}

------------------
{promotion}
"""
        return text, image_pathes

    async def get_buy_trades(self, token_address: str, chain: str, API_KEY):

        query = """
query ($offset: Int!, $token: String!, $network: EthereumNetwork) {
  ethereum(network: $network) {
    dexTrades(sellCurrency: {is: $token}, options: {limit: 25000, offset: $offset}) {
      count
    }
  }
}
        """

        variables = {'token': token_address, 'offset': 0, 'network': chain}
        response = await self.make_request_grapql(query, variables, API_KEY)
        total_trades = response['data']['ethereum']['dexTrades'][0]['count']
        n_bulks = math.ceil(total_trades / 25000)
        query = """
query ($offset: Int!, $token: String!, $network: EthereumNetwork) {
  ethereum(network: $network) {
    dexTrades(sellCurrency: {is: $token}, options: {limit: 25000, offset: $offset}) {
      transaction {
        txFrom {
          address
        }
      }
      buyCurrency {
        name
      }
      buyAmount
    }
  }
}
        
"""

        buy_dict = {}
        # while True:
        #     variables = {'token': token_address, 'offset': offset, 'network': chain}
        #     response = await self.make_request_grapql(query, variables, API_KEY)
        #     trades = response['data']['ethereum']['dexTrades']
        #     all_trades.extend(trades)
        #     if len(trades) < 20000:
        #         break
        #     offset += 20000
        tasks = []
        for i in range(n_bulks):
            variables = {'token': token_address, 'offset': i * 25000, 'network': chain}
            task = self.make_request_grapql(query, variables, API_KEY)
            tasks.append(task)
        a = await asyncio.gather(*tasks)
        all_trades = []
        for i in a:
            all_trades.extend(i['data']['ethereum']['dexTrades'])
        for trade in all_trades:
            buyer_address = trade['transaction']['txFrom']['address']
            currency = trade['buyCurrency']['name']
            if buyer_address not in buy_dict:
                buy_dict[buyer_address] = 0
            buy_amount = trade['buyAmount']
            if currency == 'Wrapped Ether' or currency == 'Wrapped BNB':
                pass

            elif currency == 'BUSD Token':
                buy_amount /= self.bnb_price
            elif currency == 'Tether USD' or currency == 'USD//C':
                if chain == 'bsc':
                    buy_amount /= self.bnb_price
                else:
                    buy_amount /= self.ether_price
            else:
                continue
            buy_dict[buyer_address] -= buy_amount
        return buy_dict

    async def get_sell_trades_new(self, token_address: str, balance_dict: dict, chain: str, API_KEY):

        query = """
query ($offset: Int!, $token: String!, $network: EthereumNetwork) {
  ethereum(network: $network) {
    dexTrades(buyCurrency: {is: $token}, options: {limit: 25000, offset: $offset}) {
      count
    }
  }
}

        """
        variables = {'token': token_address, 'offset': 0, 'network': chain}
        response = await self.make_request_grapql(query, variables, API_KEY)
        total_trades = response['data']['ethereum']['dexTrades'][0]['count']
        n_bulks = math.ceil(total_trades / 25000)

        query = """
query ($offset: Int!, $token: String!, $network: EthereumNetwork) {
  ethereum(network: $network) {
    dexTrades(buyCurrency: {is: $token}, options: {limit: 25000, offset: $offset}) {
      transaction {
        txFrom {
          address
        }
      }
      buyCurrency {
        name
      }
      sellCurrency {
        name
      }
      buyAmount
      sellAmount
    }
  }
}
        
        """

        tasks = []
        for i in range(n_bulks):
            variables = {'token': token_address, 'offset': i * 25000, 'network': chain}
            task = self.make_request_grapql(query, variables, API_KEY)
            tasks.append(task)
        a = await asyncio.gather(*tasks)
        all_trades = []
        for i in a:
            all_trades.extend(i['data']['ethereum']['dexTrades'])
        for trade in all_trades:
            buyer_address = trade['transaction']['txFrom']['address']
            currency = trade['sellCurrency']['name']
            if buyer_address not in balance_dict:
                continue
            sell_amount = trade['sellAmount']
            if currency == 'Wrapped Ether' or currency == 'Wrapped BNB':
                pass
            elif currency == 'BUSD Token':
                sell_amount /= self.bnb_price
            elif currency == 'Tether USD' or currency == 'USD//C':
                if chain == 'bsc':
                    sell_amount /= self.bnb_price
                else:
                    sell_amount /= self.ether_price
            else:
                continue
            balance_dict[buyer_address] += sell_amount
        return balance_dict

    async def get_holders(self, token_address: str, network: str, API_KEY):
        query = """query ($offset:Int!, $token:String!, $network:EthereumNetwork) 
        
 {
  ethereum(network: $network) {
    transfers(
      currency: {is :$token}
      options: { limit: 25000, offset: $offset }
    ) {

      receiver{
        address
      }
      amount
    }
  }
}
"""
        offset = 0
        holders = {}
        all_transfers = []
        while True:
            variables = {'token': token_address, 'offset': offset, 'network': network}
            response = await self.make_request_grapql(query, variables, API_KEY)
            transfers = response['data']['ethereum']['transfers']
            all_transfers.extend(transfers)
            if len(transfers) < 25000:
                break
            offset += 25000

        for transfer in all_transfers:
            address = transfer['receiver']['address']
            if address not in holders:
                holders[address] = 0
            holders[address] += transfer['amount']

        query = """query ($offset:Int!, $token:String!, $network:EthereumNetwork) 

         {
          ethereum(network: $network) {
            transfers(
              currency: {is :$token}
              options: { limit: 25000, offset: $offset }
            ) {

              sender{
                address
              }
              amount
            }
          }
        }
        """
        all_transfers = []
        while True:
            variables = {'token': token_address, 'offset': offset, 'network': network}
            response = await self.make_request_grapql(query, variables, API_KEY)
            transfers = response['data']['ethereum']['transfers']
            all_transfers.extend(transfers)
            if len(transfers) < 25000:
                break
            offset += 25000

        for transfer in all_transfers:
            address = transfer['sender']['address']
            if address not in holders:
                holders[address] = 0
            holders[address] -= transfer['amount']

        return holders

    async def check_api_key(self, API_KEY):
        client = httpx.AsyncClient()

        query = """{
  ethereum(network: ethereum) {
    address(address: {is: "0x4319e7a95fd3f0660d25bc6a4ecdc0f3cb4200c5"}) {
      balances {
        currency {
          address
          symbol
          tokenType
        }
        value
      }
    }
  }
}
"""
        headers = {"X-API-KEY": API_KEY}
        request = await self.async_http_client.post('https://graphql.bitquery.io/',
                                                    json={'query': query}, headers=headers)
        try:
            response = request.json()
            address = response['data']['ethereum']['address']
            return True
        except:
            return False

    def get_holders_count(self, token_address: str, network: str, decimals):

        if network == 'bsc':
            holders = []
            for i in range(1, 100):
                url = f'https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress={token_address}&page={i}&offset=10000&apikey=36B9Q7MR9IVDIRWR5PWNA3313G9R1HBBGQ'
                r = get(url)
                n = r.json()['result']
                holders.extend(n)

                if len(n) != 10000:
                    break
            holders = {i['TokenHolderAddress']: float(i['TokenHolderQuantity']) * 10 ** (-decimals) for i in holders}


        else:
            url = f'https://ethplorer.io/service/service.php?refresh=holders&data={token_address}&page=tab%3Dtab-holders%26pageSize%3D100000&showTx=all'
            r = get(url)
            holders = r.json()['holders']
            holders = {i['address']: float(i['balance']) * 10 ** (-decimals) for i in holders}
        return holders

    async def get_average_buy(self, token_address: str, network: str, API_KEY):
        query = """
query ($offset: Int!, $token: String!, $network: EthereumNetwork) {
  ethereum(network: $network) {
    dexTrades(sellCurrency: {is: $token}, options: {limit: 25000, offset: $offset}) {
      count
      tradeAmount(in: USD, calculate: average)
    }
  }
}
"""
        variables = {'token': token_address, 'offset': 0, 'network': network}
        response = await self.make_request_grapql(query, variables, API_KEY)
        average_buy = response['data']['ethereum']['dexTrades'][0]['tradeAmount']
        return average_buy

    async def check_liquidity_locked(self, pair: str, network: str, ):
        liq_holders = self.get_holders_count(pair, network, 0)
        max_liq_holder = max(liq_holders, key=liq_holders.get)
        is_contract = self.web3.check_is_contract(max_liq_holder, network)
        return is_contract
