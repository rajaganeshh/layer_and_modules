CREATE EXTENSION IF NOT EXISTS vector;  
 
DROP TABLE IF EXISTS public.agent_run_status;
 
CREATE TABLE IF NOT EXISTS public.agent_run_status
(
    entry_time_stamp timestamp without time zone,
    incident_id text COLLATE pg_catalog."default",
    run_status text COLLATE pg_catalog."default",
    processed_by_agent text COLLATE pg_catalog."default",
    exit_time_stamp timestamp without time zone
);
 
DROP TABLE IF EXISTS public.change_history_vec;
 
CREATE TABLE IF NOT EXISTS public.change_history_vec
(
    chg_id text COLLATE pg_catalog."default" NOT NULL,
    chunk text COLLATE pg_catalog."default",
    embedding vector(1024),
    ci text COLLATE pg_catalog."default",
    link text COLLATE pg_catalog."default",
    summary text COLLATE pg_catalog."default",
    CONSTRAINT change_history_vec_pkey PRIMARY KEY (chg_id)
);
 
DROP TABLE IF EXISTS public.incident_update_queue;
 
CREATE TABLE IF NOT EXISTS public.incident_update_queue
(
    incident_id text COLLATE pg_catalog."default",
    request_payload jsonb NOT NULL,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    processed boolean DEFAULT false
);
 
DROP TABLE IF EXISTS public.knowledge_vec;
 
CREATE TABLE IF NOT EXISTS public.knowledge_vec
(
    uid integer NOT NULL DEFAULT nextval('knowledge_vec_uid_seq'::regclass),
    ci text COLLATE pg_catalog."default",
    chunk text COLLATE pg_catalog."default",
    embedding vector(1024),
    knowledge_id text COLLATE pg_catalog."default",
    knowledge_type text COLLATE pg_catalog."default",
    source text COLLATE pg_catalog."default",
    link text COLLATE pg_catalog."default",
    summary text COLLATE pg_catalog."default",
    CONSTRAINT knowledge_vec_pkey PRIMARY KEY (uid)
);
 
 
DROP TABLE IF EXISTS public.p1p2_incidents;
 
CREATE TABLE IF NOT EXISTS public.p1p2_incidents
(
    inc_id text COLLATE pg_catalog."default" NOT NULL,
    raised_date timestamp without time zone NOT NULL,
    priority character varying(50) COLLATE pg_catalog."default",
    cmdb_ci character varying(255) COLLATE pg_catalog."default",
    short_description text COLLATE pg_catalog."default",
    state character varying(50) COLLATE pg_catalog."default",
    business_area_impact text COLLATE pg_catalog."default",
    business_category character varying(100) COLLATE pg_catalog."default",
    business_service character varying(255) COLLATE pg_catalog."default",
    category character varying(100) COLLATE pg_catalog."default",
    comments_worknotes text COLLATE pg_catalog."default",
    description text COLLATE pg_catalog."default",
    probable_cause text COLLATE pg_catalog."default",
    previous_update timestamp without time zone,
    problem text COLLATE pg_catalog."default",
    resolution_notes text COLLATE pg_catalog."default",
    severity character varying(50) COLLATE pg_catalog."default",
    mim_agent_output_blob bytea,
    CONSTRAINT p1p2_incidents_pkey PRIMARY KEY (inc_id)
);
 
 
DROP TABLE IF EXISTS public.sessions;
 
CREATE TABLE IF NOT EXISTS public.sessions
(
    id uuid NOT NULL,
    "accessToken" text COLLATE pg_catalog."default",
    "refreshToken" text COLLATE pg_catalog."default",
    userid text COLLATE pg_catalog."default",
    expiry timestamp with time zone,
    "createdAt" timestamp with time zone NOT NULL,
    "updatedAt" timestamp with time zone NOT NULL,
    CONSTRAINT sessions_pkey PRIMARY KEY (id)
);
 
DROP TABLE IF EXISTS public.ticket_history_vec;
 
CREATE TABLE IF NOT EXISTS public.ticket_history_vec
(
    inc_id text COLLATE pg_catalog."default" NOT NULL,
    chunk text COLLATE pg_catalog."default",
    embedding vector(1024),
    ci text COLLATE pg_catalog."default",
    prb_id text COLLATE pg_catalog."default",
    ptask_id text COLLATE pg_catalog."default",
    link text COLLATE pg_catalog."default",
    summary text COLLATE pg_catalog."default",
    CONSTRAINT ticket_history_vec_pkey PRIMARY KEY (inc_id)
);