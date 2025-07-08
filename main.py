from coinbase import coinbase
from dbsql import dbsql
import time

class baseBot:

    def __init__(self):
        self.cb = coinbase()
        self.db = dbsql()
    
    def buildHistory(self,pair):
        endTime = time.time()
        startTime = endTime - 21000
        candles = self.cb.getCandles(pair,startTime,endTime)
        while len(candles) > 0:
            self.db.ingestCandles(pair,candles)
            candles = candles = self.cb.getCandles(pair,startTime,endTime)

