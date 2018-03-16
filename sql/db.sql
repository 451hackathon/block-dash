
-- postgres database schema

CREATE TABLE reports (
    id serial primary key not null,
    url text not null, 
	creator text not null,
	version text not null, 
	status int not null, 
	status_text text not null, 
	blocked_by text not null, 
	date timestamptz not null,
	created timestamptz not null
);

CREATE INDEX rpt_url on reports (url);
CREATE INDEX rpt_date on reports (date);
