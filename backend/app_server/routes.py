from flask import Flask, jsonify, request
import os
import math
import time
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

def generate_gpt_response(prompt, model):
    # CPU-intensive work: perform a heavy calculation to max out compute
    # This loop runs a large number of iterations, computing square roots.
    load_iterations = 10**7  # Adjust this value if needed to increase/decrease load
    dummy = 0.0
    for i in range(1, load_iterations):
        dummy += math.sqrt(i)
    
    # After the heavy computation, return a dummy response
    response_message = f"Stress test complete for prompt: {prompt} (model: {model})"
    print(response_message)
    return response_message

@app.route('/generate-gpt-response', methods=['POST'])
def return_generated_response():
    try:
        data = request.json
        if not data or 'prompt' not in data or 'model' not in data:
            return jsonify({"error": "Missing prompt or model"}), 400

        response_text = generate_gpt_response(data.get('prompt'), data.get('model'))
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def hello_world():
    return "<p>default route</p>"

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)))
    # For local development, change port to 5000 if needed.
