CREATE TABLE instruments 
(
    instrument_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    family VARCHAR(50),
    manufacturer VARCHAR(100),
    origin_country VARCHAR(50),
    year_introduced INT,
    price DECIMAL(10, 2),
    description TEXT
);

INSERT INTO instruments 
(
    name, type, family, manufacturer, origin_country,
    year_introduced, price, description
) 
VALUES 
(
    'First Guitar', 'String', 'Guitar', '', '',
    825, 0, 'The first guitar'
);

INSERT INTO instruments 
(
    name, type, family, manufacturer, origin_country,
    year_introduced, price, description
) 
VALUES 
(
    '', 'another type', '', '', '',
    0, 0, ''
);

COPY instruments(name, type, family, manufacturer, origin_country, year_introduced, price, description)
FROM '/docker-entrypoint-initdb.d/musical_instruments.csv'
DELIMITER ',' CSV HEADER;

CREATE INDEX idx_price_btree ON instruments(price);
CREATE INDEX idx_description_gin ON instruments USING GIN (to_tsvector('english', description));
CREATE INDEX idx_instrument_id_brin ON instruments USING BRIN(instrument_id);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX instruments_name_trgm_idx
ON instruments USING GIN (name gin_trgm_ops);

CREATE EXTENSION IF NOT EXISTS pg_bigm;
CREATE INDEX instruments_type_bigm_idx
ON instruments USING GIN (type gin_bigm_ops);
