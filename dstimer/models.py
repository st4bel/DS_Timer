from dstimer.server import db

class Incomings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index = True)

    def __repr__(self):
        return "<Incomings {}>".format(self.name)