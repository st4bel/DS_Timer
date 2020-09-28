from dstimer import db

class Incomings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inc_id = db.Column(db.Integer, unique=True)
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
        return "<Incomings id: {}, name: {}>".format(self.inc_id, self.name)

def init_db():
    db.create_all()
    #new_inc = Incomings(inc_id = 1, name="test")
    #db.session.add(new_inc)
    #db.session.commit()
if __name__ == "__main__":
    init_db()