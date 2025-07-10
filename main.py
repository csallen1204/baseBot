from coinbase import coinbase
from dbsqlite import dbsqlite
import time
import pandas
import sqlite3

class baseBot:

    def __init__(self):
        self.cb = coinbase()
        self.db = dbsqlite()
    
    def buildHistory(self,pair):
        endTime = int(time.time())
        startTime = endTime - 21000
        candles = self.cb.getCandles(pair,startTime,endTime)
        while len(candles) > 0:
            self.db.ingestCandles(pair,candles)
            endTime = startTime
            startTime = endTime - 21000
            time.sleep(.03)
            candles = candles = self.cb.getCandles(pair,startTime,endTime)

        conn = sqlite3.connect('datasets.db')