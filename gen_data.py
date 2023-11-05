from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import random
from datetime import datetime
import os

# Параметры подключения к InfluxDB 2.x
INFLUXDB_URL = 'http://localhost:8086'
INFLUXDB_TOKEN = "I-f-koSfGf4Y_BT_3tbKpnkrDe_L7FHd_lWOijLcCSOYenDTOMuUvP3AwaXaERjiHxUhpM6L9zP-uy4NGDW2Zg=="
INFLUXDB_ORG = "FSP-Cup"
INFLUX_BUCKET = "metrics"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)


write_api = client.write_api(write_options=SYNCHRONOUS)


try:
    while True:
        point = Point("cpu") \
            .tag("host", "host1") \
            .field("total", 50 + int(random.uniform(-9, 9))) \
            .field("free", 50 - 30 + int(random.uniform(-9, 9))) \
            .field("used", 30 + int(random.uniform(-9, 9))) \
            .time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(INFLUX_BUCKET, INFLUXDB_ORG, point)

        point = Point("ram") \
            .tag("host", "host1") \
            .field("total", 50 + int(random.uniform(-9, 9))) \
            .field("sys", 50 - 30 + int(random.uniform(-9, 9))) \
            .field("used", 30 + int(random.uniform(-9, 9))) \
            .time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(INFLUX_BUCKET, INFLUXDB_ORG, point)

        point = Point("disk") \
            .tag("host", "host1") \
            .field("total", 50 + int(random.uniform(-9, 9))) \
            .field("free", 50 - 30 + int(random.uniform(-9, 9))) \
            .field("used", 30 + int(random.uniform(-9, 9))) \
            .time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(INFLUX_BUCKET, INFLUXDB_ORG, point)


except KeyboardInterrupt:
    pass
finally:
    client.close()
    print("Script interrupted and connection closed.")
