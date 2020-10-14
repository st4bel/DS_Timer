from dstimer import db, common, world_data
from datetime import datetime
import dateutil.parser
import ast
import requests


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
    status = db.Column(db.String(64)) # 
    # relationships:
    template_id = db.Column(db.Integer, db.ForeignKey("template.id"))
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))

    def __repr__(self):
        return "<Incomings id: {}, name: {}, status: {}>".format(self.inc_id, self.name, self.status)

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
    #domain = db.Column(db.String(64))
    sitter = db.Column(db.Integer)
    vacation = db.Column(db.Integer)
    #player_id = db.Column(db.Integer)
    #player = db.Column(db.String(64))
    building = db.Column(db.String(64))
    save_default_attack_building = db.Column(db.Integer)
    units = db.Column(db.String(255))
    status = db.Column(db.String(64)) # scheduled, pending, failed, finished, expired
    # relationships:
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))

    def __repr__(self):
        return "<Attack departure: {}, status: {}>".format(self.departure_time.strftime("%m/%d/%Y, %H:%M:%S"), self.status)
       
    def is_expired(self):
        return self.departure_time < datetime.now()
    
    def is_valid(self):
        return self.source_id is not None and self.target_id is not None and not self.is_expired() and self.player_id is not None and self.unit is not None and self.domain is not None and self.type is not None
    
    def get_units(self):
        return ast.literal_eval(self.units)
    
    def load_action(self):
        action = dict(self.__dict__)
        action["source_coord"] = dict()
        action["target_coord"] = dict()
        action["source_coord"]["x"] = self.source_coord_x
        action["source_coord"]["y"] = self.source_coord_y
        action["target_coord"]["x"] = self.target_coord_x
        action["target_coord"]["y"] = self.target_coord_y
        action["units"] = self.get_units()
        action["player"] = self.player.name
        action["player_id"] = self.player.player_id
        action["domain"] = self.player.domain
        if self.vacation == None:
            action["vacation"] = "0"
        return action

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    units = db.Column(db.String(255))
    # relationships:
    incs = db.relationship("Incomings", backref="template", lazy="dynamic")

    def __repr__(self):
        return "<Template {}>".format(self.name)

    def get_units(self):
        return ast.literal_eval(self.units)
    
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    player_id = db.Column(db.Integer)
    domain = db.Column(db.String(64))
    sid = db.Column(db.String(255))
    # relationships:
    attacks = db.relationship("Attacks", backref="player", lazy='dynamic')
    incs = db.relationship("Incomings", backref="player", lazy='dynamic')
    villages = db.relationship("Village", backref="player", lazy='dynamic')
    groups = db.relationship("Group", backref="player", lazy='dynamic')


    def __repr__(self):
        return "<Player {} ({}) on Server {} is {}>".format(self.name, self.player_id, self.domain, "active" if self.is_active() else "inactive")

    def is_active(self): # TODO Botschutz -> BeautifulSoup parse for div#botschutz (?)
        response = requests.get("https://" + self.domain + "/game.php", cookies=dict(sid=self.sid),
                                headers={"user-agent": common.USER_AGENT})
        return response.url.endswith("/game.php")
    
    def get_village_ids(self):
        return [v.village_id for v in self.villages]
    
group_village = db.Table("group_village",
    db.Column("group_id", db.Integer, db.ForeignKey("group.id")),
    db.Column("village_id", db.Integer, db.ForeignKey("village.id")))

class Village(db.Model): #nur eigene Dörfer zum zwischenspeichern der Gruppen und Truppen
    id = db.Column(db.Integer, primary_key=True)
    village_id = db.Column(db.Integer) # muss nicht unique sein über mehrere Welten
    units = db.Column(db.String(255))
    #relationships
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    groups = db.relationship("Group", secondary=group_village, back_populates="villages")

    def __repr__(self):
        return "<Village {} of {} on {}>".format(self.village_id, self.player.name, self.player.domain)

    def get_units(self):
        return ast.literal_eval(self.units)
    
    def get_bh(self):
        unit_bh = common.unit_bh
        units = self.get_units()
        total = 0
        for unit in units:
            total = total + int(units[unit]) * unit_bh[unit]
        return total

    def get_village_name(self):
        name = world_data.get_village_name_from_id(self.player.domain, self.village_id)
        if name:
            return name
        else: 
            return "Dorfname nicht gefunden"

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer)
    name = db.Column(db.String(64))
    is_used = db.Column(db.Boolean, default=False) # Derzeit benutzt für raussteller
    # relationships
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    villages = db.relationship("Village", secondary=group_village, back_populates="groups")

    def __repr__(self):
        return "<Group {} of {}>".format(self.name, self.player.name)
    
    def is_in_group(self, village):
        return 1 in [1 if v.id == village.id else 0 for v in self.villages]
    
    def add_village(self, village):
        if not self.is_in_group(village):
            self.villages.append(village)
    
    def remove_village(self,village):
        if self.is_in_group(village):
            self.villages.remove(village)





def init_db():
    db.create_all()

if __name__ == "__main__":
    init_db()

def init_samples():
    p = Player(name = "st4bel", player_id = "132465", domain = "de183.die-staemme.de")
    g = Group(name = "Test_Gruppe", group_id = "47")
    v = Village(village_id = "9874", units = str(dict(spear = 2, catapult = 100)))

    v.player = p
    g.player = p
    v.groups.append(g)

    db.session.add(p)
    db.session.add(g)
    db.session.add(v)
    db.session.commit()