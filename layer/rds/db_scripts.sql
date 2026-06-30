


CREATE TABLE P1P2_Incidents (  
    Inc_id TEXT PRIMARY KEY, -- Primary key column, accepts values like 'inc1225276  
    Raised_Date TIMESTAMP NOT NULL, -- Date and time when the incident was raised  
    Priority VARCHAR(50), -- Priority of the incident  
    Configuration_item VARCHAR(255), -- Configuration item related to the incident  
    Short_description TEXT, -- Short description of the incident  
    State VARCHAR(50), -- State of the incident  
    Business_area_impact TEXT, -- Description of the business area impact  
    Business_category VARCHAR(100), -- Business category of the incident  
    Business_service VARCHAR(255), -- Business service related to the incident  
    Category VARCHAR(100), -- Category of the incident  
    Comments_Worknotes TEXT, -- Comments or worknotes related to the incident  
    Description TEXT, -- Detailed description of the incident  
    Probable_cause TEXT, -- Probable cause of the incident  
    Previous_update TIMESTAMP, -- Timestamp of the previous update  
    Problem TEXT, -- Problem details related to the incident  
    Resolution_notes TEXT, -- Notes about the resolution of the incident  
    Severity VARCHAR(50), -- Severity of the incident  
    MIM_agent_output_Blob BYTEA -- Binary large object for additional data  
);  




CREATE EXTENSION IF NOT EXISTS vector;  
  
 
CREATE TABLE ticket_history_vec (  
    inc_id TEXT PRIMARY KEY,    -- Primary key column, accepts values like 'inc1225276'  
    chunk TEXT,                 -- Text column for the chunk  
    embedding VECTOR(1024),     -- Vector column for embeddings (1536 is a common dimensionality, adjust as needed)  
    ci TEXT,                    -- Text column for ci  
    prb_id TEXT,                -- Text column for problem ID  
    ptask_id TEXT,              -- Text column for task ID  
    link TEXT,                  -- Text column for link  
    summary TEXT                -- Text column for summary  
);  




CREATE TABLE change_history_vec (  
    chg_id TEXT PRIMARY KEY,    -- Primary key column, accepts values like 'inc1225276'  
    chunk TEXT,                 -- Text column for the chunk  
    embedding VECTOR(1024),     -- Vector column for embeddings (1536 is a common dimensionality, adjust as needed)  
    ci TEXT,                    -- Text column for ci   
    link TEXT,                  -- Text column for link  
    summary TEXT                -- Text column for summary  
);

CREATE TABLE change_history_vec (  
    chg_id TEXT PRIMARY KEY,    -- Primary key column, accepts values like 'inc1225276'  
    chunk TEXT,                 -- Text column for the chunk  
    embedding VECTOR(1024),     -- Vector column for embeddings (1536 is a common dimensionality, adjust as needed)  
    ci TEXT,                    -- Text column for ci   
    link TEXT,                  -- Text column for link  
    summary TEXT                -- Text column for summary  
);




CREATE TABLE knowledge_vec (  
    uid SERIAL PRIMARY KEY,         -- Database-generated unique identifier  
    ci TEXT,                        -- A string field for "ci" (adjust length as needed)  
    chunk TEXT,                     -- A text field for storing "chunk"  
    embedding VECTOR(1024),         -- Assuming embedding is stored in JSON format (can be adjusted)  
    knowledge_id TEXT,      	    -- A string field for "knowledge_id"  
    knowledge_type TEXT,            -- A string field for "knowledge_type"  
    source TEXT,                    -- A string field for "source"  
    link TEXT,                      -- A text field for storing "link" (e.g., URLs)  
    summary TEXT                    -- A text field for storing "summary"  
);