import time
import joblib
import json
import pymysql 
import pymysql.cursors
import traceback
import decimal 
import uuid
# CRITICAL: If you use the CustomJSONEncoder, ensure all non-standard types are imported
from datetime import date, datetime, timedelta 
from flask import Flask, jsonify, request, Response ,abort
from json import JSONEncoder 
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from flask_bcrypt import Bcrypt 
import datetime as dt # Import datetime module with alias for clarity in transactions
import sys
from flask_cors import CORS 
import logging
import datetime # <--- ONLY import the module 'datetime'
import decimal
import traceback




# Add these at the very top with your other imports
# import requests
import json 
import time # Needed for exponential backoff during API calls

# ... (Existing DB_CONFIG and other app setup) ..




# Define a Custom JSON Encoder to handle non-standard types like Decimal, DateTime, and Timedelta
class CustomJSONEncoder(JSONEncoder):
	"""
	Extends Python's default JSONEncoder to handle additional non-serializable 
	types commonly encountered with MySQL/PyMySQL.
	"""
	def default(self, obj):
		# Handle datetime and date objects
		if isinstance(obj, (datetime, date)):
			return obj.isoformat()
		# Handle timedelta objects 
		elif isinstance(obj, timedelta):
			# Convert timedelta to a string representation (e.g., "0:05:00")
			return str(obj)
		# Handle Decimal objects (e.g., from numeric/money fields)
		elif isinstance(obj, decimal.Decimal): 
			# Convert Decimal to float for JSON
			return float(obj)
		# Catch any other custom/non-serializable types and return as string
		elif hasattr(obj, '__dict__') and isinstance(obj, object):
			return str(obj)
		
		return super(CustomJSONEncoder, self).default(obj)

app = Flask(__name__)
# Apply the custom encoder to the Flask app
# app.json_encoder = CustomJSONEncoder 

# --- FIX 1: Uncommented CORS(app) to fix 'Failed to Fetch' ---
CORS(app) 
# logging.basicConfig(level=logging.DEBUG)
bcrypt = Bcrypt(app) 
# Replace with your actual database credentials
DB_CONFIG = {
	'host': '127.0.0.1',
	'user': 'root',
	'password': 'root123',
	'db': 'ipc_section',
	'cursorclass': pymysql.cursors.DictCursor # Ensures results are returned as dictionaries
}

def get_db_connection():
	"""Establishes a connection to the MySQL database."""
	try:
		connection = pymysql.connect(**DB_CONFIG)
		return connection
	except Exception as e:
		print(f"Error connecting to database: {e}")
		return None

def check_db_connection(max_retries=5, delay=5):
	"""Checks the database connection with retries."""
	for i in range(max_retries):
		connection = get_db_connection()
		if connection:
			print("✅ Database connection successful! Ready to accept requests.")
			connection.close()
			return True
		else:
			print(f"❌ Attempt {i + 1}/{max_retries}: Database connection failed.")
			if i < max_retries - 1:
				print(f"     Retrying in {delay} seconds...")
				time.sleep(delay)
	print("❌ All connection attempts failed. Application will not start.")
	return False

# Load the trained model at startup
try:
	model = joblib.load('trained_model.joblib')
	print("✅ Machine learning model loaded successfully.")
except Exception as e:
	print(f"❌ Error loading the machine learning model: {e}")
	model = None


try:
    # Attempt to import the library
    from google import genai
    print("Attempting to initialize Gemini client...")
    # Client initialization automatically uses the GEMINI_API_KEY environment variable
    client = genai.Client()
    print("Gemini client initialized successfully.")
    
except ImportError:
    print("FATAL: 'google-genai' library not found. Please run 'pip install google-genai'.")
    client = None
except Exception as e:
    # Catching issues like a missing or invalid API key
    print(f"ERROR: Could not initialize Gemini client: {e}")
    client = None


