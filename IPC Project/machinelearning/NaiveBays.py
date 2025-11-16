import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score, classification_report

# 1. Load the dataset from the provided CSV file.
# Note: You must have the 'mock_data.csv' file in the same directory.
try:
    df = pd.read_csv('mock_data.csv')
    print("Dataset loaded successfully.\n")
    print(df.head())
except FileNotFoundError:
    print("Error: 'mock_data.csv' not found. Please ensure the file is in the correct directory.")
    exit()

# 2. Prepare the data for training.
# 'crime_description' is our feature (X) and 'ipc_section' is our label (y).
X = df['crime_description']
y = df['ipc_section']

# 3. Split the data into training and testing sets.
# We'll use 80% of the data for training and 20% for testing.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Create a machine learning pipeline.
# A pipeline automates the steps of text vectorization and model training.
# TfidfVectorizer: Converts the text descriptions into a matrix of TF-IDF features,
# which are numerical representations of words' importance in the text.
# MultinomialNB: This is the Naive Bayes classifier, which is highly suitable for text classification tasks.
model = make_pipeline(TfidfVectorizer(), MultinomialNB())

# 5. Train the model using the training data.
print("\nTraining the Naive Bayes model...")
model.fit(X_train, y_train)
print("Model training complete.\n")

# 6. Evaluate the model's performance on the test data.
# This gives us an idea of how well the model generalizes to unseen data.
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy on Test Data: {accuracy:.2f}")

# Optional: Print a detailed classification report.
# This report shows precision, recall, and F1-score for each IPC section.
print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# 7. Use the trained model to predict the IPC section for a new description.
print("\n--- Making a Prediction on a New Complaint ---")
new_complaint = ["A fraudster stole my money using a fake online job offer."]
predicted_section = model.predict(new_complaint)

print(f"\nNew Complaint: '{new_complaint[0]}'")
print(f"Predicted IPC Section: {predicted_section[0]}")

# Another example
new_complaint_2 = ["My car was stolen from the parking lot last night."]
predicted_section_2 = model.predict(new_complaint_2)

print(f"\nNew Complaint: '{new_complaint_2[0]}'")
print(f"Predicted IPC Section: {predicted_section_2[0]}")
