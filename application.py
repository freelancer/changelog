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
import json
from flask import jsonify

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
json_parser.add_argument('id', type=int, location='json')
json_parser.add_argument('start_time', type=int, location='json')
json_parser.add_argument('end_time', type=int, location='json')
json_parser.add_argument('source', type=unicode, required=True, location='json')
json_parser.add_argument('description', type=unicode, required=True, location='json')
json_parser.add_argument('tags', type=list, location='json')

query_parser = reqparse.RequestParser()
query_parser.add_argument('hours_ago', type=float, required=True)
query_parser.add_argument('until', type=int)
query_parser.add_argument('source', type=unicode)
query_parser.add_argument('description', type=unicode)
query_parser.add_argument('include_tags', type=unicode, action='append')
query_parser.add_argument('exclude_tags', type=unicode, action='append')

association_table = Table('association', db.Model.metadata,
    Column('event_id', db.Integer, db.ForeignKey('event.id')),
    Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Integer, index=True)
    end_time = db.Column(db.Integer, index=True)
    source =  db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(1000), index=True)
    tags = db.relationship('Tag', secondary=association_table)

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(1000), index=True)
    name = db.Column(db.String(30), unique=True, index=True)

db.create_all()

print Tag.__table__.indexes
class EventList(Resource):
    def get(self):
        query = query_parser.parse_args()

        event = Event.__table__

        statement = select([event, Tag]).\
            select_from(event.join(association_table)).\
            where(event.c.id == association_table.c.event_id).\
            where(Tag.id == association_table.c.tag_id)

        if query['source'] is not None:
            statement = statement.where(Event.source.in_(source))
        if query['description'] is not None:
            statement = statement.where(Event.description.like("%%%s%%" % query['description']))
        if query['include_tags'] is not None:
            statement = statement.where(Tag.name.in_(query['include_tags']))
        if query['exclude_tags'] is not None:
            statement = statement.where(~Tag.name.in_(query['exclude_tags']))


        events = {}
        result = db.engine.execute(statement).fetchall()

        for row in result:
            id = row[0]
            start_time = row[1]
            end_time = row[2]
            source = row[3]
            description = row[4]
            tag_id = row[5]
            tag_description = row[6]
            tag_name = row[7]
            if events.get(id) == None:
                events[id] = {
                    "id": id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "source": source,
                    "tags" : [{
                        "id" : tag_id,
                        "description" : tag_description,
                        "tag_name" : tag_name,
                    }]
                }
            else:
                events[id]["tags"].append({
                        "id" : tag_id,
                        "description" : tag_description,
                        "tag_name" : tag_name,
                })


        return events

    def post(self):
        json = json_parser.parse_args()

        ev = Event()
        if json['start_time'] is None:
            ev.start_time = int(time.time())
        else:
            ev.start_time = json['start_time']
        if json['end_time'] is not None:
            ev.end_time = json['end_time']
        if json['source'] is not None:
            ev.source = json['source']
        if json['description'] is not None:
            ev.description = json['description']

        tags = []
        tags_in_db = db.session.query(Tag).all() # ['matchmaking','umer']
        for post_tag in json['tags']:
            tag_found = False
            for db_tag in tags_in_db:
                if db_tag.name == post_tag:
                    tag_found = True
                tags.append(db_tag)
            
            if not tag_found:
                tg = Tag()
                tg.name = post_tag
                db.session.add(tg)
                db.session.commit()

        ev.tags = tags
        db.session.add(ev)
        db.session.commit()

        return 'OK', 201

    def put(self):
        json = json_parser.parse_args()
        result = db.session.query(Event).filter(Event.id == json['id'])

        json_parser.add_argument('start_time', type=int, location='json')
        json_parser.add_argument('end_time', type=int, location='json')
        json_parser.add_argument('source', type=unicode, required=True, location='json')
        json_parser.add_argument('description', type=unicode, required=True, location='json')
        json_parser.add_argument('tags', type=list, required=True, location='json')

        for entry in result:
            if json['start_time'] is not None:
                entry.start_time = json['start_time']
            if json['end_time'] is not None:
                entry.end_time = json['end_time']
            if json['source'] is not None:
                entry.source = json['source']
            if json['description'] is not None:
                entry.description = json['description']
            if json['tags'] is not None:
                tags = []
                tags_in_db = db.session.query(Tag).all() # ['matchmaking','umer']
                for post_tag in json['tags']:
                    tag_found = False
                    for db_tag in tags_in_db:
                        if db_tag.name == post_tag:
                            tag_found = True
                        tags.append(db_tag)
                    
                    if not tag_found:
                        tg = Tag()
                        tg.name = post_tag
                        db.session.add(tg)
                        db.session.commit()

                entry = tags

        db.session.commit()



api.add_resource(EventList, '/api/events')

class TagList(Resource):
    def get(self):
        result = db.session.query(Tag).all()
        converted = [
            {"id": r.id,
             "name": r.name,
             "description": r.description} for r in result]
        return converted


    def put(self):
        json = json_parser.parse_args()
        result = db.session.query(Tag).filter(Tag.id == json['id'])
        for entry in result:
            if json['name'] is not None:
                entry.name = json['name']
            if json['description'] is not None:
                entry.name = json['description']
        db.session.commit()

api.add_resource(TagList, '/api/tags')


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
