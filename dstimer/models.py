from dstimer import db

class Incomings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index = True)
    target_village_id = db.Column(db.Integer)
    target_village_name = db.Column(db.String(64))
    source_village_id = db.Column(db.Integer)
    source_village_name = db.Column(db.String(64))
    source_player_id = db.Column(db.Integer)
    source_player_name = db.Column(db.String(64))
    distance = db.Column(db.Float)
    arrival_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return "<Incomings attack from {} to {} of {}>".format(self.source_village_name, self.target_village_name, self.source_player_name)