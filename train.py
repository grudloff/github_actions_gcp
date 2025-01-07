from google.cloud import aiplatform
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME')
TRAINING_NAME = os.getenv('TRAINING_NAME')

def run_training():

    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    # job from module in gcs bucket (not local script)
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    with open("trainer/requirements.txt", "r") as f:
        requirements = f.read().splitlines()
        requirements = list(set(requirements))

    job = aiplatform.CustomTrainingJob(
        display_name=TRAINING_NAME,
        script_path="trainer/task.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/scikit-learn-cpu.0-24:latest",
        model_serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest",
        requirements=requirements,
        staging_bucket=f"gs://{BUCKET_NAME}/staging",
    )

    VERTEX_SA = os.getenv('VERTEX_SA')
    model = job.run(
        model_display_name=MODEL_NAME,
        service_account=f"{VERTEX_SA}@{PROJECT_ID}.iam.gserviceaccount.com"
    )

    print(model.display_name)
    print(model.resource_name)
    print(model.uri)

if __name__ == '__main__':
    run_training()