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


# Инициализация API для записи данных
write_api = client.write_api(write_options=SYNCHRONOUS)

# Функция для генерации случайных данных
def write_random_data(measurement, field, base_value):
    point = Point(measurement) \
        .tag("host", "host1") \
        .field("total", base_value + random.uniform(-3, 3)) \
        .field("free", base_value + random.uniform(-3, 3)) \
        .field("used", base_value + random.uniform(-3, 3)) \
        .time(datetime.utcnow(), WritePrecision.NS)
    write_api.write(INFLUX_BUCKET, INFLUXDB_ORG, point)

try:
    while True:
        # Генерация и запись данных для CPU
        write_random_data("cpu", "total", 50)  # Предполагаем, что 50 - это базовое значение использования CPU
        # write_random_data("cpu", "free", 30)
        # write_random_data("cpu", "used", 20)
        # # Генерация и запись данных для Disk
        # write_random_data("disk", "usage", 70)  # Предполагаем, что 70 - это базовое значение использования Disk

        # # Генерация и запись данных для RAM
        # write_random_data("ram", "usage", 30)  # Предполагаем, что 30 - это базовое значение использования RAM

except KeyboardInterrupt:
    pass
finally:
    client.close()
    print("Script interrupted and connection closed.")
