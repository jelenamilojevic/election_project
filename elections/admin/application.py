from flask import Flask, request, Response, jsonify
from elections.configuration import Configuration
from elections.models import database, Participant, Election, ElectionParticipant, Vote
from adminDecorator import roleCheck
from flask_jwt_extended import JWTManager
from datetime import datetime
from sqlalchemy import and_


application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

def checkDates(start, end):
    try:
        sd = datetime.strptime(start, '%Y-%m-%d')
        ed = datetime.strptime(end, '%Y-%m-%d')

        if sd > ed:
            return False

        duplicate = Election.query.filter(and_(sd <= Election.end, ed >= Election.start)).first()
        if (duplicate):
            return False

        return True
    except ValueError:
        return False

def checkParticipants(participants, individual):
    exists = True
    wrongType = False

    if len(participants) < 2:
        return False

    for item in participants:
        participant = Participant.query.get(item)
        if (not participant):
            exists = False
        elif (participant.individual != individual):
            wrongType = True

    if (not exists):
        return False

    if (wrongType):
        return False

    return True

def getIndividualResult(participantId, electionId):
    votes = Vote.query.filter(and_(participantId == Vote.participantId, electionId == Vote.electionId, Vote.comment == None)).all()
    allVotes = Vote.query.filter(Vote.comment == None).all()

    votesCount = len(votes)
    allVotesCount = len(allVotes)
    if (votesCount != 0 and allVotesCount != 0):
        result = len (votes) / len(allVotes)
    else:
        result = 0
    return round(result,2)


def getPartyResult(participants):
    seats = len(participants)
    votes = {
    }

    return True

@application.route("/createParticipant", methods = ["POST"])
@roleCheck(role="admin")
def createParticipant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    nameEmpty = len(name) == 0
    individualEmpty = str(individual) != "True" and str(individual) != "False"

    if (nameEmpty):
        data = {"message": "Field name is missing."}
        return jsonify(data), 400

    if (individualEmpty):
        data = {"message": "Field individual is missing."}
        return jsonify(data), 400

    participant = Participant(name= name, individual=individual)
    database.session.add(participant)
    database.session.commit()

    data = {"id": participant.id}
    return jsonify(data), 200

@application.route("/getParticipants", methods = ["GET"])
@roleCheck(role="admin")
def getParticipants():
    participants = Participant.query.all()

    data = {"participants": []}

    for participant in participants:
        tmp = {}
        tmp["id"] = participant.id
        tmp["name"] = participant.name
        tmp["individual"] = participant.individual
        data["participants"].append(tmp)

    return jsonify(data), 200

@application.route("/createElection", methods = ["POST"])
@roleCheck(role="admin")
def createElection():
    start = request.json.get("start", "")
    end = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participants = request.json.get("participants", "")

    startEmpty = len(start) == 0
    endEmpty = len(end) == 0
    participantsEmpty = len(participants) == 0
    individualEmpty = str(individual) != "True" and str(individual) != "False"

    if (startEmpty):
        data = {"message": "Field start is missing."}
        return jsonify(data), 400

    if (endEmpty):
        data = {"message": "Field end is missing."}
        return jsonify(data), 400

    if (individualEmpty):
        data = {"message": "Field individual is missing."}
        return jsonify(data), 400

    if (participantsEmpty):
        data = {"message": "Field participants is missing."}
        return jsonify(data), 400

    if (not checkDates(start, end)):
        data = {"message": "Invalid date and time."}
        return jsonify(data), 400

    if (not checkParticipants(participants, individual)):
        data = {"message": "Invalid participant."}
        return jsonify(data), 400

    election = Election(start=start, end=end, individual=individual)
    database.session.add(election)
    database.session.commit()

    pollNumbers = {"pollNumbers": []}

    for participant in participants:
        electionParticipant = ElectionParticipant(electionId=election.id, participantId=participant)
        database.session.add(electionParticipant)
        database.session.commit()
        pollNumbers["pollNumbers"].append(participant)


    return jsonify(pollNumbers), 200

@application.route("/getElections", methods = ["GET"])
@roleCheck(role="admin")
def getElections():
    elections = Election.query.all()

    data = {"elections": []}

    for election in elections:
        tmp = {"participants": []}
        tmp["id"] = election.id
        tmp["start"] = election.start
        tmp["end"] = election.end
        tmp["individual"] = election.individual
        for participant in election.participants:
            tmp2 = {}
            tmp2["id"] = participant.id
            tmp2["name"] = participant.name
            tmp["participants"].append(tmp2)
        data["elections"].append(tmp)

    return jsonify(data), 200

@application.route("/getResults", methods=["GET"])
@roleCheck(role="admin")
def getResults():

    data = {}
    electionId = request.args["id"]

    election = Election.query.filter(Election.id == electionId).first()

    participants = []
    for participant in election.participants:
        tmp = {}
        tmp["pollNumber"] = participant.id
        tmp["name"] = participant.name
        if participant.individual:
            tmp["result"] = getIndividualResult(participant.id, electionId)
        else:
            getPartyResult(election.participants)

        participants.append(tmp)

    data["participants"] = participants

    invalid_votes = []
    for vote in election.votes:
        tmp = {}
        if (vote.comment != None):
            tmp["electionOfficialJmbg"] = vote.jmbg
            tmp["ballotGuid"] = vote.guid
            tmp["pollNumber"] = vote.participantId
            tmp["reason"] = vote.comment
            invalid_votes.append(tmp)

    data["invalidVotes"] = invalid_votes

    getPartyResult(election.participants)

    return jsonify(data), 200


if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug=True, port=5001)