@app.route('/predict_ipc', methods=['POST'])
@cross_origin()
def predict_ipc():
    """
    Handles the request, calls the real Gemini API for structured IPC prediction, 
    and returns the result.
    """
    data = request.get_json()
    if not data or 'description' not in data or 'offence_type' not in data:
        # 400 Bad Request: Missing required data
        return jsonify({"error": "Missing 'description' or 'offence_type' in request."}), 400

    description = data['description']
    offence_type = data['offence_type']

    # --- Fallback Check ---
    if client is None:
        print("Falling back to MOCK data due to client initialization error.")
        mock_result = MOCK_PREDICTIONS.get(offence_type, MOCK_PREDICTIONS["Other"])
        return jsonify(mock_result), 200

    # --- Real Gemini API Call Logic ---
    try:
        # 1. Define the system prompt (Model's role)
        system_prompt = (
            "You are an expert legal assistant specializing in the Indian Penal Code (IPC). "
            "Analyze the user's incident description and assign the single, most appropriate IPC section, "
            "providing a concise justification based strictly on the legal definitions."
        )
        
        # 2. Define the user query (The task)
        user_prompt = (
            f"Offence Type: {offence_type}. "
            f"Incident Description: {description}. "
            f"Based on this, predict the single best IPC Section and provide a concise justification."
        )
        
        # 3. Configuration to force structured JSON output
        config = {
            "systemInstruction": system_prompt,
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "predicted_ipc": {"type": "STRING", "description": "The exact IPC section (e.g., 'IPC Section 379')."},
                    "justification": {"type": "STRING", "description": "A concise explanation of why this section applies to the incident."}
                },
                "propertyOrdering": ["predicted_ipc", "justification"] # Ensure order is consistent
            }
        }
        
        # 4. Call the Model
        response = client.models.generate_content(
            model='gemini-2.5-flash-preview-09-2025',
            contents=[{'parts': [{'text': user_prompt}]}],
            config=config
        )
        
        # 5. Extract and Parse the JSON text
        response_json_text = response.text.strip()
        prediction_data = json.loads(response_json_text)
        
        # 6. Verify the required keys are present
        if 'predicted_ipc' not in prediction_data or 'justification' not in prediction_data:
             return jsonify({"error": "AI response was successful but failed structural validation."}), 500

        # Return the structured JSON response to the frontend
        return jsonify(prediction_data), 200

    except json.JSONDecodeError:
        print(f"Failed to parse JSON response from Gemini: {response.text}")
        return jsonify({"error": "AI returned malformed data."}), 500
    except Exception as e:
        # General catch for network issues, API errors, etc.
        print(f"Gemini API call failed: {e}")
        return jsonify({"error": f"Internal Server Error during AI prediction: {str(e)}"}), 500



