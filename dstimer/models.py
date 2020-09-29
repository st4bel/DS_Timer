from dstimer import db
from datetime import datetime
import dateutil.parser
import json

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

class Attacks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer)
    source_coord_x = db.Column(db.Integer)
    source_coord_y = db.Column(db.Integer)
    target_id = db.Column(db.Integer)
    target_coord_x = db.Column(db.Integer)
    target_coord_y = db.Column(db.Integer)
    departure_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    type = db.Column(db.String(64))
    force = db.Column(db.Boolean)
    domain = db.Column(db.String(64))
    sitter = db.Column(db.Integer)
    vacation = db.Column(db.Integer)
    player_id = db.Column(db.Integer)
    player_name = db.Column(db.String(64))
    building = db.Column(db.String(64))
    save_default_attack_building = db.Column(db.Integer)
    units = db.Column(db.String(255))

    def __repr__(self):
        return "<Attack {}>".format(self.departure_time.strftime("%m/%d/%Y, %H:%M:%S"))
       
    def is_expired(self):
        return self.departure_time < datetime.now()
    
    def is_valid(self):
        return self.source_id is not None and self.target_id is not None and not self.is_expired() and self.player_id is not None and self.unit is not None

def init_db():
    db.create_all()
    #new_inc = Incomings(inc_id = 1, name="test")
    #db.session.add(new_inc)
    #db.session.commit()
if __name__ == "__main__":
    init_db()