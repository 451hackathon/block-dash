
import math

import psycopg2
from psycopg2.extras import DictCursor

from flask import current_app, g

__all__ = ['get_counts','get_reports','get_report_count']

PAGESIZE = 10

def cursor():
    c = g.conn.cursor(cursor_factory=DictCursor)
    return c

def get_counts(start, end, interval):
    c = cursor()
    c.execute("""
        select 
            generate_series::date as date, case when ct is null then 0 else ct end as count
        from
            generate_series(%s::timestamptz, %s::timestamptz, interval %s)
            left join (
                select date_trunc('day', date) dt, count(*) ct
                from reports
                group by date_trunc('day', date)
                ) sub1 on sub1.dt = generate_series
            order by generate_series::date
        """,
        [ start, end, '1 ' + interval ]
        )

    data = []
    for row in c:
        yield row
    c.close()

def get_reports(page):
    c = cursor()
    c.execute("""
              select * from reports order by id desc limit {0} offset {1}
              """.format(PAGESIZE, page*PAGESIZE))
    for row in c:
        yield row
    c.close()
    
def get_report_count():
    c = cursor()
    c.execute("select count(*) as ct from reports")
    row = c.fetchone()
    c.close()
    return math.ceil(row['ct'] / float(PAGESIZE))
              
    
