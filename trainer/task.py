from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, roc_curve
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from google.cloud import aiplatform
import joblib
import os
import argparse
from datetime import datetime

EXPERIMENT_NAME = "iris-experiment"

def get_preprocessor():
    preprocessor = StandardScaler()
    return preprocessor

def get_model(**kwargs):
    model = RandomForestClassifier(**kwargs)
    return model

def get_pipe():
    preprocessor = get_preprocessor()
    model = get_model()
    pipe = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    return pipe

def train():
    parser = argparse.ArgumentParser(description='Train a model on the Iris dataset.')
    parser.add_argument('--local', type=bool, required=False,
                        help='Should be set to true if running locally.',
                        default=False)
    local = parser.parse_args().local

    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')

    aiplatform.init(
        experiment=EXPERIMENT_NAME,
        project=PROJECT_ID,
        location=LOCATION
    )

    # Set up experiment tracking
    aiplatform.autolog()
    aiplatform.start_run(run=f"sklearn-iris-run-{datetime.now().strftime('%Y%m%d%H%M%S')}")


    # Load the iris dataset
    iris = load_iris()
    X, y = iris.data, iris.target

    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the pipeline
    clf = get_pipe()

    # Train the model
    clf.fit(X_train, y_train)

    # Make predictions
    y_pred = clf.predict(X_test)

    # Save the model
    if local:
        MODEL_DIR = "local_model_dir"
    else:
        MODEL_DIR = os.getenv('AIP_MODEL_DIR')
        MODEL_DIR = MODEL_DIR.replace('gs://', '/gcs/')

    filepath = os.path.join(MODEL_DIR, 'model.joblib')
    folder_path = os.path.dirname(filepath)
    os.makedirs(folder_path, exist_ok=True)
    joblib.dump(clf, filepath)

    # Calculate the accuracy
    accuracy = accuracy_score(y_test, y_pred)
    aiplatform.log_metrics({'accuracy': accuracy})
    print(f'Accuracy: {accuracy:.2f}')

    labels = list(iris.target_names)
    matrix = confusion_matrix(y_test, y_pred)
    matrix = matrix.tolist()

    aiplatform.log_classification_metrics(
        labels=labels,
        matrix=matrix
    )

    # Stop experiment run
    aiplatform.end_run()

if __name__ == '__main__':
    train()