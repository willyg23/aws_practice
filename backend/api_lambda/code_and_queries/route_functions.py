from datetime import datetime, date, timedelta
import random
import string
import uuid
import os
import logging
import psycopg2
import psycopg2.extras
from sql_queries import (
    GET_USER_CARS_DETAILS_QUERY,
    INSERT_USER_QUERY,
    INSERT_CAR_QUERY, 
    INSERT_CAR_DETAILS_QUERY,
    VERIFY_CAR_BELONGS_TO_USER_QUERY,
    DELETE_CAR_QUERY,
    VERIFY_CAR_OWNERSHIP_QUERY,
    CHECK_CAR_DETAILS_EXIST_QUERY,
    CHECK_USER_EXISTS_QUERY,
    CREATE_SCHEMA
)
psycopg2.extras.register_uuid()

logger = logging.getLogger()

# Database configuration
DB_HOST = "terraform-20250323164944761200000005.cnqq0meu6lwj.us-east-2.rds.amazonaws.com"
DB_NAME = "dev_db"
DB_USER = os.environ.get('DB_USERNAME')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = 5432

def get_db_connection():
    """Establish and return a connection to the database."""
    logger.info(f"Attempting to connect to DB at {DB_HOST}:{DB_PORT}")
    logger.info(f"DB_NAME: {DB_NAME}, DB_USER: {DB_USER}")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def create_schema():
    """Create the database schema if it doesn't exist."""
    conn = None
    try:
        logger.info("new code has been deployed 2")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the entire schema as one statement
        cursor.execute(CREATE_SCHEMA)
        
        # Commit the transaction
        conn.commit()
        logger.info("Database schema created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating schema: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_user_cars_details(user_uuid):
    """Retrieve all cars and their details for a specific user UUID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
                
        cursor.execute(GET_USER_CARS_DETAILS_QUERY, (user_uuid,))
        
        # Fetch all results
        results = cursor.fetchall()
        
        # Format the results
        cars = []
        for row in results:
            car = {
                "car_id": row[0],
                "detail_id": row[1],
                "make": row[2],
                "model": row[3],
                "year": row[4],
                "mileage": row[5],
                "last_maintenance_checkup": row[6].isoformat() if row[6] else None,
                "last_oil_change": row[7].isoformat() if row[7] else None,
                "purchase_date": row[8].isoformat() if row[8] else None,
                "last_brake_pad_change": row[9].isoformat() if row[9] else None
            }
            cars.append(car)
        
        logger.info(f"Retrieved {len(cars)} cars for user {user_uuid}")
        return cars
    except Exception as e:
        logger.error(f"Error retrieving cars for user {user_uuid}: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def create_fake_user_data():
    """Generate and store random fake data for a user, their cars, and car details."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate fake user data
        user_uuid = uuid.uuid4()
        email = f"{''.join(random.choices(string.ascii_lowercase, k=8))}@example.com"
        location = random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"])

        cursor.execute(INSERT_USER_QUERY, (user_uuid, email, location))

        # Generate random number of cars (1-3)
        num_cars = random.randint(1, 3)
        car_ids = []

        for _ in range(num_cars):
            # Insert car into database
            cursor.execute(INSERT_CAR_QUERY, (user_uuid,))
            car_id = cursor.fetchone()[0]
            car_ids.append(car_id)

            # Generate fake car details
            make = random.choice(["Toyota", "Ford", "Honda", "Chevrolet", "Nissan"])
            model = random.choice(["Corolla", "F-150", "Civic", "Silverado", "Altima"])
            year = random.randint(2000, 2023)
            mileage = random.randint(0, 200000)

            # Generate random dates
            last_maintenance_checkup = datetime.now() - timedelta(days=random.randint(30, 365))
            last_oil_change = datetime.now() - timedelta(days=random.randint(30, 180))
            purchase_date = datetime.now() - timedelta(days=random.randint(365, 3650))
            last_brake_pad_change = datetime.now() - timedelta(days=random.randint(30, 365))

            # Insert car details into database
            cursor.execute(
                INSERT_CAR_DETAILS_QUERY,
                (car_id, make, model, year, mileage, last_maintenance_checkup,
                 last_oil_change, purchase_date, last_brake_pad_change)
            )

        # Commit the transaction
        conn.commit()
        logger.info(f"Created user with UUID {user_uuid} and {num_cars} cars")
        return user_uuid
    except Exception as e:
        logger.error(f"Error creating fake user data: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def delete_car_for_user(user_uuid, car_id):
    """Delete a specific car for a user if it belongs to them."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First verify that the car belongs to the user
        cursor.execute(VERIFY_CAR_BELONGS_TO_USER_QUERY, (car_id, user_uuid))
        car = cursor.fetchone()
        
        if not car:
            logger.warning(f"Car {car_id} does not belong to user {user_uuid} or does not exist")
            return {"deleted": False, "message": "Car not found or doesn't belong to this user"}
        
        # Delete the car (cascading delete will remove related records due to ON DELETE CASCADE)
        cursor.execute(DELETE_CAR_QUERY, (car_id,))
        conn.commit()
        
        logger.info(f"Successfully deleted car {car_id} for user {user_uuid}")
        return {"deleted": True}
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error deleting car {car_id} for user {user_uuid}: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def update_car_details_for_user(user_uuid, car_id, update_data):
    """Update car details if the car belongs to the specified user."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify the car belongs to the user
        cursor.execute(VERIFY_CAR_OWNERSHIP_QUERY, (car_id, user_uuid))
        if not cursor.fetchone():
            return {"updated": False, "message": "Car not found or doesn't belong to this user"}

        # Get allowed fields and filter the update data
        allowed_fields = ['make', 'model', 'year', 'mileage', 'last_maintenance_checkup', 
                          'last_oil_change', 'purchase_date', 'last_brake_pad_change']
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not filtered_data:
            return {"updated": False, "message": "No valid fields to update"}
            
        # Check if car_details record exists
        cursor.execute(CHECK_CAR_DETAILS_EXIST_QUERY, (car_id,))
        details_exist = cursor.fetchone()
        
        if details_exist:
            # Update existing record
            set_clause = ", ".join([f"{field} = %s" for field in filtered_data])
            query = f"UPDATE car_details SET {set_clause} WHERE car_id = %s RETURNING *"
            values = list(filtered_data.values()) + [car_id]
        else:
            # Insert new record
            fields = ['car_id'] + list(filtered_data.keys())
            placeholders = ['%s'] * len(fields)
            query = f"INSERT INTO car_details ({', '.join(fields)}) VALUES ({', '.join(placeholders)}) RETURNING *"
            values = [car_id] + list(filtered_data.values())
            
        cursor.execute(query, values)
        result = cursor.fetchone()
        conn.commit()
        
        # Convert to dict and format dates
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, result))
        for k, v in data.items():
            if isinstance(v, (date, datetime)):
                data[k] = v.isoformat()
                
        return {"updated": True, "data": data}
    
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error updating car details: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

