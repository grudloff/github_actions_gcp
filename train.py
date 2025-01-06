from google.cloud import aiplatform
import os

def run_training():

    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    # job from module in gcs bucket (not local script)
    bucket_name = os.getenv('BUCKET_NAME')

    with open("requirements.txt", "r") as f:
        requirements = f.read().splitlines()
        requirements = list(set(requirements))

    job = aiplatform.CustomTrainingJob(
        display_name="xgboost-iris-training",
        script_path="trainer/task.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/xgboost-cpu.1-6:latest",
        requirements=requirements,
        staging_bucket=f"gs://{bucket_name}/staging",
    )

    VERTEX_SA = os.getenv('VERTEX_SA')
    job.run(
        service_account=f"{VERTEX_SA}@{PROJECT_ID}.iam.gserviceaccount.com",
    )

if __name__ == '__main__':
    run_training()