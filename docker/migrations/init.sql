CREATE TABLE pvz (
    id text primary key,
    register_date date NOT NULL,
    city text NOT NULL
);

CREATE TYPE status AS ENUM ('in_progress', 'close');

CREATE TABLE reception (
    id text primary key,
    reception_datetime TIMESTAMP NOT NULL,
    pvz_id text NOT NULL REFERENCES pvz(id),
    status status,
    products text[]
);

CREATE TYPE productType AS ENUM ('электроника', 'одежда', 'обувь');

CREATE TABLE product (
    id text PRIMARY KEY,
    received_datetime TIMESTAMP NOT NULL,
    product_type productType,
    reception_id text NOT NULL REFERENCES reception(id)
);

CREATE TYPE role AS ENUM ('client', 'moderator', 'employee');

CREATE TABLE users(
    id text PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    role role
);
