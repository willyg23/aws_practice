### create_schema_endpoint

CREATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    uuid UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    location VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS cars (
    car_id SERIAL PRIMARY KEY,
    user_uuid UUID NOT NULL REFERENCES users(uuid) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS car_details (
    detail_id SERIAL PRIMARY KEY,
    car_id INTEGER NOT NULL REFERENCES cars(car_id) ON DELETE CASCADE,
    make VARCHAR(100),
    model VARCHAR(100),
    year INTEGER,
    mileage INTEGER,
    last_maintenance_checkup DATE,
    last_oil_change DATE,
    purchase_date DATE,
    last_brake_pad_change DATE
);

CREATE TABLE IF NOT EXISTS error_events (
    error_event_id SERIAL PRIMARY KEY,
    car_id INTEGER NOT NULL REFERENCES cars(car_id) ON DELETE CASCADE,
    error_codes TEXT,
    occurrence_mileage INTEGER,
    occurrence_date DATE
);

CREATE TABLE IF NOT EXISTS error_parts (
    part_id SERIAL PRIMARY KEY,
    error_event_id INTEGER NOT NULL REFERENCES error_events(error_event_id) ON DELETE CASCADE,
    part_name VARCHAR(255)
);

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
"""



### get_user_cars_endpoint

# SQL query to join cars and car_details tables for a specific user
GET_USER_CARS_DETAILS_QUERY = """
SELECT c.car_id, cd.detail_id, cd.make, cd.model, cd.year, cd.mileage, 
       cd.last_maintenance_checkup, cd.last_oil_change, cd.purchase_date, 
       cd.last_brake_pad_change
FROM cars c
LEFT JOIN car_details cd ON c.car_id = cd.car_id
WHERE c.user_uuid = %s
"""



### create_fake_user_endpoint

# SQL query to insert a new user
INSERT_USER_QUERY = """
INSERT INTO users (uuid, email, location) VALUES (%s, %s, %s)
"""

# SQL query to insert a new car and return its ID
INSERT_CAR_QUERY = """
INSERT INTO cars (user_uuid) VALUES (%s) RETURNING car_id
"""

# SQL query to insert car details
INSERT_CAR_DETAILS_QUERY = """
INSERT INTO car_details
(car_id, make, model, year, mileage, last_maintenance_checkup,
last_oil_change, purchase_date, last_brake_pad_change)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""



### delete_user_car_endpoint

# SQL query to verify a car belongs to a user
VERIFY_CAR_BELONGS_TO_USER_QUERY = """
    SELECT car_id FROM cars
    WHERE car_id = %s AND user_uuid = %s
"""

# SQL query to delete a car
DELETE_CAR_QUERY = """
    DELETE FROM cars
    WHERE car_id = %s
"""

### update_car_details_endpoint

# SQL query to verify a car belongs to a user
VERIFY_CAR_OWNERSHIP_QUERY = """
SELECT 1 FROM cars WHERE car_id = %s AND user_uuid = %s
"""

# SQL query to check if car_details record exists
CHECK_CAR_DETAILS_EXIST_QUERY = """
SELECT 1 FROM car_details WHERE car_id = %s
"""

### add_user_car
# Query to verify user exists
CHECK_USER_EXISTS_QUERY = """
SELECT 1 FROM users WHERE uuid = %s
"""

# Query to insert a new car
INSERT_CAR_QUERY = """
INSERT INTO cars (user_uuid) VALUES (%s) RETURNING car_id
"""

# Query to insert car details
INSERT_CAR_DETAILS_QUERY = """
INSERT INTO car_details
(car_id, make, model, year, mileage, last_maintenance_checkup,
 last_oil_change, purchase_date, last_brake_pad_change)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING * 
"""


### get_car_details_endpoint