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

@app.get("/timeseries")
async def get_time_series():
    query = f'from(bucket: "{INFLUX_BUCKET}") |> range(start: -1h)'

    result: List[FluxTable] = query_api.query(query=query)

    data = []
    for table in result:
        for record in table.records:
            data.append({
                'time': record.get_time(),
                'measurement': record.get_measurement(),
                'field': record.get_field(),
                'value': record.get_value()
            })

    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
