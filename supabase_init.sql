-- Create raw_text_chunk table
CREATE TABLE IF NOT EXISTS raw_text_chunk (
    id BIGSERIAL PRIMARY KEY,
    timestamp TEXT,
    filename TEXT,
    speaker TEXT,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create tangent table
CREATE TABLE IF NOT EXISTS tangent (
    id BIGSERIAL PRIMARY KEY,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create text_chunk_tangent_mapping table
CREATE TABLE IF NOT EXISTS text_chunk_tangent_mapping (
    id BIGSERIAL PRIMARY KEY,
    raw_text_chunk_id BIGINT REFERENCES raw_text_chunk(id),
    tangent_id BIGINT REFERENCES tangent(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chapter table
CREATE TABLE IF NOT EXISTS chapter (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create part table
CREATE TABLE IF NOT EXISTS part (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create subsection table
CREATE TABLE IF NOT EXISTS subsection (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    chapter_id BIGINT REFERENCES chapter(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create outline_version table to store autosaves
CREATE TABLE IF NOT EXISTS outline_version (
    id BIGSERIAL PRIMARY KEY,
    name TEXT,
    content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
); 