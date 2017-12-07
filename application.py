import time
import settings
from flask import Flask, render_template
from flask.ext.restful import reqparse, Api, Resource
from raven.contrib.flask import Sentry
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, distinct, select
from sqlalchemy.exc import IntegrityError
from flask.ext.cors import CORS
from sqlalchemy import or_, and_
from urllib import quote_plus, unquote

from utils import json_response


app = Flask(__name__)

if settings.USE_SENTRY:
    app.config['SENTRY_DSN'] = settings.SENTRY_DSN
    sentry = Sentry(app)

app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = settings.ALCHEMY_URL

api = Api(app)
db = SQLAlchemy(app)
cors = CORS(app, supports_credentials=True)

association_table = Table(
    'association', db.Model.metadata,
    Column('event_id', db.Integer, db.ForeignKey('event.id')),
    Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)


class Event(db.Model):
    """
    Event model

    Attributes:
        id:           the event id
        start_time:   the unix timestamp when the event started; defaults to
                      the time when the event was added
        end_time:     the unix timestamp when the event ended; defaults to
                      start_time
        source:       the event source (e.g. Rundeck, CI, etc.)
        name:         a short description of the event
        description:  a detailed description of the event
        links:        a string of URLs related to the event separated by `|`
                      (e.g. link to phabricator diffs, Rundeck output, etc.)
        tags:         a list of Tag objects related to the event
    """

    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Integer, index=True, nullable=False)
    end_time = db.Column(db.Integer, index=True, nullable=False)
    source = db.Column(db.String(30), nullable=False, index=True)
    name = db.Column(db.String(500), index=True, nullable=False)
    description = db.Column(db.String(1000), index=True)
    links = db.Column(db.String(1000))
    tags = db.relationship('Tag', secondary=association_table)


class Tag(db.Model):
    """
    Tag model

    Attributes:
        id:           the tag id
        name:         the name of the tag (e.g. username, event type, etc.)
        description:  a more detailed description of the tag
    """
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, index=True, nullable=False)
    description = db.Column(db.String(1000), index=True)


class EventList(Resource):

    def get(self):
        query_parser = reqparse.RequestParser()
        query_parser.add_argument('start_time', type=int)
        query_parser.add_argument('end_time', type=int)
        query_parser.add_argument('until', type=int, default=-1)
        query_parser.add_argument('hours_ago', type=int)
        query_parser.add_argument('source', type=unicode)
        query_parser.add_argument('keyword', type=unicode)
        query_parser.add_argument('tag', type=unicode)
        query = query_parser.parse_args()

        event = Event.__table__
        statement = select([
            Event,
            Tag.id.label('tag_id'),
            Tag.name.label('tag_name'),
            Tag.description.label('tag_description')
        ]).select_from(event.outerjoin(association_table).outerjoin(Tag))

        if query['until'] != -1:
            statement = statement.where((and_(
                Event.start_time >= query['until']-query['hours_ago']*3600,
                Event.start_time <= query['until'])
            ))
        else:
            statement = statement.where(
              (and_(Event.start_time >= time.time()-query['hours_ago']*3600))
            )
        if query['source']:
            source = map(unicode, query['source'].split(','))
            statement = statement.where(Event.source.in_(source))
        if query['keyword']:
            statement = statement.where(or_(
                Event.name.like('%{}%'.format(query['keyword'])),
                Event.description.like('%{}%'.format(query['keyword']))
            ))
        if query['tag']:
            tag = map(unicode, query['tag'].split(','))
            statement = statement.where(Tag.name.in_(tag))

        events = {}
        result = db.engine.execute(statement).fetchall()

        for row in result:
            event_id = row['id']
            if event_id not in events:
                events[event_id] = {
                    'id': event_id,
                    'start_time': row['start_time'],
                    'end_time': row['end_time'],
                    'source': row['source'],
                    'name': row['name'],
                    'description': row['description'],
                    'links': ([unquote(link)
                               for link in row['links'].split('|')]
                              if row['links'] else []),
                    'tags': [{
                        'id': row['tag_id'],
                        'description': row['tag_description'],
                        'name': row['tag_name'],
                    }]
                }
            else:
                events[event_id]['tags'].append({
                    'id': row['tag_id'],
                    'description': row['tag_description'],
                    'name': row['tag_name'],
                })

        return json_response(events)

    def post(self):
        json_parser = reqparse.RequestParser()
        json_parser.add_argument('start_time', type=int, location='json')
        json_parser.add_argument('end_time', type=int, location='json')
        json_parser.add_argument('source', type=unicode, required=True,
                                 location='json')
        json_parser.add_argument('name', type=unicode, required=True,
                                 location='json')
        json_parser.add_argument('description', type=unicode, location='json')
        json_parser.add_argument('links', type=list, location='json')
        json_parser.add_argument('tags', type=list, location='json')
        post_event = json_parser.parse_args()

        event = Event()
        event.source = post_event['source']
        event.name = post_event['name']

        if not post_event['start_time']:
            event.start_time = int(time.time())
        else:
            event.start_time = post_event['start_time']
        if post_event['end_time']:
            event.end_time = post_event['end_time']
        else:
            event.end_time = event.start_time
        if post_event['description']:
            event.description = post_event['description']
        if post_event['links']:
            event.links = '|'.join(quote_plus(link)
                                   for link in post_event['links'])

        tags = []
        if post_event['tags']:
            tags_in_db = db.session.query(Tag).filter(
                Tag.name.in_(post_event['tags'])
            ).all()

            for post_tag in post_event['tags']:
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

            event.tags = tags

        db.session.add(event)
        db.session.commit()

        return json_response(
            message='Event was successfully added'
        )

    def put(self):
        json_parser = reqparse.RequestParser()
        json_parser.add_argument('id', type=int, required=True,
                                 location='json')
        json_parser.add_argument('start_time', type=int, location='json')
        json_parser.add_argument('end_time', type=int, location='json')
        json_parser.add_argument('source', type=unicode, location='json')
        json_parser.add_argument('name', type=unicode, location='json')
        json_parser.add_argument('description', type=unicode, location='json')
        json_parser.add_argument('links', type=list, location='json')
        json_parser.add_argument('tags', type=list, location='json')
        event = json_parser.parse_args()
        existing_event = db.session.query(Event).filter(
            Event.id == event['id']
        ).first()

        if not existing_event:
            return json_response(
                message='Event {} not found'.format(event['id']),
                status_code=404
            )

        if event['start_time']:
            existing_event.start_time = event['start_time']
        if event['end_time']:
            existing_event.end_time = event['end_time']
        if event['source']:
            existing_event.source = event['source']
        if event['name']:
            existing_event.name = event['name']
        if event['description']:
            existing_event.description = event['description']
        if event['links']:
            existing_event.links = '|'.join(quote_plus(link)
                                            for link in event['links'])
        if event['tags']:
            event_tags = []

            result = db.session.query(Tag).filter(
                Tag.name.in_(event['tags'])
            ).all()
            tags_in_db = {}
            for tag in result:
                tags_in_db[tag.name] = tag

            for post_tag in event['tags']:
                if post_tag in tags_in_db:
                    event_tags.append(tags_in_db[post_tag])
                else:
                    tag = Tag()
                    tag.name = post_tag
                    db.session.add(tag)
                    db.session.commit()
                    event_tags.append(tag)

            existing_event.tags = event_tags

        db.session.commit()

        return json_response(
            message='Successfully updated Event {}'.format(existing_event.id)
        )


