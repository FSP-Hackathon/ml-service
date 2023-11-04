import os
from typing import List
from fastapi import FastAPI
from influxdb_client import InfluxDBClient, Point, QueryApi
from influxdb_client.client.flux_table import FluxTable

app = FastAPI()

INFLUXDB_URL = 'http://8086:8086'
INFLUXDB_TOKEN = os.environ['INFLUXDB_TOKEN']
INFLUXDB_ORG = os.environ['INFLUXDB_ORG']
INFLUX_BUCKET = os.environ['INFLUXDB_BUCKET']

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()

@app.get("/metrica/{mtype}")
async def get_time_series(mtype: str):
    query = f'from(bucket: "{INFLUX_BUCKET}") |> range(start: -1h)'
    query = f'''
            from(bucket: "{INFLUX_BUCKET}")
            |> range(start: -1h)
            |> filter(fn: (r) => r._measurement == {mtype})
            '''

    result: List[FluxTable] = query_api.query(query=query)
    x, y = [], []
    for table in result:
        for record in table.records:
            x.append(record.get_time()) 
            y.append(record.get_value())

    return x, y


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
