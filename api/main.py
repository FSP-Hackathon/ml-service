import os
import sys
import inspect
from typing import List, Dict
from datetime import datetime, timedelta
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response
from influxdb_client import InfluxDBClient, Point, WriteOptions, WritePrecision, Bucket, BucketRetentionRules
from influxdb_client.client.flux_table import FluxTable
import numpy as np

from __scheme__ import SCHEME
from ml import MultidimensionalMatrixProfile, MultivariateTimeSeriesPredictor


class RAMMetrics(BaseModel):
    sys: int
    used: int
    total: int

class DiskMetrics(BaseModel):
    total: int
    free: int
    used: int

class CPUMetrics(BaseModel):
    total: int
    free: int
    used: int

class PgStatActivity(BaseModel):
    pid: int
    wait_event: str
    duration: int

class Metrics(BaseModel):
    hardware: Dict[str, Dict[str, int]]
    pg_stat_activity: List[PgStatActivity]
    timestamp: int
    db_id: str


app = FastAPI()

INFLUXDB_URL = 'http://influxdb:8086'
INFLUXDB_TOKEN = os.environ['INFLUXDB_TOKEN']
INFLUXDB_ORG = os.environ['INFLUXDB_ORG']
INFLUX_BUCKET = os.environ['INFLUXDB_BUCKET']

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()
write_api = client.write_api(write_options=WriteOptions(batch_size=1_000, flush_interval=10_000))
buckets_api = client.buckets_api()
orgs_api = client.organizations_api()

last_check_time = None
last_predict_time = None

THRESHOLD = 90


@app.get("/metrics/{db_id}/")
async def get_time_series(db_id: str, mtype: str, duration: int, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST"
    response.headers["Access-Control-Allow-Headers"] = "Accept,Accept-Encoding,Accept-Language,Access-Control-Request-Header,Access-Control-Request-Method,Authorization,Cache-Control,Connection,Content-Type,DNT,Host,If-Modified-Since,Keep-Alive,Origin,Pragma,Referer,User-Agent,x-csrf-token,x-requested-with"

    query = f'''
            from(bucket: "{db_id}")
            |> range(start: -{duration}s)
            |> filter(fn: (r) => r._measurement == "{mtype}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''

    result: List[FluxTable] = query_api.query(query=query)

    data = []
    
    for table in result:
            for record in table.records:
                row = {}
                for val in SCHEME[mtype]['values']:
                    row[val] = record.values[val]

                row['timestamp'] = record.get_time().timestamp()
                data += [row]

    return { 'data': data }


@app.post("/metrics/")
async def proc_updates(metrics: Metrics):
    timestamp = datetime.utcfromtimestamp(metrics.timestamp)
    db_id = metrics.db_id

    existing_buckets = buckets_api.find_buckets().buckets
    bucket_exists = any(bucket.name == db_id for bucket in existing_buckets)

    if not bucket_exists:
        orgs = orgs_api.find_organizations()
        org_id = next(org.id for org in orgs if org.name == INFLUXDB_ORG)

        retention_rules = BucketRetentionRules(type="expire", every_seconds=604800)
        new_bucket = Bucket(name=db_id, retention_rules=[retention_rules], org_id=org_id)
        buckets_api.create_bucket(bucket=new_bucket, org=INFLUXDB_ORG)
        print(f"Bucket '{db_id}' was created.")

    try:
        for key, value in metrics.hardware.items():
            if key in ['db_id', 'timestamp']:
                continue

            point = Point(key).time(timestamp, WritePrecision.NS)
            for field_key, field_value in value.items():
                point = point.field(field_key, field_value)
            write_api.write(bucket=db_id, org=INFLUXDB_ORG, record=point)

        pg_stat_activity_str = str(metrics.pg_stat_activity)
        pg_stat_point = Point("pg_stat_activity").time(timestamp, WritePrecision.NS).field("data", pg_stat_activity_str)
        write_api.write(bucket=db_id, org=INFLUXDB_ORG, record=pg_stat_point)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    alerts = []

    if check_anomaly(db_id):
        alerts += ['Anomaly detected.']
    
    if check_prediction(db_id):
        alerts += ['A large increase in the load is expected.']

    return {"message": "Data written successfully", "alerts": alerts}


def get_data(db_id: str):
    data = []
    timestamps = []
    ts = False
    for measurement in SCHEME:
        if measurement == "pg_stat_activity":
            continue

        query = f'''
                from(bucket: "{db_id}")
                |> range(start: -24h)
                |> filter(fn: (r) => r._measurement == "{measurement}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                '''

        result: List[FluxTable] = query_api.query(query=query)

        metrics = []
        for table in result:
                for record in table.records:
                    load = record.values['used'] / record.values['total']

                    metrics += [load]
                    if not ts:
                        timestamps += [record.get_time().timestamp()]
        
        data += [np.array(metrics)]
        ts = True

    data = np.array(data)
    timestamps = np.array(data)

    return data, timestamps


def check_prediction(db_id: str):
    global last_predict_time

    now = datetime.now()
    if last_predict_time is None or now - last_predict_time < timedelta(minutes=30):
        last_predict_time = now
        return False

    data, timestamps = get_data(db_id)

    predictor = MultivariateTimeSeriesPredictor(timestamps, data)
    predictor.fit()

    predictions = predictor.predict(steps=50)

    high_predictions = predictions[predictions['target'] > THRESHOLD]

    return high_predictions.empty


def check_anomaly(db_id: str):
    global last_check_time

    now = datetime.now()
    if last_check_time is None or now - last_check_time < timedelta(minutes=10):
        last_check_time = now
        return False

    data, _ = get_data(db_id)

    mmp = MultidimensionalMatrixProfile(data, 40)

    return mmp.check_last_10mins()

     


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
