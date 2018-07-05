from flask import Flask, request, jsonify
import mysql.connector
import math
from contextlib import contextmanager

HOST = "db4free.net"
USER = "hobrien17"
PWORD = "dbpword1"
DB_NAME = "ei8htideas"

app = Flask(__name__)

@contextmanager
def open_db():
    cnx = mysql.connector.connect(user=USER, password=PWORD, host=HOST, database=DB_NAME)
    cursor = cnx.cursor()
    yield cursor
    cnx.close()


@app.route('/nearby')
def get_nearby():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    src_range = request.args.get('range', default=0, type=float)

    with open_db() as cursor:

        max_lat = my_lat + src_range
        min_lat = my_lat - src_range
        max_long = my_long + src_range
        min_long = my_long - src_range
        query = f"SELECT id, name, latitude, longitude FROM users " \
                f"WHERE (latitude BETWEEN {min_lat} AND {max_lat}) AND (longitude BETWEEN {min_long} AND {max_long}) " \
                f"ORDER BY (SQRT(POWER({my_lat} - latitude, 2) + POWER({my_long} - longitude, 2)))"

        cursor.execute(query)
        result = []
        for id, name, latitude, longitude in cursor:
            d = {
                'id': id,
                'name': name,
                'lat': latitude,
                'long': longitude,
                'dist': math.sqrt((my_lat - latitude)**2 + (my_long - longitude)**2)
            }
            result.append(d)

    return jsonify(result)


if __name__ == "__main__":
    app.run()

