
import json
import datetime
import psycopg2
from psycopg2.extras import DictCursor

from flask import Flask, g, request, jsonify, config, render_template

app = Flask(__name__)
app.config.from_object('settings')

@app.before_request
def db_connect():
    g.conn = psycopg2.connect(app.config['DB'])

@app.route('/')
def index():
    return render_template('index.html', counts=get_counts('2017-06-01','2017-07-01','day'))

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
    data['blockedBy'] = data.pop('blocked_by')
    data['statusText'] = data.pop('status_text')
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

@app.route('/data/rate')
@app.route('/data/rate/<interval>')
@app.route('/data/rate/<interval>/<start>')
@app.route('/data/rate/<interval>/<start>/<end>')
def report_data_rate(start=None, end=None, interval='day'):

    if interval == 'day':
        if start is None:
            start = datetime.date.today().replace(day=1) # start of current month
    elif interval == 'month':
        if start is None:
            start = datetime.date.today().replace(day=1, month=1) # start of current year
    else:
        return jsonify({'error': 'unsupported interval'}), 400

    if end is None:
        today = datetime.date.today()
        end = today.replace(month=today.month+1, day=1) # start of next month

    data = get_counts(start, end, interval)
    g.conn.commit()

    return jsonify(data=data)
        
        
def get_counts(start, end, interval):
    app.logger.info("Start: %s, End: %s", start, end)
    c = g.conn.cursor()
    c.execute("""
        select 
            generate_series::date, case when ct is null then 0 else ct end ct
        from
            generate_series(%s::timestamptz, %s::timestamptz, interval '1 day')
            left join (
                select date_trunc('day', date) dt, count(*) ct
                from reports
                group by date_trunc('day', date)
                ) sub1 on sub1.dt = generate_series
        """,
        [ start, end ]
        )

    data = []
    for row in c:
        app.logger.info(row)
        data.append({'date':row[0].strftime('%Y-%m-%d'), 'count': row[1]})
    c.close()
    return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
