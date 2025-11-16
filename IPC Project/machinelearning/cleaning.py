import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Load the dataset from the provided CSV file.
try:
    df = pd.read_csv('mock_data.csv')
    print("Dataset loaded successfully.\n")
except FileNotFoundError:
    print("Error: 'mock_data.csv' not found. Please ensure the file is in the correct directory.")
    exit()

# 2. Prepare the data for preprocessing.
X = df['crime_description']
y = df['ipc_section']

# Split the data into training and testing sets to demonstrate the process on different data.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Create an instance of the TfidfVectorizer.
# This object will be responsible for both cleaning the text and converting it to numbers.
# We set `stop_words='english'` to automatically remove common English words.
vectorizer = TfidfVectorizer(stop_words='english')

# 4. Fit the vectorizer to the training data.
# The `fit()` method analyzes the text to learn the vocabulary and calculate IDF scores.
print("Fitting the TfidfVectorizer to the training data...")
vectorizer.fit(X_train)
print("Vocabulary learned successfully.")

# 5. Transform the training data.
# The `transform()` method converts the text into a numerical matrix.
X_train_vectorized = vectorizer.transform(X_train)

# 6. Transform the test data using the *same* vectorizer.
# It is critical to use the same vectorizer for both training and testing data.
X_test_vectorized = vectorizer.transform(X_test)

# 7. Print the results to see the output.
print("\n--- After Preprocessing and Vectorization ---")
print("Shape of the vectorized training data (samples, features):", X_train_vectorized.shape)
print("Shape of the vectorized test data (samples, features):", X_test_vectorized.shape)
print("\nFirst 10 features (words) from the learned vocabulary:")
print(vectorizer.get_feature_names_out()[:10])

# To see the numerical data, you can convert the sparse matrix to a dense array.
# Note: This is for demonstration only. Do not do this on large datasets as it consumes a lot of memory.
# print("\nVectorized data for the first training example:\n", X_train_vectorized.toarray()[0])
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

# 1. Load the dataset from the provided CSV file.
try:
    df = pd.read_csv('mock_data.csv')
    print("Dataset loaded successfully.\n")
except FileNotFoundError:
    print("Error: 'mock_data.csv' not found. Please ensure the file is in the correct directory.")
    exit()

# 2. Print the raw data to check its initial state.
print("--- Raw Data Sample (Before Preprocessing) ---")
print(df.head())
print(f"\nShape of the raw data: {df.shape}\n")

# 3. Prepare the data for preprocessing.
X = df['crime_description']
y = df['ipc_section']

# Split the data into training and testing sets.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Create an instance of the TfidfVectorizer.
vectorizer = TfidfVectorizer(stop_words='english')

# 5. Fit the vectorizer to the training data and transform it.
print("Fitting the TfidfVectorizer to the training data...")
X_train_vectorized = vectorizer.fit_transform(X_train)
print("Vocabulary learned successfully.")

# 6. Transform the test data using the *same* vectorizer.
X_test_vectorized = vectorizer.transform(X_test)

# 7. Print the results to see the output.
print("\n--- After Preprocessing and Vectorization ---")
print("Shape of the vectorized training data (samples, features):", X_train_vectorized.shape)
print("Shape of the vectorized test data (samples, features):", X_test_vectorized.shape)
print("\nFirst 10 features (words) from the learned vocabulary:")
print(vectorizer.get_feature_names_out()[:10])

# To see the numerical data, you can convert the sparse matrix to a dense array.
# Note: This is for demonstration only. Do not do this on large datasets as it consumes a lot of memory.
# print("\nVectorized data for the first training example:\n", X_train_vectorized.toarray()[0])
