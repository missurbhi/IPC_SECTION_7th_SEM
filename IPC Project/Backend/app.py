# import json
# from flask import Flask, request, jsonify

# # Initialize the Flask application
# app = Flask(__name__)

# # --- Configuration to prevent 405 errors ---
# # By default, Flask routes only accept GET requests. 
# # We explicitly set 'methods=['POST']' to allow POST requests.

# @app.route('/predict', methods=['POST'])
# def predict():
#     """
#     Handles model prediction requests. Requires 'POST' method.
#     The 405 error is fixed by explicitly listing 'POST' in the methods list.
#     """
#     try:
#         # Get JSON data from the request body
#         data = request.get_json(silent=True)
        
#         if not data:
#             return jsonify({"error": "No JSON data received or content-type is incorrect. Did you send JSON?"}), 400

#         # --- Mock Prediction Logic ---
#         # Assuming the input data has a 'features' key
#         if 'features' in data:
#             # Simple mock response based on input length
#             input_length = len(data['features'])
#             mock_result = f"Prediction successful for {input_length} features."
#             confidence = 0.95 if input_length > 3 else 0.70
            
#             return jsonify({
#                 "status": "success",
#                 "result": mock_result,
#                 "confidence_score": confidence,
#                 "input_received": data
#             }), 200
#         else:
#             return jsonify({"error": "Missing 'features' key in request data."}), 400

#     except Exception as e:
#         # Catch all other potential errors (e.g., malformed JSON)
#         return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

# @app.route('/submit_fir', methods=['POST'])
# def submit_fir():
#     """
#     Handles the submission of a First Information Report (FIR). 
#     Requires 'POST' method to submit form data.
#     """
#     try:
#         # Get form or JSON data from the request
#         data = request.get_json(silent=True)
        
#         if not data:
#             # Fallback to form data if JSON is not present
#             data = request.form.to_dict()

#         if not data:
#             return jsonify({"error": "No data received for FIR submission."}), 400
        
#         # --- Mock FIR Submission Logic ---
#         required_fields = ['name', 'address', 'incident_details']
#         if not all(field in data for field in required_fields):
#             return jsonify({"error": "Missing required FIR fields (name, address, incident_details)."}), 400
            
#         # Mock database insertion (in a real app, this would save to Firestore)
#         fir_id = f"FIR-{abs(hash(json.dumps(data))) % 10000}"
        
#         return jsonify({
#             "status": "FIR Submitted",
#             "message": "Your FIR has been recorded.",
#             "fir_id": fir_id,
#             "submitted_data_preview": {k: data[k] for k in required_fields}
#         }), 201 # 201 Created

#     except Exception as e:
#         return jsonify({"error": f"An unexpected error occurred during FIR submission: {str(e)}"}), 500


# # The default route for testing connectivity
# @app.route('/')
# def home():
#     return "API is running. Use POST on /predict or /submit_fir."

# if __name__ == '__main__':
#     # Running the app will now correctly accept POST requests on the specified routes
#     app.run(debug=True, port=8000)


# app.py or models.py
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import os

# --- Configuration ---
app = Flask(__name__)

# Replace placeholders with your actual MySQL credentials
# Format: 'mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME'
# Make sure the database (e.g., 'project_data') is already created on your server.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root123@localhost:3306/ipc_section'

# Optional: Disable tracking overhead
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Model ---
class DataPoint(db.Model):
    __tablename__ = 'visualization_data' # Optional: name the table
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(50), nullable=False)
    sales = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<DataPoint {self.month}: {self.sales}>"

# --- Database Initialization and Sample Data Insertion ---
def initialize_database():
    with app.app_context():
        db.create_all() # Create tables if they don't exist

        # Check if the table is empty and insert sample data
        if not DataPoint.query.first():
            print("Inserting sample data...")
            sample_data = [
                DataPoint(month='Jan', sales=150),
                DataPoint(month='Feb', sales=220),
                DataPoint(month='Mar', sales=180),
                DataPoint(month='Apr', sales=300),
                DataPoint(month='May', sales=250)
            ]
            db.session.add_all(sample_data)
            db.session.commit()
            print("Sample data inserted successfully.")
        else:
            print("Database already populated.")

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page for the visualization."""
    return render_template('index.html')

@app.route('/data')
def chart_data():
    """Fetches data from the MySQL database and returns it as JSON."""
    try:
        results = DataPoint.query.all()
        
        # Prepare two lists for Chart.js
        labels = [item.month for item in results]
        values = [item.sales for item in results]
        
        # Return as JSON
        return jsonify({
            'labels': labels,
            'values': values
        })
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching data: {e}")
        return jsonify({'error': 'Failed to fetch data from database'}), 500


# --- Run Application ---
if __name__ == '__main__':
    initialize_database() # Initialize and populate the database
    app.run(debug=True)