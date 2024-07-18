from flask import Flask, request, Response, jsonify
from configuration import Configuration
from models import database, User, UserRole
from flask_jwt_extended import JWTManager, create_access_token, jwt_required,create_refresh_token, get_jwt_identity, get_jwt
from sqlalchemy import and_
import re

application = Flask(__name__)
application.config.from_object(Configuration)

def jmbg_check(jmbg):
    try:
        day = (int (jmbg[:2]))
        month = (int (jmbg[2:4]))
        year = (int (jmbg[4:7]))
        region = (int (jmbg[7:9]))
        number = (int (jmbg[9:12]))
        checksum = (int(jmbg[12]))

        if (day < 1 or day > 31):
            return False

        if (month < 1 or month > 12):
            return False

        if (year < 0 or year > 999):
            return False

        if (region < 70 or region > 99):
            return False

        if (number < 0 or number > 999):
            return False

        a1 = int (jmbg[0])
        a2 = int(jmbg[1])
        a3 = int(jmbg[2])
        a4 = int(jmbg[3])
        a5 = int(jmbg[4])
        a6 = int(jmbg[5])
        a7 = int(jmbg[6])
        a8 = int(jmbg[7])
        a9 = int(jmbg[8])
        a10 = int(jmbg[9])
        a11 = int(jmbg[10])
        a12 = int(jmbg[11])

        sum = 7*a1 + 6*a2 + 5*a3 + 4*a4 + 3*a5 + 2*a6 + 7*a7 + 6*a8 + 5*a9 + 4*a10 + 3*a11 + 2*a12
        m = sum % 11

        if (m == 0):
            a13 = 0
        elif (m == 1):
            a13 = -1
        else:
            a13 = 11 - m

        if (checksum != a13):
            return False

        return True
    except ValueError:
        return False


@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    jmbgEmpty = len(jmbg) == 0
    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    forenameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if (jmbgEmpty):
        data = {"message": "Field jmbg is missing." }
        return jsonify(data), 400

    if (forenameEmpty):
        data = {"message": "Field forename is missing." }
        return jsonify(data), 400

    if (surnameEmpty):
        data = {"message": "Field surname is missing." }
        return jsonify(data), 400

    if (emailEmpty):
        data = {"message": "Field email is missing." }
        return jsonify(data), 400

    if (passwordEmpty):
        data = {"message": "Field password is missing." }
        return jsonify(data), 400

    if (not jmbg_check(jmbg)):
        data = {"message": "Invalid jmbg."}
        return jsonify(data), 400

    reg = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$"
    if(not re.search(reg,email)):
        data = {"message": "Invalid email."}
        return jsonify(data), 400

    reg = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d]{8,}$"
    pattern = re.compile(reg)
    match = re.search(pattern, password)
    if (not match):
        data = {"message": "Invalid password."}
        return jsonify(data), 400

    duplicate = User.query.filter( User.email == email).first()
    if (duplicate):
        data = {"message": "Email already exists."}
        return jsonify(data), 400


    user = User(email = email, password = password, forename= forename, surname= surname, jmbg=jmbg)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId=user.id, roleId=2)
    database.session.add(userRole)
    database.session.commit()

    return Response (status= 200)

jwt = JWTManager(application)

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len (email) == 0
    passwordEmpty = len(password) == 0

    if (emailEmpty):
        data = {"message": "Field email is missing."}
        return jsonify(data), 400

    if (passwordEmpty):
        data = {"message": "Field password is missing."}
        return jsonify(data), 400

    reg = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$"
    if(not re.search(reg,email)):
        data = {"message": "Invalid email."}
        return jsonify(data), 400

    user = User.query.filter( and_(User.email == email, User.password == password)).first()
    if (not user):
        data = {"message": "Invalid credentials."}
        return jsonify(data), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "jmbg": user.jmbg,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity=user.email, additional_claims= additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    # return Response(accessToken, status=200)
    return jsonify(accessToken = accessToken, refreshToken = refreshToken)

@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "jmbg":refreshClaims["jmbg"],
        "roles": refreshClaims["roles"]
    }

    token = create_access_token(identity= identity, additional_claims=additionalClaims)

    return jsonify(accessToken = token)

@application.route("/delete", methods=["POST"])
@jwt_required()
def deleteUser():
    email = request.json.get("email", "")

    identity = get_jwt_identity()

    emailEmpty = len(email) == 0

    if (emailEmpty):
        data = {"message": "Field email is missing."}
        return jsonify(data), 400

    reg = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$"
    if(not re.search(reg,email)):
        data = {"message": "Invalid email."}
        return jsonify(data), 400

    user = User.query.filter( User.email == email).first()
    if (not user):
        data = {"message": "Unknown user."}
        return jsonify(data), 400

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)


@application.route("/check", methods=["POST"])
@jwt_required()
def check():
    return "Token is valid"

@application.route("/", methods=["GET"])
def index():
    return "Hello world!"


if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, port=5002)