@app.route('/submit_fir', methods=['POST'])
def submit_fir():
    """
    Handles the submission of FIR data, inserting into a MySQL database.
    """
    # 1. Input validation
    fir_data = request.get_json(silent=True)
    if not fir_data:
        logging.warning("Received non-JSON data at /submit_fir.")
        return jsonify({
            'error': 'Invalid JSON data received.',
            'detail': 'Ensure Content-Type: application/json header is set.'
        }), 400

    # 2. Extract and structure data with safe defaults
    unique_tracking_id = str(uuid.uuid4())
    # Use .get({}, {}) to safely initialize dictionaries, ensuring no crash if keys are missing
    complainant = fir_data.get('complainant', {})
    incident = fir_data.get('incident', {})
    accused = fir_data.get('accused', {})
    witnesses = fir_data.get('witnesses', [])
    witnesses_json = json.dumps(witnesses)
    
    # NOTE: The column order MUST match the order they appear in the table schema.
    sql = """
    INSERT INTO complaints (
        complainant_name, complainant_father_name, complainant_address, complainant_mobile, complainant_email,
        incident_date, incident_time, incident_place, offence_type, incident_description,
        accused_name, accused_address, accused_description,
        witnesses, predicted_ipc, status, rejection_reason, fir_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # CRITICAL FIX: Use .get(key, '') for all string/date/time fields 
    # to ensure Python sends an empty string instead of NULL if the key is missing.
    values = (
        # Complainant Details (5 fields)
        complainant.get('name', ''), complainant.get('fatherName', ''), complainant.get('address', ''),
        complainant.get('mobile', ''), complainant.get('email', ''),
        # Incident Details (5 fields)
        incident.get('date', ''), incident.get('time', ''), incident.get('place', ''),
        incident.get('offenceType', ''), incident.get('description', ''),
        # Accused Details (3 fields)
        accused.get('name', ''), accused.get('address', ''), accused.get('description', ''),
        # Witnesses, IPC, Status, Rejection Reason, fir_id (5 fields)
        witnesses_json,
        fir_data.get('predicted_ipc', 'N/A'),
        'Pending', # status (VARCHAR(20) NOT NULL, Default 'Pending')
        '',        # rejection_reason (TEXT, Nullable, default empty string to be safe)
        unique_tracking_id # fir_id (VARCHAR(255) NOT NULL, which must be the last field)
    )
    
    try:
        # 3. Database transaction
        # NOTE: If get_db_connection() is not correctly implemented to return a database connection, 
        # it will throw a NotImplementedError, which is caught below.
        with get_db_connection() as connection:
            cursor = connection.cursor()
            
            cursor.execute(sql, values)
            connection.commit()
            cursor.close()
            
        logging.info(f"FIR successfully submitted with Tracking ID: {unique_tracking_id}")

        # 4. Success response
        return jsonify({
            'message': 'FIR submitted successfully!',
            'tracking_id': unique_tracking_id
        }), 201

    # Using a generic database exception (or the specific one if you know the library)
    except Exception as e:
        # --- ENHANCED ERROR LOGGING ---
        # This catch is now robust against the previous NameError for MySQLError and logging
        logging.error("--- Submission Failed ---")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Error Details: {e}")
        logging.error(f"SQL Query (Attempted): {sql.strip().replace('\n', ' ')}")
        logging.error(f"Values (Attempted): {values}")
        logging.error("------------------------------")
        
        # 5. Error response
        if 'NotImplementedError' in str(e):
             return jsonify({'error': 'Database Connection Error', 'detail': 'The get_db_connection() function is a placeholder and must be implemented with your actual database credentials and logic.'}), 500
        
        return jsonify({'error': f"Internal Server/Database Error: {str(e)}", 'detail': 'Check server logs for detailed traceback.'}), 500




@app.route('/police_dashboard_summary', methods=['GET'])
def police_dashboard_summary():
	"""
	Fetches comprehensive complaint summary data from the MySQL database.
	"""
	
	# Initialize variables to zero/empty
	total_complaints = 0
	pending_complaints = 0
	accepted_complaints = 0
	rejected_complaints = 0
	case_type_summary_list = []
	
	conn = get_db_connection()
	if conn is None:
		# If connection fails, return initialized zero values
		return jsonify({
			"total_complaints": 0, "pending_complaints": 0, "accepted_complaints": 0, 
			"rejected_complaints": 0, "case_type_summary": [] 
		})
	
	# Cursor uses DictCursor because it's defined in DB_CONFIG
	cursor = conn.cursor() 
	
	try:
		
		# ------------------------------------------------------------------
		# STEP 1: FETCH STATUS COUNTS (Total, Pending, Accepted, Rejected)
		# ------------------------------------------------------------------
		
		# Query to get all status counts in one go (using conditional aggregation)
		status_query = """
		SELECT 
			COUNT(*) AS total_count,
			SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
			SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS accepted_count,
			SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count
		FROM complaints;
		"""
		cursor.execute(status_query)
		status_data = cursor.fetchone()
		
		if status_data:
			total_complaints = status_data['total_count']
			pending_complaints = status_data['pending_count']
			accepted_complaints = status_data['accepted_count']
			rejected_complaints = status_data['rejected_count']


		# ------------------------------------------------------------------
		# STEP 2: FETCH CASE TYPE SUMMARY (for the Bar Chart)
		# ------------------------------------------------------------------
		
		# Query to group complaints by 'case_type' and count them
		case_type_query = """
		SELECT offence_type AS type, COUNT(*) AS count
		FROM complaints
		GROUP BY offence_type
		ORDER BY count DESC;
		"""
		cursor.execute(case_type_query)
		
		# Format the results into the list of dictionaries the frontend expects
		case_type_summary_list = [
			{'type': row['type'], 'count': row['count']}
			for row in cursor.fetchall()
		]

	# --- FIX 2: Corrected error type from mysql.connector.Error to pymysql.Error ---
	except pymysql.Error as err:
		print(f"Database query error: {err}")
		# On error, the initialized zero/empty values will be used
		
	finally:
		# 3. CLOSE CONNECTION
		cursor.close()
		conn.close()
	
	# 4. Return the complete JSON object
	return jsonify({
		"total_complaints": total_complaints,
		"pending_complaints": pending_complaints,
		"accepted_complaints": accepted_complaints,
		"rejected_complaints": rejected_complaints,
		"case_type_summary": case_type_summary_list 
	})
	

@app.route('/case_type_data', methods=['GET']) # Renamed from /complaint_offence_summary
@cross_origin()
def case_type_data_for_chart():
	"""
	NEW ROUTE: Calculates and returns the counts of complaints grouped by offence_type 
	(Assault, Rape, Theft, Lost Document) specifically for the Chart.js Bar Chart.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		with connection.cursor() as cursor:
			# SQL Query to group by offence_type (your specific case types)
			sql = """
				SELECT offence_type, COUNT(*) AS count 
				FROM complaints 
				WHERE offence_type IS NOT NULL AND offence_type != '' 
				GROUP BY offence_type
				ORDER BY count DESC
			"""
			cursor.execute(sql)
			offence_counts = cursor.fetchall()
			
			# Transform the list of dictionaries into a Chart.js friendly format
			labels = [row['offence_type'] for row in offence_counts]
			values = [row['count'] for row in offence_counts]

			response_data = {
				"labels": labels,
				"values": values
			}
			
			# Manually dump the result using our custom encoder
			json_output = json.dumps(response_data, cls=CustomJSONEncoder)
			return Response(json_output, mimetype='application/json')

	except Exception as e:
		print(f"ERROR in /case_type_data: {e}")
		traceback.print_exc()
		return jsonify({"error": "Failed to fetch complaint case type data."}), 500
	finally:
		if connection:
			connection.close()