def create_car_for_user(user_uuid, car_data):
    """Create a new car and its details for a specific user."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Verify the user exists
        cursor.execute(CHECK_USER_EXISTS_QUERY, (user_uuid,))
        if not cursor.fetchone():
            logger.warning(f"Attempt to add car for non-existent user: {user_uuid}")
            return {"created": False, "message": "User not found"}

        # 2. Insert the new car record to get a car_id
        cursor.execute(INSERT_CAR_QUERY, (user_uuid,))
        car_id = cursor.fetchone()[0]
        logger.info(f"Created new car record with car_id: {car_id} for user {user_uuid}")

        # 3. Prepare and insert the car details
        # Use .get() to handle potentially missing optional fields
        make = car_data.get('make')
        model = car_data.get('model')
        year = car_data.get('year')
        mileage = car_data.get('mileage')
        last_maintenance_checkup = car_data.get('last_maintenance_checkup')
        last_oil_change = car_data.get('last_oil_change')
        purchase_date = car_data.get('purchase_date')
        last_brake_pad_change = car_data.get('last_brake_pad_change')

        cursor.execute(
            INSERT_CAR_DETAILS_QUERY,
            (car_id, make, model, year, mileage, last_maintenance_checkup,
             last_oil_change, purchase_date, last_brake_pad_change)
        )
        
        new_details_record = cursor.fetchone()
        conn.commit()

        # Convert the returned record to a dictionary for the response
        columns = [desc[0] for desc in cursor.description]
        new_car_details = dict(zip(columns, new_details_record))

        # Format dates for JSON response
        for key, value in new_car_details.items():
            if isinstance(value, (date, datetime)):
                new_car_details[key] = value.isoformat() if value else None

        logger.info(f"Successfully created car details for car_id: {car_id}")
        return {"created": True, "data": new_car_details}

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating car for user {user_uuid}: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()
