from requests import get
from fake_headers import Headers
import math
from datetime import datetime, timezone, timedelta
import os
import mplfinance as fplt
from matplotlib import pyplot as plt

import numpy as np
import pandas as pd

h = Headers(headers=True)


class DextoolsClient:
    def __init__(self):
        pass

    def get_price(self, token, chain):
        token = token.lower()
        if chain == 'bsc':
            chain = 'chain-bsc'
        else:
            chain = 'chain-ethereum'
        url = f'https://www.dextools.io/{chain}/api/pair/search?s={token}'
        r = get(url, headers=h.generate())

        if chain == 'chain-bsc':
            for i in r.json():
                if not i['exchange'].startswith('dex'):
                    pair = i
                    break
            else:
                pair = r.json()[0]
        else:
            pair = r.json()[0]
        price = pair['price']
        token1 = pair['token1']
        token0 = pair['token0']
        if token0['id'] == token:
            token_info = token0
            liq_amount = pair['reserve1']
            liq_name = token1['symbol']
        else:
            token_info = token1
            liq_amount = pair['reserve0']
            liq_name = token0['symbol']
        token_name = token_info['name']
        token_symbol = token_info['symbol']
        token_decimals = token_info['decimals']

        return price, token_name, token_symbol, token_decimals, f"{token0['symbol']}/{token1['symbol']}", f"{liq_amount:,.2f} {liq_name}"

    def get_bnb_price(self):
        price, _, _, _, _, _ = self.get_price('0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c', 'bsc')
        return price

    def get_ether_price(self):
        price, _, _, _, _, _ = self.get_price('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'ethereum')
        return price

    def get_pair_address(self, token, chain):
        token = token.lower()
        if chain == 'bsc':
            chain = 'chain-bsc'
        else:
            chain = 'chain-ethereum'
        url = f'https://www.dextools.io/{chain}/api/pair/search?s={token}'
        r = get(url, headers=h.generate())
        print(r.text)
        if chain == 'chain-bsc':
            for i in r.json():
                if not i['exchange'].startswith('dex'):
                    pair = i
                    break
            else:
                pair = r.json()[0]
        else:
            pair = r.json()[0]

        return pair['id'], int(pair['liquidity']), int(pair.get('dilutedMarketCap', 0) or 0)

    def create_chart(self, token, chain, pair):
        if chain == 'bsc':
            exchange = 'Pancakeswap'
        else:
            exchange = 'Uniswap'
        utc_now = datetime.now(tz=timezone.utc)
        a_day_ago = (utc_now - timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        a_day_ago_timestamp = a_day_ago.timestamp() * 1000
        april_28 = 1651104000000
        utc_now_timestamp = utc_now.timestamp() * 1000
        past_weeks = math.ceil((utc_now_timestamp - april_28) / (86_400 * 7 * 1000))
        start_week = april_28 + (past_weeks - 2) * (86_400 * 7 * 1000)
        url = f'https://www.dextools.io/chain-{chain}/api/{exchange}/history/candles?sym=usd&span=week&pair={pair}&ts={start_week}'
        r = get(url, headers=h.generate())
        candles = r.json()['data']['candles']
        second_week = start_week + (86_400 * 7 * 1000)
        url = f'https://www.dextools.io/chain-{chain}/api/{exchange}/history/candles?sym=usd&span=week&pair={pair}&ts={second_week}'
        r = get(url, headers=h.generate())
        candles.extend(r.json()['data']['candles'])
        five_minute_candles = []
        last_range = -1
        candle_dict = {}
        close = -1
        for candle in candles:
            if candle['time'] < a_day_ago_timestamp:
                continue
            candle_datetime = datetime.fromtimestamp(candle['time'] / 1000, tz=timezone.utc)
            current_range = candle_datetime.hour * 12 + candle_datetime.minute // 5
            if current_range != last_range:
                last_time = candle_dict.get('time', 0)
                if last_time == 0:
                    pass
                else:
                    last_datetime = datetime.fromtimestamp(last_time / 1000, tz=timezone.utc)
                    minutes = last_datetime.minute // 5
                    new_timestamp = last_datetime.replace(minute=minutes * 5).timestamp() * 1000
                    candle_dict['time'] = new_timestamp

                five_minute_candles.append(candle_dict)
                new_candle = {}
                if candle_dict.get('Close', -1) != -1:
                    new_candle['Open'] = candle_dict['Close']
                else:
                    new_candle['Open'] = candle['open']
                candle_dict = new_candle
                last_range = current_range
            candle_dict['Close'] = candle['close']
            candle_dict['High'] = max(candle['high'], candle_dict.get('High', -1))
            candle_dict['Low'] = min(candle['low'], candle_dict.get('Low', float('inf')))
            candle_dict['time'] = candle['time']
            # candle_dict['volume'] =  candle['volume'] + candle_dict.get('volume', 0)

        ind = 2
        while ind < len(five_minute_candles):
            current_candle = five_minute_candles[ind]
            current_candle_time = current_candle['time']
            prev_candle_time = five_minute_candles[ind - 1]['time']
            diff = int((current_candle_time - prev_candle_time) // 300000)
            price = current_candle['Open']
            for i in range(diff - 1):
                candle_dict = {'Open': price, 'Close': price, 'High': price, 'Low': price,
                               'time': prev_candle_time + 300000 * (i + 1)}
                five_minute_candles.insert(ind, candle_dict)
                ind += 1
            ind += 1

        for i in five_minute_candles:
            i['time'] = i.get('time', 0) / 1000

        df = pd.DataFrame(five_minute_candles)
        if df.shape[0] == 0:
            return None

        df = df[-96 * 3:]
        df['time'] = pd.to_datetime(df.time, unit='s')
        df = df.set_index('time')

        mc = fplt.make_marketcolors(up='#26A69A', down='#EF5350', edge='inherit', wick='inherit')
        s = fplt.make_mpf_style(base_mpf_style='charles', rc={'font.size': 6}, marketcolors=mc)
        fig = plt.figure(figsize=(18, 8), facecolor='#161825')

        ax = fig.add_subplot(1, 1, 1)
        ax.set_facecolor('#161825')
        ax.tick_params(axis='both', colors='#828490', length=0)

        mask = ((df.index.minute % 60 == 0) & (df.index.hour % 3 == 0))
        plt.setp(ax, xticks=np.where(mask)[0])
        plt.setp(ax.spines.values(), linestyle='--', linewidth=0.2, color='white')
        ax.grid(color='w', linestyle='--', linewidth=0.2)
        fplt.plot(
            df,
            type='candle',
            style=s,
            ax=ax
        )
        ax.set_ylabel('')
        ax.set_xticklabels([f'{i:02d}:00' for i in df[mask].index.hour], rotation=0)
        image_path = os.path.join('tokens', f'{pair}.png')
        plt.savefig(image_path, bbox_inches='tight')
        plt.close(fig)
        return image_path

    def get_tg_or_web(self, address: str, chain: str):
        if chain == 'bsc':
            exchange = 'Pancakeswap'
        else:
            exchange = 'Uniswap'
        url = f'https://www.dextools.io/chain-{chain}/api/{exchange}/token?address={address}'
        r = get(url, headers=h.generate())
        tg = r.json()['result'][0]['telegram']
        web = r.json()['result'][0]['website']
        links = ''
        if tg:
            links += f'| <a href="{tg}">Tg</a>'
        if web:
            links += f'| <a href="{web}">Web</a>'

        return links

    def get_token_info(self, pair: str, chain: str):

        if chain == 'bsc':
            exchange = 'Pancakeswap'
        else:
            exchange = 'Uniswap'
        url = f'https://www.dextools.io/chain-{chain}/api/{exchange}/poolx?pairSelected={pair}'
        r = get(url, headers=h.generate())
        pair_info = r.json()['data']['pair']['info']
        mcap = int(pair_info['marketCapFormatted'])
        mcap = f'${mcap:,}'
        supply = int(pair_info['totalSupplyFormatted'])
        return supply

    def check_honeypot(self, address: str, chain: str):
        if chain == 'bsc':
            url = f'https://aywt3wreda.execute-api.eu-west-1.amazonaws.com/default/IsHoneypot?chain=bsc2&token={address}'
        else:
            url = f'https://aywt3wreda.execute-api.eu-west-1.amazonaws.com/default/IsHoneypot?chain=eth&token={address}'
        r = get(url, headers=h.generate())
        is_honeypot = r.json()['IsHoneypot']
        buy_tax = r.json()['BuyTax']
        sell_tax = r.json()['SellTax']
        if is_honeypot:
            top_text = '🍯 Honeypot:  TRANSFER_FROM_FAILED 🤬\n----\nAlways DYOR. Since, Auto rugcheckers can\'t detect all scams'
        else:
            top_text = '🥳🎉 Does not seem like a honeypot. This can always change!\n----\nAlways DYOR. Since, Auto rugcheckers can\'t detect all scams'
        buy_sell_tax = f"""🔺Buy Tax:                            {buy_tax}%
🔻Sell Tax:                            {sell_tax}%
"""
        return top_text, buy_sell_tax
