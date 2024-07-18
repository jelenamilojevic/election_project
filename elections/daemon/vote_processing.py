from elections.models import database, Election, ElectionParticipant, Vote
from elections.configuration import Configuration
from redis import Redis
from datetime import datetime
from sqlalchemy import and_
from flask import Flask

application = Flask(__name__)
application.config.from_object(Configuration)


def check_for_messages():
    with Redis (host=Configuration.REDIS_HOST, charset="utf-8", decode_responses=True) as redis:
        sub = redis.pubsub()
        sub.subscribe('votes_channel')
        for message in sub.listen():
            if message is not None and isinstance(message, dict):
                message = message.get('data')
                if (message == "added"):
                    now = datetime.now()
                    current = Election.query.filter(and_(now >= Election.start, now <= Election.end)).first()
                    if (not current):
                        return False

                    pid = redis.lpop(Configuration.REDIS_VOTES_LIST)
                    guid = redis.lpop(Configuration.REDIS_VOTES_LIST)
                    officialJmbg = redis.lpop("official")


                    while (pid and guid):

                        duplicate = Vote.query.filter(Vote.guid == guid).first()
                        participant = ElectionParticipant.query.filter(and_(pid == ElectionParticipant.participantId, current.id == ElectionParticipant.electionId)).first()
                        if (duplicate):
                            vote = Vote(participantId=pid, guid=guid, electionId=current.id, jmbg=officialJmbg, comment="Duplicate ballot.")
                        elif (not participant):
                            vote = Vote(participantId=pid, guid=guid, electionId=current.id, jmbg=officialJmbg, comment="Invalid poll number.")
                        else:
                            vote = Vote(participantId=pid, guid=guid, electionId=current.id, jmbg=officialJmbg)
                        database.session.add(vote)
                        database.session.commit()

                        pid = redis.lpop(Configuration.REDIS_VOTES_LIST)
                        guid = redis.lpop(Configuration.REDIS_VOTES_LIST)

                    return True

    return False

database.init_app(application)
with application.app_context():
    while True:
        check_for_messages()
        #if check_for_messages():
            #break