import sqlite3

class dbsqlite:
    def __init__(self):
        pass

    def ingestCandles(self,pair,candles):
        con = sqlite3.connect("datasets.db")
        cur = con.cursor()
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute(f"CREATE TABLE IF NOT EXISTS '{pair}' (start INTEGER PRIMARY KEY, low REAL, high REAL, open REAL, close REAL, volume REAL)")
        
        for candle in candles:
            print(candle)
            cur.execute(f"INSERT INTO '{pair}' VALUES({candle['start']}, {candle['low']}, {candle['high']}, {candle['open']}, {candle['close']}, {candle['volume']})")
        con.commit()
        con.close()
        return