# generate unique fir_id
@app.route('/generate_fir_id', methods=['GET'])
def generate_fir_id():
	"""
	Generates the next unique, sequential FIR ID (YYYY/SEQ) and saves 
	a placeholder record into the 'complaints' table, all within a transaction.
	"""
	conn = get_db_connection() 
	if not conn:
		return jsonify({"error": "Database connection failed"}), 500

	cursor = conn.cursor()
	current_year = dt.datetime.now().year
	
	try:
		# 1. START TRANSACTION (Crucial for atomic operation)
		conn.start_transaction() 
		
		# 2. SELECT and LOCK the current sequence number for the current year.
		query_select_and_lock = """
		SELECT next_fir_sequence FROM sequences 
		WHERE year = %s FOR UPDATE;
		"""
		cursor.execute(query_select_and_lock, (current_year,))
		result = cursor.fetchone()

		if result:
			# Row for the current year exists: calculate next sequence
			# result is a tuple (last_sequence,) because cursor was not DictCursor here
			last_sequence = result[0] 
			next_sequence = last_sequence + 1
			
			# Update the sequence table with the new, incremented value
			query_sequence_op = """
			UPDATE sequences SET next_fir_sequence = %s 
			WHERE year = %s;
			"""
			cursor.execute(query_sequence_op, (next_sequence, current_year))
		else:
			# New year entry: start the sequence at 1, insert new row
			next_sequence = 1
			query_sequence_op = """
			INSERT INTO sequences (year, next_fir_sequence) 
			VALUES (%s, %s);
			"""
			cursor.execute(query_sequence_op, (current_year, next_sequence))
		
		# 3. Format the full FIR ID
		sequence_str = str(next_sequence).zfill(4) 
		fir_id = f"{current_year}/{sequence_str}"
		
		# 4. INSERT the generated FIR ID into the 'complaints' table
		# This creates the placeholder record, ensuring the ID is reserved.
		current_timestamp = dt.datetime.now()
		
		query_insert_complaint = """
		UPDATE complaints SET fir_id = %s, status = %s, created_at = %s 
		WHERE fir_id = 'Draft'
		"""
		# If the placeholder was created on the frontend, update it. If not, insert a new one.
		# A simpler logic is used here by attempting to update. 
		# If you need to reserve the ID, the logic of INSERT and subsequent UPDATE is generally safer.
		# For this exercise, we will assume a placeholder needs to be created, so we'll use INSERT.
		
		query_insert_complaint = """
		INSERT INTO complaints (fir_id, status, created_at) 
		VALUES (%s, %s, %s);
		"""
		# We assume minimal columns are required for a placeholder record:
		cursor.execute(query_insert_complaint, (fir_id, 'Draft', current_timestamp))
		
		# 5. COMMIT the transaction (If the sequence update and complaint insert both succeeded)
		conn.commit()
		
		print(f"SUCCESS: FIR ID {fir_id} generated and placeholder created.")

		return jsonify({
			"fir_id": fir_id,
			"year": current_year,
			"sequence": next_sequence,
			"status": "Draft"
		}), 200

	except Exception as err:
		# 6. ROLLBACK the transaction on any error (Releases the lock and discards both sequence increment and complaint insert)
		print(f"Database Error during FIR ID generation and saving: {err}")
		conn.rollback() 
		return jsonify({"error": "Failed to generate and save FIR ID due to database error."}), 500
	finally:
		# Always close the resources
		if cursor:
			cursor.close()
		if conn:
			conn.close()


