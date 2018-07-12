from flask import Flask, request, jsonify
import mysql.connector
import math
import datetime
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
    cnx.commit()
    cnx.close()


def get_age(dob):
    today = datetime.date.today()
    return (today - dob) // datetime.timedelta(days=365.2425)


@app.route('/addacq')
def add_acq():
    my_id = request.args.get('id', default=-1, type=int)
    their_id = request.args.get('user', default=-1, type=int)

    with open_db() as cursor:

        query = f"INSERT INTO acquaintances (user_from, user_to, confirmed) " \
                f"VALUES ({my_id}, {their_id}, 0)"

        cursor.execute(query)

    return EMPTY


@app.route('/confirmacq')
def confirm_acq():
    my_id = request.args.get('id', default=-1, type=int)
    their_id = request.args.get('user', default=-1, type=int)

    with open_db() as cursor:

        query = f"UPDATE acquaintances " \
                 f"SET confirmed = 1 " \
                 f"WHERE user_from = {their_id} AND user_to = {my_id}"

        cursor.execute(query)

    return EMPTY


@app.route('/checkrequests')
def check_requests():
    my_id = request.args.get('id', default=-1, type=int)
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude, title FROM users " \
                f"WHERE id IN (" \
                f"SELECT user_from FROM acquaintances " \
                f"WHERE user_to = {my_id} AND confirmed = 0 " \
                f")"

        return jsonify(execute(cursor, query, my_lat, my_long))


@app.route('/writelatlong')
def write_lat_long():
    user = request.args.get('id', default=-1, type=int)
    lat = request.args.get('lat', default=-1, type=float)
    long = request.args.get('long', default=-1, type=float)

    with open_db() as cursor:

        query = f"UPDATE users " \
                f"SET latitude = {lat}, longitude = {long} " \
                f"WHERE id = {user}"
        print(query)

        cursor.execute(query)
        print(cursor)

    return EMPTY


def calculate_distance(lat1, lat2, long1, long2):
    return 12742 * math.asin(math.sqrt(0.5 - math.cos((lat2 - lat1) * P)/2 + math.cos(lat1 * P) *
                                       math.cos(lat2 * P) * (1 - math.cos((long2 - long1) * P))/2))


def execute(cursor, query, my_lat, my_long):
    cursor.execute(query)
    result = []
    for id, name, latitude, longitude, title, dob, gender, description in cursor:
        print(id, name, latitude, longitude, title, dob, gender, description)
        latitude = float(latitude)
        longitude = float(longitude)
        d = {
            'id': id,
            'name': name,
            'latitude': latitude,
            'longitude': longitude,
            'distance': calculate_distance(my_lat, latitude, my_long, longitude),
            'title': title,
            'age': get_age(dob),
            'gender': gender,
            'description': description
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


@app.route('/newaccount')
def new_account():
    username = request.args.get('username', default="", type=str)
    pword = request.args.get('pword', default="", type=str)
    name = request.args.get('name', default="", type=str)
    lat = request.args.get('lat', default="", type=float)
    long = request.args.get('long', default="", type=float)

    with open_db() as cursor:

        src_query = f"SELECT username FROM users " \
                    f"WHERE username = \"{username}\""
        cursor.execute(src_query)
        for username, in cursor:
            print(username)
            return jsonify([])

        query = f"INSERT INTO users (username, password, name, latitude, longitude) " \
                f"VALUES (\"{username}\", \"{pword}\", \"{name}\", {lat}, {long})"
        cursor.execute(query)

        id_query = f"SELECT id FROM users " \
                   f"WHERE username = \"{username}\""
        cursor.execute(id_query)
        id = None
        for i, in cursor:
            id = i

        d = {
            'id': id,
            'username': username,
            'pword': pword,
            'name': name
        }
        return jsonify([d])


@app.route('/verifylogin')
def verify_pword():
    # username is encrypted using MD5, pword encrypted using SHA1
    # TODO: use better encrpytion techniques
    username = request.args.get('username', default="", type=str)
    pword = request.args.get('pword', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude, title, username, password FROM users " \
                f"WHERE username = \"{username}\""

        cursor.execute(query)
        for id, name, latitude, longitude, title, u, p in cursor:
            latitude = float(latitude)
            longitude = float(longitude)
            if p == pword:
                d = {
                    'id': id,
                    'name': name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'distance': 0,
                    'title': title
                }
                return jsonify([d])

    return jsonify([])


@app.route('/searchallacqs')
def search_all_acqs():
    my_lat = request.args.get('lat', default=-1, type=float)
    my_long = request.args.get('long', default=-1, type=float)
    my_id = request.args.get('id', default=-1, type=int)
    order = request.args.get('order', default="", type=str)

    with open_db() as cursor:

        query = f"SELECT id, name, latitude, longitude, title, dob, gender, description FROM users " \
                f"WHERE id <> {my_id} " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id} AND confirmed = 1" \
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

        query = f"SELECT id, name, latitude, longitude, title, dob, gender, description FROM users " \
                f"WHERE name = \"{search}\" AND id <> {my_id} " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id} AND confirmed = 1" \
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

        query = f"SELECT id, name, latitude, longitude, title, dob, gender, description FROM users " \
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

        query = f"SELECT id, name, latitude, longitude, title, dob, gender, description FROM users " \
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
        query = f"SELECT id, name, latitude, longitude, title, dob, gender, description FROM users " \
                f"WHERE (latitude BETWEEN {min_lat} AND {max_lat}) AND (longitude BETWEEN {min_long} AND {max_long}) " \
                f"AND id IN (" \
                f"SELECT user_to FROM acquaintances " \
                f"WHERE user_from = {my_id}" \
                f")"
        query += gen_order("distance", my_lat, my_long)

        return jsonify(execute(cursor, query, my_lat, my_long))


if __name__ == "__main__":
    app.run()

