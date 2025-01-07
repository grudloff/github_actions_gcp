from google.cloud import aiplatform
import os
from dotenv import load_dotenv
load_dotenv()

MODEL_NAME = os.getenv('MODEL_NAME')
ENDPOINT_NAME = os.getenv('ENDPOINT_NAME')

def deploy_model():
    PROJECT_ID = os.getenv('PROJECT_ID')
    LOCATION = os.getenv('LOCATION')
    VERTEX_SA = os.getenv('VERTEX_SA')

    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    model = aiplatform.Model(model_name=f"{MODEL_NAME}@latest")

    endpoint = aiplatform.Endpoint.create(display_name=ENDPOINT_NAME)

    model.deploy(
        endpoint=endpoint,
        machine_type='n1-standard-4',
        min_replica_count=1,
        max_replica_count=1,
        service_account=VERTEX_SA
    )

if __name__ == '__main__':
    deploy_model()