@app.route('/complaint_offence_summary', methods=['GET'])
@cross_origin()
def complaint_offence_summary():
	"""
	Calculates and returns the counts of complaints grouped by offence type.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		with connection.cursor() as cursor:
			# Get counts by offence_type
			sql = """
				SELECT offence_type, COUNT(*) AS count 
				FROM complaints 
				WHERE offence_type IS NOT NULL AND offence_type != '' 
				GROUP BY offence_type
				ORDER BY count DESC
			"""
			cursor.execute(sql)
			offence_counts = cursor.fetchall()
			
			# Manually dump the result using our custom encoder
			json_output = json.dumps(offence_counts, cls=CustomJSONEncoder)
			return Response(json_output, mimetype='application/json')

	except Exception as e:
		print(f"ERROR in /complaint_offence_summary: {e}")
		traceback.print_exc()
		return jsonify({"error": "Failed to fetch complaint offence summary data."}), 500
	finally:
		if connection:
			connection.close()




#signup
@app.route('/sign_up', methods=['POST'])
@cross_origin()
def sign_up():
	"""
	Registers a new user account, hashes the password, and stores the creation date.
	Expects JSON: {"name": "...", "email": "...", "password": "..."}
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		data = request.get_json(silent=True)
		# The validation must check for 'password' (sent by client), not 'password_hash'
		if not all(k in data for k in ('name', 'email', 'password')):
			return jsonify({'error': 'Missing required fields: name, email, and password are required.'}), 400

		name = data['name']
		email = data['email']
		# Retrieve the raw password using the key 'password'
		raw_password = data['password'] 
		
		# 1. Check if user already exists
		with connection.cursor() as cursor:
			sql_check = "SELECT id FROM users WHERE email = %s"
			cursor.execute(sql_check, (email,))
			if cursor.fetchone():
				return jsonify({'error': 'User with this email already exists.'}), 409 # HTTP 409 Conflict

		# 2. Hash the password for secure storage
		# This function is now correctly imported and available
		hashed_password = generate_password_hash(raw_password)
		
		# 3. Generate unique ID and creation date
		user_id = str(uuid.uuid4()) # Use UUID for a guaranteed unique ID
		created_at = datetime.now()
		
		# 4. Insert new user into the 'users' table
		with connection.cursor() as cursor:
			sql_insert = """
				INSERT INTO users (id, name, email, password_hash, created_at) 
				VALUES (%s, %s, %s, %s, %s)
			"""
			cursor.execute(sql_insert, (user_id, name, email, hashed_password, created_at))
			connection.commit()
			
		print(f"User {email} successfully created with ID {user_id}")
		return jsonify({
			'message': 'Account created successfully. Please log in.',
			'user_id': user_id
		}), 201 # HTTP 201 Created

	except Exception as e:
		print(f"FATAL ERROR: /sign_up failed: {e}")
		connection.rollback()
		traceback.print_exc()
		return jsonify({'error': 'Internal Server Error during sign up.', 'details': str(e)}), 500
	finally:
		if connection:
			connection.close()

#login

