# 451 Block Dashboard

This project reads reports from the postgres database created by [link], and displays 
the most recent results in pages.  It also shows a graph of the number of reports (by date of effect) 
over the last month.

## Installation, Configuration and execution

* ```pip -r requirements.txt```

* Edit settings.py to set the database connection parameters (a standard postgres connection string)

* python dashboard.py

* Connect to localhost:5000 in a web browser

