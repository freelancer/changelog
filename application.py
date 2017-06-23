import time
from flask import Flask, render_template
from flask.ext.restful import reqparse, Api, Resource
from raven.contrib.flask import Sentry
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, distinct, select
from sqlalchemy.exc import IntegrityError
import settings
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.cors import CORS

app = Flask(__name__)

if settings.USE_SENTRY:
    app.config['SENTRY_DSN'] = settings.SENTRY_DSN
    sentry = Sentry(app)

try:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+settings.DB_PATH
except AttributeError:
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.ALCHEMY_URL

api = Api(app)
db = SQLAlchemy(app)
cors = CORS(app, supports_credentials=True)

json_parser = reqparse.RequestParser()
json_parser.add_argument('start_time', type=int, location='json')
json_parser.add_argument('end_time', type=int, location='json')
json_parser.add_argument('source', type=unicode, required=True, location='json')
json_parser.add_argument('description', type=unicode, required=True, location='json')

query_parser = reqparse.RequestParser()
query_parser.add_argument('hours_ago', type=float, required=True)
query_parser.add_argument('until', type=int)
query_parser.add_argument('source', type=unicode)
query_parser.add_argument('description', type=unicode)


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Integer, index=True)
    end_time = db.Column(db.Integer, index=True)
    source =  db.Column(db.String(30), index=True)
    description = db.Column(db.String(1000), index=True)
    tags = db.relationship('Tag', backref='event',
                                lazy='dynamic')
    def __init__(self, start_time, end_time, source, description):
        self.start_time = start_time
        self.source = source
        self.description = description
        if start_time == None:
            self.start_time = int(time.time())

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    description = db.Column(db.String(1000), index=True)
    name = db.Column(db.String(30), unique=True, index=True)
    def __init__(self, description, name):
        self.name = name
        self.description = description

db.create_all()

print Tag.__table__.indexes
class EventList(Resource):
    def get(self):
        query = query_parser.parse_args()
        db_query = db.session.query(Event)
        # time
        if query['until'] != -1:
            db_query = db_query.filter(Event.start_time >= query['until'] - query['hours_ago'] * 3600)
            db_query = db_query.filter(Event.start_time <= query['until'])
        else:
            db_query = db_query.filter(Event.start_time >= time.time() - query['hours_ago'] * 3600)
        #source
        if query['source'] is not None:
            source = query['source'].split(',')
            db_query = db_query.filter(Event.source.in_(source))
        # description
        if query['description'] is not None:
            db_query = db_query.filter(Event.description.like("%%%s%%" % query['description']))
        result = db_query.order_by(Event.start_time.desc()).all()
        converted = [
            {"start_time": r.start_time,
             "end_time": r.end_time,
             "source": r.source,
             "description": r.description} for r in result]
        return converted

    def post(self):
        json = json_parser.parse_args()
        try:
            ev = Event(json['start_time'], json['end_time'], json['source'], json['description'])
            db.session.add(ev)
            db.session.commit()

        except IntegrityError:
            pass  # This happens if we try to add the same event multiple times
                  # Don't really care about that
        return 'OK', 201


api.add_resource(EventList, '/api/events')

# Healthcheck, supposing that there is at least one element in the database.
@app.route('/healthcheck')
def healthcheck():
    try:
        db_query = db.session.query(Event)
        db_query = db_query.limit(1)
        result = db_query.all()
        if (len(result) == 0):
            return "1 FAIL: No record is found in the database."
        else:
            return "0 OK: There is at least one record in the database."
    except Exception, e:
        return ("1 FAIL: Some exception occured:\n %s" % str(e))

@app.route('/')
def index():
    statement = select([distinct(Event.source)])
    categories = [str(entry[0]) for entry in db.engine.execute(statement).fetchall()]
    return render_template('index.html', categories=categories)


if __name__ == '__main__':
    app.run(debug=True, host=settings.LISTEN_HOST, port=settings.LISTEN_PORT)
