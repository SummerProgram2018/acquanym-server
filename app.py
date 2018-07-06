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


def execute(cursor, query, my_lat, my_long):
    cursor.execute(query)
    result = []
    for id, name, latitude, longitude in cursor:
        latitude = float(latitude)
        longitude = float(longitude)
        d = {
            'id': id,
            'name': name,
            'latitude': latitude,
            'longitude': longitude,
            'distance': math.sqrt((my_lat - latitude) ** 2 + (my_long - longitude) ** 2)
        }
        result.append(d)

    return result


def gen_order(order, my_lat, my_long):
    order_by = ""
    if order == "distance":
        order_by = f"ORDER BY (SQRT(POWER({my_lat} - latitude, 2) + POWER({my_long} - longitude, 2)))"
    elif order == "name":
        order_by = f"ORDER BY name"
    return order_by


@app.route('/searchallacqs')
def search_all_users():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude FROM users " \
                f"WHERE id IN (" \
                f"SELECT to_id FROM acquaintances " \
                f"WHERE from_id = {my_id}" \
                f")"

        query += gen_order(order, my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


@app.route('/searchacqs')
def search_acqs():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)
    search = request.args.get('search', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude FROM users " \
                f"WHERE name = {search}" \
                f"AND id IN (" \
                f"SELECT to_id FROM acquaintances " \
                f"WHERE from_id = {my_id}" \
                f")"

        query += gen_order(order, my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


@app.route('/searchallusers')
def search_all_users():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude FROM users " \
                f"WHERE id NOT IN (" \
                f"SELECT to_id FROM acquaintances " \
                f"WHERE from_id = {my_id}" \
                f")"

        query += gen_order(order, my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


@app.route('/searchusers')
def search_users():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)
    search = request.args.get('search', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude FROM users " \
                f"WHERE name = {search}" \
                f"AND id NOT IN (" \
                f"SELECT to_id FROM acquaintances " \
                f"WHERE from_id = {my_id}" \
                f")"

        query += gen_order(order, my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


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

    return jsonify(execute(cursor, query, my_lat, my_long))


if __name__ == "__main__":
    app.run()

