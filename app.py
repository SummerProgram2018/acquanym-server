from flask import Flask, request, jsonify
import mysql.connector
import math
from contextlib import contextmanager

HOST = "db4free.net"
USER = "hobrien17"
PWORD = "dbpword1"
DB_NAME = "ei8htideas"
EMPTY = ""
P = math.pi/180
DIST_CALC = "12742 * ASIN(SQRT(0.5 - COS((latitude - {}) * {})/2 " \
            "+ COS({} * {}) * COS(latitude * {}) * " \
                  "(1 - COS((longitude - {}) * {}))/2))"

app = Flask(__name__)


@contextmanager
def open_db():
    cnx = mysql.connector.connect(user=USER, password=PWORD, host=HOST, database=DB_NAME)
    cursor = cnx.cursor()
    yield cursor
    cnx.close()


@app.route('/writelatlong')
def write_lat_long():
    user = request.args.get('id', default=-1, type=int)
    lat = request.args.get('lat', default=-1, type=float)
    long = request.args.get('long', default=-1, type=float)

    with open_db() as cursor:

        query = f"UPDATE users " \
                f"SET latitude = {lat}, longitude = {long} " \
                f"WHERE id = {user}"

        cursor.execute(query)

    return EMPTY


def calculate_distance(lat1, lat2, long1, long2):
    return 12742 * math.asin(math.sqrt(0.5 - math.cos((lat2 - lat1) * P)/2 + math.cos(lat1 * P) *
                                       math.cos(lat2 * P) * (1 - math.cos((long2 - long1) * P))/2))


def execute(cursor, query, my_lat, my_long):
    cursor.execute(query)
    result = []
    for id, name, latitude, longitude, title in cursor:
        latitude = float(latitude)
        longitude = float(longitude)
        d = {
            'id': id,
            'name': name,
            'latitude': latitude,
            'longitude': longitude,
            'distance': calculate_distance(my_lat, latitude, my_long, longitude),
            'title': title
        }
        result.append(d)

    return result


def gen_order(order, my_lat, my_long):
    order_by = ""
    if order == "distance":
        print("dist")
        order_by = f"ORDER BY ({DIST_CALC.format(my_lat, P, my_lat, P, P, my_long, P)})"
        print(order_by)
    elif order == "name":
        print("name")
        order_by = f"ORDER BY name"
    return order_by


@app.route('/searchallacqs')
def search_all_acqs():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE id <> {my_id} " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
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

        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE name = \"{search}\" AND id <> {my_id} " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
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

        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE id <> {my_id} " \
                f"AND id NOT IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
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

        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE name = \"{search}\" AND id <> {my_id} " \
                f"AND id NOT IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
                f")"

        query += gen_order(order, my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


@app.route('/nearbyacqs')
def get_nearby():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=float)
    src_range = request.args.get('range', default=0, type=float)

    with open_db() as cursor:

        max_lat = my_lat + src_range
        min_lat = my_lat - src_range
        max_long = my_long + src_range
        min_long = my_long - src_range
        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE (latitude BETWEEN {min_lat} AND {max_lat}) AND (longitude BETWEEN {min_long} AND {max_long}) " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
                f") " \
                f"ORDER BY (SQRT(POWER({my_lat} - latitude, 2) + POWER({my_long} - longitude, 2)))"

    return jsonify(execute(cursor, query, my_lat, my_long))


if __name__ == "__main__":
    app.run()