@app.route('/login', methods=['POST'])
@cross_origin()
def login():
	"""
	Authenticates a user by checking their email and password against the database.
	Expects JSON: {"username": "...", "password": "..."}
	The 'username' field is treated as the email for login.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		data = request.get_json(silent=True)
		
		if not all(k in data for k in ('username', 'password')):
			return jsonify({'error': 'Missing required fields: username and password.'}), 400

		email = data['username'] # Use username input as email
		raw_password = data['password'] 
		
		user_data = None
		
		# 1. Retrieve user data based on email
		with connection.cursor() as cursor:
			sql_select = "SELECT id, name, email, password_hash FROM users WHERE email = %s"
			cursor.execute(sql_select, (email,))
			user_data = cursor.fetchone()

		# 2. Check if user exists and verify password
		if user_data:
			hashed_password = user_data['password_hash']
			
			# --- DEBUG LOGGING ADDED ---
			print("===========================================")
			print(f"ATTEMPTING LOGIN FOR: {email}")
			print(f"Raw Password Submitted: {raw_password}")
			# Note: We only print the start of the hash for security
			print(f"DB Hash Retrieved: {hashed_password[:20]}...") 
			
			# Use check_password_hash to verify the raw password against the hash
			password_matches = check_password_hash(hashed_password, raw_password)
			
			print(f"check_password_hash result: {password_matches}")
			print("===========================================")
			# --- END DEBUG LOGGING ---

			if password_matches:
				print(f"User {email} logged in successfully. PASSWORD MATCH.")
				return jsonify({
					'message': 'Login successful. Redirecting to dashboard...',
					'user_id': user_data['id'],
					'name': user_data['name']
				}), 200
			else:
				# Password does not match
				print(f"Attempted login for {email} failed: Incorrect password. PASSWORD MISMATCH.")
				return jsonify({'error': 'Invalid username or password.'}), 401 # HTTP 401 Unauthorized
		else:
			# User not found
			print(f"Attempted login for {email} failed: User not found.")
			return jsonify({'error': 'Invalid username or password.'}), 401 # HTTP 401 Unauthorized

	except pymysql.Error as db_error:
		print(f"❌ DATABASE ERROR during /login: Code {db_error.args[0]}, Message: {db_error.args[1]}")
		traceback.print_exc()
		return jsonify({'error': 'Database Error during login. Check server logs for details.'}), 500
	
	except Exception as e:
		print(f"FATAL ERROR: /login failed: {e}")
		traceback.print_exc()
		return jsonify({'error': 'Internal Server Error during login.', 'details': str(e)}), 500
	finally:
		if connection:
			connection.close()
# --- Complaint Data Retrieval and Update Routes ---


@app.route('/get_all_complaints', methods=['GET'])
@cross_origin()
def get_all_complaints():
	"""
	Fetches all complaints from the database, manually serializing using CustomJSONEncoder.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		with connection.cursor() as cursor: 
			sql = "SELECT * FROM complaints ORDER BY incident_date DESC"
			cursor.execute(sql)
			result = cursor.fetchall()
			
			# Manually dump the result using our custom encoder
			json_output = json.dumps(result, cls=CustomJSONEncoder)
			
			# Return the raw JSON string wrapped in a Flask Response object
			return Response(json_output, mimetype='application/json')

	except Exception as e:
		print(f"FATAL ERROR: /get_all_complaints failed at JSON conversion stage: {e}")
		traceback.print_exc()
		return jsonify({'error': 'An internal error occurred during data processing.'}), 500
	finally:
		if connection:
			connection.close()

@app.route('/get_accepted_complaints', methods=['GET'])
@cross_origin()
def get_accepted_complaints():
	"""
	Fetches all complaints with status 'Accepted'.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500
	
	try:
		with connection.cursor() as cursor:
			sql = "SELECT * FROM complaints WHERE status = 'Accepted' ORDER BY incident_date DESC"
			cursor.execute(sql)
			result = cursor.fetchall()
			# Use manual serialization here as well for consistency
			json_output = json.dumps(result, cls=CustomJSONEncoder)
			return Response(json_output, mimetype='application/json')

	except Exception as e:
		print(f"ERROR: /get_accepted_complaints query failed: {e}")
		traceback.print_exc()
		return jsonify({"error": "An internal error occurred while fetching accepted complaints."}), 500
	finally:
		if connection:
			connection.close()

@app.route('/get_pending_complaints', methods=['GET'])
@cross_origin()
def get_pending_complaints():
	"""
	Fetches all complaints with status 'Pending'.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500
	
	try:
		with connection.cursor() as cursor:
			sql = "SELECT * FROM complaints WHERE status = 'Pending' ORDER BY incident_date DESC"
			cursor.execute(sql)
			result = cursor.fetchall()
			# Use manual serialization here as well for consistency
			json_output = json.dumps(result, cls=CustomJSONEncoder)
			return Response(json_output, mimetype='application/json')

	except Exception as e:
		print(f"ERROR: /get_pending_complaints query failed: {e}")
		traceback.print_exc()
		return jsonify({"error": "An internal error occurred while fetching pending complaints."}), 500
	finally:
		if connection:
			connection.close()


