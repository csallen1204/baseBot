import time
import os
import http.client
import json
import jwt
from cryptography.hazmat.primitives import serialization
import secrets
import websocket
import uuid

class coinbase:

    def __init__(self):
        self.HEADERS = {
            'Content-Type': 'application/json',
            'cache-control': 'no-cache'
        }
        self.COINBASE_DOMAIN = "api.coinbase.com"
        self.COINBASE_API_PATH = "/api/v3/brokerage/"
        self.API_KEY=os.environ['COINBASE_API_KEY']
        self.API_SECRET=os.environ['COINBASE_API_SECRET']

    def restApiCall(self,method="GET",path="",payload={},parameters=""):
        conn = http.client.HTTPSConnection(self.COINBASE_DOMAIN, 443)
        private_key = serialization.load_pem_private_key(self.API_SECRET.encode('utf-8'), password=None)
        jwt_token = jwt.encode(
            {
                'sub': self.API_KEY,
                'iss': "cdp",
                'nbf': int(time.time()),
                'exp': int(time.time()) + 120,
                'uri': f"{method} {self.COINBASE_DOMAIN}{self.COINBASE_API_PATH}{path}",
            },
            private_key,
            algorithm='ES256',
            headers={'kid': self.API_KEY, 'nonce': secrets.token_hex()},
        )
        self.HEADERS['Authorization'] = f"Bearer {jwt_token}"
        conn.request(method,self.COINBASE_API_PATH+path+parameters,json.dumps(payload),self.HEADERS)
        return json.loads(conn.getresponse().read().decode())

    def getPairs(self):
        pairData = self.restApiCall(path="products")['products']
        pairList = []
        for i in range(0,len(pairData)):
            if pairData[i]['trading_disabled']:
                continue
            if pairData[i]['quote_display_symbol'] == 'USD' and '-USDC' not in pairData[i]['product_id'] and pairData[i]['volume_24h'] != '':
                if (float(pairData[i]['volume_24h']) * float(pairData[i]['price'])) > 499999.9:
                    pairList.append(pairData[i])
        return pairList
    
    def getLikelyPumps(self):
        returnData = []
        pairs = self.getPairs()
        averagePastHrVol = 0.0
        last3minAverage = 0.0
        for item in pairs:
            time.sleep(.03)
            candles = self.restApiCall(path=f"products/{item['product_id']}/candles",parameters="?granularity=ONE_MINUTE")['candles']
            if len(candles) > 63:
                currentPrice = float(candles[0]['close'])
                threeMinAgoPrice = float(candles[3]['close'])
                for i in range(0,3):
                    last3minAverage = last3minAverage + float(candles[i]['volume'])
                last3minAverage = last3minAverage / 3
                for i in range(3,63):
                    averagePastHrVol = averagePastHrVol + float(candles[i]['volume'])
                averagePastHrVol = averagePastHrVol / 60
                priceChange = currentPrice - threeMinAgoPrice
                if last3minAverage > (averagePastHrVol * .5) and priceChange > 0:
                    returnData.append({"pair":{item['product_id']},"volume_change": (last3minAverage / averagePastHrVol),"price_change": priceChange })
        return sorted(returnData, key=lambda d: d['volume_change'], reverse=True)

    def getLikelyPumps1(self):
        returnData = []
        pairs = self.getPairs()

        for item in pairs:
            if float(item['approximate_quote_24h_volume']) < 399000.00:
                continue
            time.sleep(.03)
            last4minAverage = 0.0
            averagePastHrVol = 0.0
            candles = self.restApiCall(path=f"products/{item['product_id']}/candles",parameters="?granularity=ONE_MINUTE")['candles']
            if len(candles) > 64:
                fiveMinAgoPrice = candles[0]
                currentPrice = 0.0
                for i in range(0,4):
                    last4minAverage = last4minAverage + float(candles[i]['close'])
                last4minAverage = last4minAverage / 4
                for i in range(4,64):
                    averagePastHrVol = averagePastHrVol + float(candles[i]['close']) 
                averagePastHrVol = averagePastHrVol / 60           
                if last4minAverage > averagePastHrVol:
                    returnData.append({"pair":{item['product_id']},"volume_change": (last4minAverage / averagePastHrVol) })
        return sorted(returnData, key=lambda d: d['volume_change'], reverse=True)

    def getTop(self):
        returnData = []
        pairs = self.getPairs()

        for item in pairs:
            time.sleep(.03)
            oneMinData = self.restApiCall(path=f"products/{item['product_id']}/candles",parameters="?granularity=ONE_MINUTE&limit=10")['candles']
            average24Volume = float(item['volume_24h']) / 1440.00
            volumeChange = 0.0
            initialPrice = 0.0
            currentPrice = 0.0
            for i in range(0,len(oneMinData)):
                if i == 0:
                    currentPrice = float(oneMinData[i]['close'])
                if i == (len(oneMinData) - 1):
                    initialPrice = float(oneMinData[i]['open'])
                volumeChange = volumeChange + float(oneMinData[i]['volume'])
            average5Volume = volumeChange / len(oneMinData)
            percentageChange = (currentPrice - initialPrice) / initialPrice
            volumeChange = (average5Volume - average24Volume) / average24Volume
            if volumeChange > 1 and percentageChange > 0:
                returnData.append({"pair": item['product_id'],"priceChange5min": percentageChange,"volumeChange": volumeChange,"momentum": () })

        return sorted(returnData, key=lambda d: d['volumeChange'], reverse=True)
            
class coinbase_ws:
    def __init__(self):
        self.API_KEY=os.environ['COINBASE_API_KEY']
        self.API_SECRET=os.environ['COINBASE_API_SECRET']
        self.WS_URL = "wss://advanced-trade-ws.coinbase.com"

    def generate_jwt(self):
        current_time = int(time.time())
        payload = {
            "iss": "cdp",
            "nbf": current_time,
            "exp": current_time + 120,  # JWT valid for 120 seconds
            "sub": self.API_KEY,
        }
        headers = {
            "kid": self.API_KEY,
            "nonce": uuid.uuid4().hex
        }
        return jwt.encode(payload, self.SIGNING_KEY, algorithm="ES256", headers=headers)

    def on_open(self,ws):
        # Generate JWT
        token = self.generate_jwt()

        # Subscribe to the user channel for BTC-USD orders
        subscribe_message = {
            "type": "subscribe",
            "product_ids": ["BTC-USD"],
            "channel": "ticker"
        }
        ws.send(json.dumps(subscribe_message))
        print("Subscribed to user channel for BTC-USD data")

    def on_message(ws, message):
        data = json.loads(message)
        print(f"Received message: {data}")

    def on_error(ws, error):
        print(f"Error: {error}")

    def on_close(ws):
        print("Connection closed")

    def createWebSocket(self):
        # Create the WebSocket connection
        ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        ws.run_forever()

if __name__=="__main__":
    test = ()
    stuff = test.getTop()
