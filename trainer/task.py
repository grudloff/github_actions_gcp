from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

def train():
    # Load the iris dataset
    iris = load_iris()
    X, y = iris.data, iris.target

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)

    # Train the model
    clf.fit(X_train, y_train)

    # Make predictions
    y_pred = clf.predict(X_test)

    # Save the model
    filepath = f"/gcs/{os.environ["BUCKET_NAME"]}/model_artifacts/model.bst"
    joblib.dump(clf, filepath)

    # Calculate the accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {accuracy:.2f}')

if __name__ == '__main__':
    train()