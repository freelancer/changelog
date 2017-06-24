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
from sqlalchemy import or_, and_

app = Flask(__name__)

if settings.USE_SENTRY:
    app.config['SENTRY_DSN'] = settings.SENTRY_DSN
    sentry = Sentry(app)

app.config['SQLALCHEMY_ECHO'] = True

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
query_parser.add_argument('start_time', type=int)
query_parser.add_argument('end_time', type=int)
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
    start_time = db.Column(db.Integer, index=True, nullable=False)
    end_time = db.Column(db.Integer, index=True, nullable=False)
    source =  db.Column(db.String(30), nullable=False)
    description = db.Column(db.String(1000), index=True)
    tags = db.relationship('Tag', secondary=association_table)

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(1000), index=True)
    name = db.Column(db.String(30), unique=True, index=True, nullable=False)

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

        start_time = int(time.time()) - 86400 # 24 hours ago
        end_time = int(time.time()) # now

        if query.get('start_time') is not None:
            start_time = query['start_time']
        if query.get('end_time') is not None:
            end_time = query['end_time']

        statement = statement.where(
            (and_(Event.start_time >= start_time, Event.end_time <= end_time)).self_group() | # both inside
            (and_(Event.start_time <= start_time, Event.end_time >= start_time)).self_group() | # start before
            (and_(Event.start_time <= end_time, Event.end_time >= end_time)).self_group() # both inside
        )

        if query['source'] is not None:
            statement = statement.where(Event.source.in_(source))
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
                    "description": description,
                    "tags" : [{
                        "id" : tag_id,
                        "description" : tag_description,
                        "name" : tag_name,
                    }]
                }
            else:
                events[id]["tags"].append({
                        "id" : tag_id,
                        "description" : tag_description,
                        "name" : tag_name,
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
        else:
            ev.end_time = ev.start_time
        if json['source'] is not None:
            ev.source = json['source']
        if json['description'] is not None:
            ev.description = json['description']

        tags = []
        tags_in_db = db.session.query(Tag).filter(Tag.name.in_(json['tags'])).all() # ['matchmaking','umer']
        for post_tag in json['tags']:
            for db_tag in tags_in_db:
                if post_tag == db_tag.name:
                    tags.append(db_tag)
                    break
            else:
                tg = Tag()
                tg.name = post_tag
                db.session.add(tg)
                db.session.commit()
                tags.append(tg)

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
                tags_in_db = db.session.query(Tag).filter(Tag.name.in_(json['tags'])).all() # ['matchmaking','umer']
                for post_tag in json['tags']:
                    for db_tag in tags_in_db:
                        if post_tag == db_tag.name:
                            tags.append(db_tag)
                            break
                    else:
                        tg = Tag()
                        tg.name = post_tag
                        db.session.add(tg)
                        db.session.commit()
                        tags.append(tg)

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
    sources = [str(entry[0]) for entry in db.engine.execute(statement).fetchall()]
    statement = select([distinct(Tag.name)])
    tag_names = [str(entry[0]) for entry in db.engine.execute(statement).fetchall()]
    return render_template('index.html', sources=sources, tag_names=tag_names)


if __name__ == '__main__':
    app.run(debug=True, host=settings.LISTEN_HOST, port=settings.LISTEN_PORT)
