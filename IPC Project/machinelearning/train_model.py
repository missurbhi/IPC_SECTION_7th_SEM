import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib


# 1. Load the dataset from the provided CSV file.
try:
    df = pd.read_csv('mock_data.csv')
    print("Dataset loaded successfully.\n")
except FileNotFoundError:
    print("Error: 'mock_data.csv' not found. Please ensure the file is in the correct directory.")
    exit()

# 2. Prepare the data for training.
X = df['crime_description']
y = df['ipc_section']

# Split the data into training and testing sets.
# 80% of the data will be used to train the model, and 20% to test its performance.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Create a machine learning pipeline.
# This pipeline first vectorizes the text and then trains the Naive Bayes model.
# The TfidfVectorizer handles all the preprocessing and numerical conversion.
model = make_pipeline(TfidfVectorizer(stop_words='english'), MultinomialNB())

# 4. Train the model.
# This single command trains the entire pipeline on your data.
print("Training the Naive Bayes model...")
model.fit(X_train, y_train)
print("Model training complete.\n")

# 5. Make predictions on the test data.
# The model predicts the IPC sections for the descriptions it has never seen before.
y_pred = model.predict(X_test)

# 6. Evaluate the model's performance.
# We compare the predicted IPC sections with the actual ones to calculate accuracy.
print("--- Model Performance ---")
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy * 100:.2f}%")

# The classification report provides more detailed metrics like precision, recall, and F1-score for each class.
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# 7. Save the trained model to a file.
model_filename = 'trained_model.joblib'
joblib.dump(model, model_filename)
print(f"\nModel saved successfully as '{model_filename}'.")
# Use the saved model to make a new prediction.
# This demonstrates how your backend would load and use the model
print("--- Using the Trained Model for a New Complaint ---")
new_complaint = ["A fraudster stole money from my bank account using my credit card."]
predicted_ipc = model.predict(new_complaint)
print(f"\nNew complaint: '{new_complaint[0]}'")
print(f"Predicted IPC Section(s): {predicted_ipc[0]}")
