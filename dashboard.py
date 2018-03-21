#!/usr/bin/env python2.7

import json
import datetime
import psycopg2
from psycopg2.extras import DictCursor

from flask import Flask, g, request, jsonify, config, render_template

from db import * # database query functions
from utils import * # utility and calendar functions

app = Flask(__name__)
app.config.from_object('settings')

@app.before_request
def db_connect():
    g.conn = psycopg2.connect(app.config['DB'])

@app.after_request
def db_commit():
    g.conn.commit()

@app.route('/')
@app.route('/page/<int:page>')
def index(page=1):
    return render_template('index.html', 
                           counts=({'date':str(x['date']), 'count':x['count']}
                                    for x in 
                                    get_counts(get_start_current_month(),
                                               get_start_next_month(),
                                               'day')),
                           page=page,   
                           pagecount=get_report_count(),  
                           reports=get_reports(page-1))

### Reporting API

@app.route('/report/<int:id>', methods=['GET'])
def load_report(id):
    c = g.conn.cursor(cursor_factory=DictCursor)
    c.execute("select * from reports where id = %s", [id])
    row = c.fetchone()
    c.close()
    g.conn.commit()
    if row is None:
        return jsonify({'error': 'not found'}), 404
    data = row.copy()
    return jsonify(**data)

@app.route('/report', methods=['POST'])
def report():
    """Writes a JSON 451 report to the database."""

    f = request.json
    c = g.conn.cursor()
    try:
        c.execute("""
            insert into reports
                (url, creator, version, status, status_text, blocked_by, date, created)
            values 
                (%s,%s,%s,%s,%s,%s,%s, now())
            returning id as id
            """,
            [f['url'], f['creator'], f['version'], f['status'], f['statusText'], f['blockedBy'], f['date']]
            )
        newrecord = c.fetchone()
        app.logger.info("Created record %s for %s", newrecord[0], f['url'])
        c.close()
        g.conn.commit()
        return jsonify(id=newrecord[0]), 201
    except psycopg2.Error as exc:
        app.logger.warn("Database error: %s", repr(exc))
        g.conn.rollback()
        return jsonify({'error':repr(exc)}), 400

### Summary views

@app.route('/view/rate')
@app.route('/view/rate/<interval>')
@app.route('/view/rate/<interval>/<start>')
@app.route('/view/rate/<interval>/<start>/<end>')
def report_data_rate(start=None, end=None, interval='day'):

    if interval == 'day':
        if start is None:
            start = get_start_current_month()
    elif interval == 'month':
        if start is None:
            start = get_start_current_year()
    else:
        return jsonify({'error': 'unsupported interval'}), 400

    if end is None:
        today = datetime.date.today()
        end = get_start_next_month  # start of next month

    data = get_counts(start, end, interval)
    g.conn.commit()

    return jsonify(data=data)
        


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