api.add_resource(EventList, '/api/events')


class TagList(Resource):

    def get(self):
        result = db.session.query(Tag).all()
        converted_result = [
            {'id': r.id,
             'name': r.name,
             'description': r.description} for r in result]
        return json_response(converted_result)

    def put(self):
        json_parser = reqparse.RequestParser()
        json_parser.add_argument('id', type=int, required=True,
                                 location='json')
        json_parser.add_argument('description', type=unicode, location='json')
        json_parser.add_argument('name', type=unicode, location='json')

        tag = json_parser.parse_args()
        existing_tag = db.session.query(Tag).filter(
            Tag.id == tag['id']
        ).first()

        if not existing_tag:
            return json_response(
                message='Tag {} not found'.format(tag['id']),
                status_code=404
            )

        try:
            if tag['name']:
                existing_tag.name = tag['name']
            if tag['description']:
                existing_tag.description = tag['description']
            db.session.commit()
        except IntegrityError:
            return json_response(
                message='Tag with name {} already exists'.format(tag.name),
                status_code=422
            )

        return json_response(
            message='Successfully updated Tag {}'.format(existing_tag.id)
        )


api.add_resource(TagList, '/api/tags')


# Healthcheck, supposing that there is at least one element in the database.
@app.route('/healthcheck')
def healthcheck():
    try:
        db_query = db.session.query(Event)
        db_query = db_query.limit(1)
        result = db_query.all()
        if len(result) == 0:
            return json_response(
                message='FAIL: No records were found in the database.',
                status_code=404
            )
        else:
            return json_response(
                message='OK: There is at least one record in the database.'
            )
    except Exception, e:
        return json_response(
            message='FAIL: Unexpected error occured:\n {}'.format(str(e)),
            status_code=500
        )


@app.route('/')
def index():
    statement = select([distinct(Event.source)])
    sources = [
        unicode(entry[0]) for entry in db.engine.execute(statement).fetchall()
    ]
    statement = select([distinct(Tag.name)])
    tag_names = [
        unicode(entry[0]) for entry in db.engine.execute(statement).fetchall()
    ]
    return render_template('index.html', sources=sources, tags=tag_names)


if __name__ == '__main__':
    app.run(debug=True, host=settings.LISTEN_HOST, port=settings.LISTEN_PORT)
