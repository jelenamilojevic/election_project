from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy();


class ElectionParticipant(database.Model):
    __tablename__= "electionParticipant"
    id = database.Column(database.Integer, primary_key=True)
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)
    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False)


class Participant(database.Model):
    __tablename__ = "participants"
    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    individual = database.Column(database.Boolean)

    elections = database.relationship("Election", secondary=ElectionParticipant.__table__, back_populates="participants")

    def __repr__(self):
        return "({}, {}, {})".format(self.id, self.name, str(self.individual))

class Election(database.Model):
    __tablename__ = "elections"
    id = database.Column(database.Integer, primary_key=True)
    start = database.Column(database.DateTime, nullable=False)
    end = database.Column(database.DateTime, nullable=False)
    individual = database.Column(database.Boolean)

    participants = database.relationship("Participant", secondary=ElectionParticipant.__table__, back_populates="elections")
    votes = database.relationship("Vote", back_populates="election")

    def __repr__(self):
        return "({}, {}, {}, {})".format(self.id, str(self.start), str(self.end), str(self.individual))


class Vote(database.Model):
    __tablename__ = "votes"

    id = database.Column(database.Integer, primary_key=True)
    guid = database.Column(database.String(256), nullable=False)
    jmbg = database.Column(database.String(13))
    participantId = database.Column(database.Integer, nullable=False)
    comment = database.Column(database.String(256))

    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)
    election = database.relationship("Election", back_populates = "votes")

    def __repr__(self):
        return "({}, {})".format(self.id, self.participantId)