@app.route('/update_complaint_status', methods=['POST'])
@cross_origin() 
def update_complaint_status():
	"""
	UPDATED: Updates the status of a specific complaint and stores the rejection reason if provided.
	Expects JSON data: {"id": "1002", "status": "Rejected", "rejection_reason": "Not enough evidence."}
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500

	try:
		data = request.json
		complaint_id = data.get('id')
		new_status = data.get('status')
		rejection_reason = data.get('rejection_reason', None) # New: Grab rejection reason
		
		# 1. Validation
		if not complaint_id or new_status not in ["Accepted", "Rejected"]:
			return jsonify({"error": "Invalid ID or Status provided (must be 'Accepted' or 'Rejected')"}), 400
		
		# 2. Database Update
		with connection.cursor() as cursor:
			if new_status == 'Rejected':
				# Use reason from payload, or empty string if not passed (though frontend should send it)
				reason_to_store = rejection_reason if rejection_reason is not None else '' 
				sql = "UPDATE complaints SET status = %s, rejection_reason = %s WHERE id = %s"
				rows_affected = cursor.execute(sql, (new_status, reason_to_store, complaint_id))
			else: # Status is 'Accepted'
				# Clear the rejection_reason if it was previously set
				sql = "UPDATE complaints SET status = %s, rejection_reason = NULL WHERE id = %s"
				rows_affected = cursor.execute(sql, (new_status, complaint_id))
			
			connection.commit()
			
			# 3. Response based on update result
			if rows_affected > 0:
				print(f"Complaint {complaint_id} status updated to {new_status} in DB.")
				return jsonify({"message": f"Complaint {complaint_id} status updated to {new_status}"}), 200
			else:
				return jsonify({"error": f"Complaint with ID {complaint_id} not found"}), 404

	except Exception as e:
		print(f"FATAL ERROR: /update_complaint_status failed: {e}")
		connection.rollback() # Rollback in case of error
		traceback.print_exc()
		return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
	finally:
		if connection:
			connection.close()
			

# get complaints count (commented out in original)

# predict route (commented out in original)

# submit_fir route (commented out in original)


@app.route('/get_rejected_complaints', methods=['GET'])
@cross_origin()
def get_rejected_complaints():
	"""
	NEW ENDPOINT: Retrieves all complaints with status 'Rejected'.
	"""
	connection = get_db_connection()
	if not connection:
		return jsonify({'error': 'Database connection failed.'}), 500
	
	try:
		with connection.cursor() as cursor:
			sql = "SELECT * FROM complaints WHERE status = 'Rejected' ORDER BY incident_date DESC"
			cursor.execute(sql)
			result = cursor.fetchall()
			
			# Manually dump the result using our custom encoder
			json_output = json.dumps(result, cls=CustomJSONEncoder)
			return Response(json_output, mimetype='application/json')
			
	except Exception as e:
		# IMPORTANT: Print full traceback immediately on error
		traceback.print_exc()
		print(f"Error retrieving rejected complaints: {e}")
		return jsonify({"error": "An internal server error occurred while retrieving rejected complaints. Check server logs for traceback."}), 500
	finally:
		if connection:
			connection.close()



# This data simulates a database table of complaint records.

# app = Flask(__name__)
# # Enable CORS for all routes, allowing your frontend to access this API.
# CORS(app)


# --- STATUS TRACKING API (Updated for numerical ID) ---
TABLE_NAME = "complaints" # <-- Verify this table name is EXACTLY correct

# --- Data Cleaning Function (The Ultimate Fix, now including timedelta) ---
def clean_json_data(data):
    """
    Recursively checks and converts non-JSON serializable objects 
    (like datetime, timedelta, Decimal, UUID, bytes) to strings.
    """
    if isinstance(data, dict):
        # Recursively clean dictionary contents
        return {k: clean_json_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Recursively clean list contents
        return [clean_json_data(item) for item in data]
    # Handle known non-serializable database types, INCLUDING timedelta
    elif isinstance(data, (datetime.date, datetime.datetime, datetime.timedelta, uuid.UUID, decimal.Decimal)):
        # Convert date/time, UUIDs, Decimals, and TIMEDELTAs to a standard string
        return str(data)
    elif isinstance(data, bytes):
        # Decode bytes objects to strings, assuming UTF-8
        return data.decode('utf-8')
    # Standard serializable types and None
    elif data is None or isinstance(data, (str, int, float, bool)):
        return data
    else:
        # FALLBACK: Convert any remaining custom/unknown object to its string representation.
        print(f"WARNING: Converted unknown type {type(data)} to string for JSON serialization.")
        return str(data)



@app.route('/get_complaint_status/<fir_id>', methods=['GET'])
def get_complaint_status(fir_id):
    conn = None
    cursor = None
    
    try:
        # 1. Establish connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # 2. Execute query
        # IMPORTANT: Always use parameterized queries (%s) to prevent SQL injection.
        query = f"SELECT * FROM {TABLE_NAME} WHERE fir_id = %s"
        print(f"Executing query: {query} with ID: {fir_id}")
        cursor.execute(query, (fir_id,))
        result = cursor.fetchone()

        if result:
            # 3. Clean the result before jsonify
            cleaned_result = clean_json_data(result)
            return jsonify(cleaned_result)
        else:
            print(f"Error: FIR ID {fir_id} not found in table '{TABLE_NAME}'.")
            # Return a 404 response
            abort(404, description=f"FIR ID {fir_id} not found")
            
    # Catch specific PyMySQL errors (e.g., table/column errors)
    except pymysql.Error as err:
        print(f"\n--- CRITICAL PyMySQL Query/Connection Error ---")
        print(f"Database Error Details: {err}")
        abort(500, description="Database operation failed due to configuration or query error.")
    
    # Catch any other unexpected Python errors
    except Exception as e:
        print(f"\n--- CRITICAL UNCAUGHT PYTHON ERROR ---")
        print(f"Error Type: {type(e).__name__}, Message: {e}")
        traceback.print_exc() # Print the full traceback
        print("--------------------------------------\n")
        # Ensure Flask returns a 500 error consistently
        abort(500, description="Internal processing error. Check the server console for the full traceback.")
        
    finally:
        # 5. Ensure resources are cleaned up
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()


#register :

@app.route('/register', methods=['POST'])
def register_officer():
    conn = None
    cursor = None
    
    try:
        # 1. Get and validate JSON data
        data = request.get_json()
        name = data.get('name')
        username = data.get('username')
        password = data.get('password') # The raw, unhashed password

        if not name or not username or not password:
            return jsonify({"error": "Missing required fields (name, username, or password)"}), 400

        # 2. Connect to DB
        conn = get_db_connection()
        cursor = conn.cursor()

        # 3. Check if username already exists (Username is a UNI key)
        check_query = f"SELECT id FROM police_officers WHERE username = %s"
        cursor.execute(check_query, (username,))
        if cursor.fetchone():
            return jsonify({"error": f"Username '{username}' already exists. Please choose a different Police ID."}), 400

        # 4. Insert new officer record
        # 🚨 SECURITY RISK: Storing the password in plain text (as requested).
        insert_query = f"""
            INSERT INTO police_officers (name, username, password_hash) 
            VALUES (%s, %s, %s)
        """
        # We save the plain password into the 'password_hash' column
        cursor.execute(insert_query, (name, username, password))
        conn.commit()
        
        # 5. Success response
        return jsonify({
            "message": "Officer registered successfully",
            "username": username
        }), 201

    # Catch specific database errors 
    except pymysql.Error as err:
        print(f"\n--- Database Error during Registration ---")
        print(f"Details: {err}")
        conn.rollback() # Ensure no partial commit
        return jsonify({"error": "Database error during registration. Could not save record."}), 500
    
    # Catch any other unexpected Python errors
    except Exception as e:
        print(f"\n--- CRITICAL UNCAUGHT PYTHON ERROR ---")
        print(f"Error Type: {type(e).__name__}, Message: {e}")
        traceback.print_exc() 
        return jsonify({"error": "Internal server error. Check server logs."}), 500
        
    finally:
        # 6. Cleanup resources
        if cursor:
            cursor.close()
        if conn and conn.open:
            conn.close()

# --- NEW API Endpoint: Officer Login (/login) ---
TABLE_NAME = "police_officers" 


@app.route('/police_login', methods=['POST'])
def login_officer():
    conn = None
    cursor = None
    
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password') # The raw, unhashed password

        if not username or not password:
            return jsonify({"error": "Missing Police ID or Password."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch the officer record by username
        query = f"SELECT id, name, password_hash FROM {TABLE_NAME} WHERE username = %s"
        cursor.execute(query, (username,))
        officer = cursor.fetchone()
        
        if officer:
            # 2. 🚨 SECURITY RISK: Compare plain-text password against stored plain password_hash.
            stored_password = officer.get('password_hash')
            if stored_password == password:
                # 3. Success! Return necessary user info.
                return jsonify({
                    "message": "Login successful.",
                    "user_id": officer['id'],
                    "name": officer['name']
                }), 200
            else:
                # Password mismatch
                return jsonify({"error": "Invalid Police ID or Password."}), 401
        else:
            # Username not found
            return jsonify({"error": "Invalid Police ID or Password."}), 401

    except pymysql.Error as err:
        print(f"Database Error during Login: {err}")
        return jsonify({"error": "Database error during login."}), 500
    
    except Exception as e:
        print(f"CRITICAL UNCAUGHT PYTHON ERROR: {e}")
        traceback.print_exc() 
        return jsonify({"error": "Internal server error."}), 500
        
    finally:
        if cursor: cursor.close()
        if conn and conn.open: conn.close()


# --- FIX 4: Added the mandatory Flask run block ---
if __name__ == '__main__':
	# Check the database connection status before starting the app
	if check_db_connection():
		# Run the Flask app on http://127.0.0.1:8000
		app.run(host='0.0.0.0', port=8000, debug=True)