from google.cloud import aiplatform
from google.cloud import storage
import os

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
        display_name="xgboost-iris-training",
        script_path="trainer/task.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/xgboost-cpu.1-6:latest",
        requirements=requirements,
        staging_bucket=f"gs://{BUCKET_NAME}/staging",
    )

    # # print contents of the bucket
    # print(f"Contents of {BUCKET_NAME}")
    # client = storage.Client()
    # blobs = client.list_blobs(BUCKET_NAME)
    # for blob in blobs:
    #     print(blob.name)

    VERTEX_SA = os.getenv('VERTEX_SA')
    job.run(
        service_account=f"{VERTEX_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
    )

if __name__ == '__main__':
    run_training()