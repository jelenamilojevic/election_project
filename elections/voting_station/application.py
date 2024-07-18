import werkzeug
from flask import Flask, request, Response, jsonify
from elections.configuration import Configuration
from elections.models import database
from redis import Redis
from officialDecorator import roleCheck
from flask_jwt_extended import JWTManager, get_jwt
import io
import csv

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/", methods=["GET"])
@roleCheck(role="official")
def index():
    return "Hello world!"

@application.route("/vote", methods=["POST"])
@roleCheck(role="official")
def vote():
    try:
        with Redis(host=Configuration.REDIS_HOST) as redis:
            content = request.files["file"].stream.read().decode("utf-8")
            stream = io.StringIO(content)
            reader = csv.reader(stream)

            claims = get_jwt()
            officialJmbg = claims["jmbg"]

            count = 0
            pids = []
            guids = []
            flag = True
            for row in reader:
                if len(row) != 2:
                    data = {"message": "Incorrect number of values on line {}.".format(count)}
                    flag = False
                    return jsonify(data), 400

                guid = row[0]
                try:
                    pid = int(row[1])
                except ValueError:
                    flag = False
                    data = {"message": "Incorrect poll number on line {}.".format(count)}
                    return jsonify(data), 400

                if pid < 0:
                    flag = False
                    data = {"message": "Incorrect poll number on line {}.".format(count)}
                    return jsonify(data), 400

                pids.append(pid)
                guids.append(guid)
                count += 1

            if flag:
                for i in range (count):
                    redis.rpush(Configuration.REDIS_VOTES_LIST, pids[i], guids[i])
                redis.rpush("official", officialJmbg)
                redis.publish("votes_channel", "added")


        return Response(status=200)

    except werkzeug.exceptions.BadRequestKeyError:
        data = {"message": "Field file is missing."}
        return jsonify(data), 400


if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, port=5000)