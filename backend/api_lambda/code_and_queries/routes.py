from flask import Flask, jsonify, request
import logging
import os
import json
import awsgi
import traceback
from route_functions import (
    get_user_cars_details,
    create_fake_user_data,
    delete_car_for_user,
    update_car_details_for_user,
    create_car_for_user,
    create_schema
)

ENV = os.environ.get('ENVIRONMENT')
logger = logging.getLogger()

app = Flask(__name__)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    try:
        logger.info("Attempting to process with awsgi")
        response = awsgi.response(app, event, context)
        logger.info(f"AWSGI response: {json.dumps(response)}")
        return response
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }

@app.route(f"/{ENV}/")
def hello_world():
    logger.info("Default route accessed")
    return "<p>default route</p>"

@app.route(f"/{ENV}/health", methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return jsonify({"status": "healthy"})

@app.route(f"/{ENV}/create_db_schema", methods=['POST'])
def db_create_schema():
    logger.info("Create schema endpoint accessed")
    try:
        create_schema()
        return jsonify({"status": "success", "message": "Database schema created"})
    except Exception as e:
        logger.error(f"Error in create_schema endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Get all cars and car data for a user given a uuid
@app.route(f"/{ENV}/user/<uuid:user_uuid>/cars", methods=['GET'])
def get_user_cars(user_uuid):
    logger.info(f"Getting cars for user: {user_uuid}")
    try:
        cars = get_user_cars_details(user_uuid)
        return jsonify({"status": "success", "data": cars})
    except Exception as e:
        logger.error(f"Error in get_user_cars endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route(f"/{ENV}/create_fake_user", methods=['POST'])
def create_fake_user_endpoint():
    logger.info("Create fake user endpoint accessed")
    try:
        user_uuid = create_fake_user_data()
        logger.info(f"Fake user created with UUID: {user_uuid}")
        # Convert UUID to string explicitly
        user_uuid_str = str(user_uuid) if user_uuid else None
        return jsonify({
            "status": "success", 
            "message": "Fake user data created", 
            "user_uuid": user_uuid_str
        })
    except Exception as e:
        logger.error(f"Error in create_fake_user endpoint: {str(e)}")
        # Convert exception to string to ensure no UUID objects
        error_message = str(e)
        return jsonify({"status": "error", "message": error_message}), 500

@app.route(f"/{ENV}/user/<uuid:user_uuid>/car/<int:car_id>", methods=['DELETE'])
def delete_user_car(user_uuid, car_id):
    logger.info(f"Deleting car {car_id} for user: {user_uuid}")
    try:
        result = delete_car_for_user(user_uuid, car_id)
        if result['deleted']:
            return jsonify({"status": "success", "message": f"Car {car_id} successfully deleted"}), 200
        else:
            return jsonify({"status": "error", "message": result['message']}), 404
    except Exception as e:
        logger.error(f"Error in delete_user_car endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route(f"/{ENV}/user/<uuid:user_uuid>/car/<int:car_id>/details", methods=['PUT'])
def update_car_details(user_uuid, car_id):
    logger.info(f"Updating details for car {car_id} owned by user: {user_uuid}")
    try:
        update_data = request.get_json()
        if not update_data:
            return jsonify({"status": "error", "message": "No update data provided"}), 400
        
        result = update_car_details_for_user(user_uuid, car_id, update_data)
        if not result['updated']:
            return jsonify({"status": "error", "message": result['message']}), 404
        
        return jsonify({"status": "success", "data": result['data']}), 200
    except Exception as e:
        logger.error(f"Error in update_car_details endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route(f"/{ENV}/user/<uuid:user_uuid>/car/add_user_car", methods=['POST'])
def add_user_car(user_uuid):
    """Endpoint to add a new car for a specific user."""
    logger.info(f"Received request to add car for user: {user_uuid}")
    
    car_data = request.get_json()
    if not car_data:
        logger.warning("Add car request received without JSON body")
        return jsonify({"status": "error", "message": "Missing car data in request body"}), 400

    try:
        result = create_car_for_user(user_uuid, car_data)
        
        if result["created"]:
            logger.info(f"Successfully added car for user {user_uuid}. Car ID: {result['data']['car_id']}")
            return jsonify({"status": "success", "message": "Car added successfully", "data": result["data"]}), 201 
        else:
            logger.warning(f"Failed to add car for user {user_uuid}: {result['message']}")
            status_code = 404 if result["message"] == "User not found" else 400
            return jsonify({"status": "error", "message": result["message"]}), status_code

    except Exception as e:
        logger.error(f"Unexpected error in add_user_car endpoint for user {user_uuid}: {str(e)}")
        return jsonify({"status": "error", "message": "An internal error occurred"}), 500
