# Ci/CD with GitHub Actions and Vertex AI

This repository explores Continuous Integration and Continuous Deployment (CI/CD) using GitHub Actions in conjunction with a cloud provider, specifically Google Cloud Platform (GCP). It demonstrates how to automate the training of a custom model using Vertex AI.

The workflow is triggered by any push to the main branch that modifies the `trainer/task.py` file. The workflow sets up the environment and calls the `train.py` script to start a custom training job in GCP.

The only assumption to follow along is that you have a GCP project and a GitHub repository.

## Structure

```plaintext
.github/                # GitHub Actions workflows
    workflows/
        main.yml
trainer/                # Training package
    task.py             # Training script
    requirements.txt    # Python dependencies
environment.yml         # Conda environment file
README.md
train.py                # Script to start the custom training job
```
## Instructions

### Basic Setup (optional)

This step is optional as you may perform this steps from cloud shell. However, setting it up locally is useful as it also allows you to test the training script locally.

1. Create conda environment

    ```sh
    conda env create -f environment.yml
    ```

2. Activate conda environment

    ```sh
    conda activate github_actions_gcp
    ```

3. Authenticate with gcloud
    ```sh	
    gcloud auth login
    ```

4. Set the project
    ```sh
    gcloud config set project ${PROJECT_ID}
    ```

5. Create the bucket
    ```sh
    gcloud storage create ${BUCKET_NAME} --location=${LOCATION}
    ```

6. Set up uniform bucket-level access for the bucket
    ```sh
    gcloud storage buckets update gs://${BUCKET_NAME} --uniform-bucket-level-access
    ```
    > Note: This is necessary to grant access to the Workload Identity Pool over that single bucket.

7. Activate necessary services
    ```sh
    gcloud services enable \
        aiplatform.googleapis.com \
        iam.googleapis.com \
        storage-api.googleapis.com
    ```

8. Create a service account for the custom training job
    ```sh
    gcloud iam service-accounts create ${VERTEX_SA} \
        --display-name "Vertex AI Service Account"
    ```

9. Grant the service account the necessary permissions
    ```sh
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="serviceAccount:${VERTEX_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/aiplatform.serviceAgent"
    ``` 

### Set up Workload Identity for GitHub Actions

The google auth github action provides us with multiple ways to authenticate with GCP. In this case, we will use Workload Identity. This method allows us to authenticate with GCP using the GitHub Actions token. This is useful as it allows us to avoid storing any keys in the GitHub repository secrets. You may check the other alternatives at the [google auth github action documentation](https://github.com/google-github-actions/auth).

1. Add the following values as secrets in your GitHub repository:
    - `PROJECT_ID`: The GCP project ID.
    - `BUCKET_NAME`: The name of the bucket to store the training package and for staging.
    - `LOCATION`: The location of the training job and the bucket.
    - `VERTEX_SA`: The service account name that will be used to run the custom training job.

1.  Create a Workload Identity Pool:

    ```sh
    # TODO: replace ${PROJECT_ID} with your value below.

    gcloud iam workload-identity-pools create "github" \
      --project="${PROJECT_ID}" \
      --location="global" \
      --display-name="GitHub Actions Pool"
    ```

1.  Get the full ID of the Workload Identity **Pool** and set it to a local variable

    ```sh
    # TODO: replace ${PROJECT_ID} with your value below.

    WORKLOAD_IDENTITY_POOL_ID=$(gcloud iam workload-identity-pools describe "github" \
        --project="${PROJECT_ID}" \
        --location="global" \
        --format="value(name)")
    ```

    This value should be of the format:

    ```text
    projects/123456789/locations/global/workloadIdentityPools/github
    ```

1.  Create a Workload Identity **Provider** in that pool:

    For security reasons, you should limit the Workload Identity Provider. A general recomendation is to restrict based on the organization. The following example shows how to restrict the provider to a specific GitHub user and repository:

    ```sh
    # TODO: replace ${PROJECT_ID}, ${GITHUB_USER}, and ${REPO} with your values below.

    # ${REPO} is the full repo name including the github user or organization,
    # such as "user/my-repo" or "org/my-repo".

    gcloud iam workload-identity-pools providers create-oidc "github-repo-provider" \
    --project="${PROJECT_ID}" \
    --location="global" \
    --workload-identity-pool="github" \
    --display-name="My GitHub repo Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.actor == '${GITHUB_USER}' && assertion.repository == '${REPO}'" \
    --issuer-uri="https://token.actions.githubusercontent.com"
    ```

1.  Extract the Workload Identity **Provider** resource name:

    ```sh
    # TODO: replace ${PROJECT_ID} with your value below.

    gcloud iam workload-identity-pools providers describe "github-repo-provider" \
      --project="${PROJECT_ID}" \
      --location="global" \
      --workload-identity-pool="github" \
      --format="value(name)"
    ```

    Add this `workload_identity_provider` value as a secret in your GitHub
    repository.

1.  As needed, allow authentications from the Workload Identity Pool to Google
    Cloud resources. These can be any Google Cloud resources that support
    federated ID tokens, and it can be done after the GitHub Action is
    configured.

    Here we need to grant permissions to create the custom training job as well as using the service account used inside the custom training job. Specifically, we need to grant the following permissions:
    - `roles/iam.serviceAccountUser` on the service account used to run the custom training job.
    - `roles/storage.objectAdmin` on the bucket which will be used to store the python packages.
        <details>
        This is necesary because when usin the aiplatform API to create a custom job, internally it packages the training code and stores it in a bucket.  
        </details>

    - `roles/aiplatform.user` over the project, to create the training pipelines.

    ```sh
    # TODO: replace ${PROJECT_ID}, ${WORKLOAD_IDENTITY_POOL_ID}, ${REPO}, ${PROJECT_NUMBER} and ${VERTEX_SA}
    # with your values below.
    #
    # ${REPO} is the full repo name including the parent GitHub user or organization,
    # such as "user/my-repo" or "org/my-repo".
    #
    # ${WORKLOAD_IDENTITY_POOL_ID} is the full pool id, such as
    # "projects/123456789/locations/global/workloadIdentityPools/github".
    # 
    # ${VERTEX_SA} is the service account name that will be used to run the custom training job.

    gcloud iam service-accounts add-iam-policy-binding \
        --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}" \
        --role="roles/iam.serviceAccountUser" \
        ${VERTEX_SA}@${PROJECT_ID}.iam.gserviceaccount.com

    gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
        --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}" \
        --role="roles/storage.objectAdmin"
    
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}" \
        --role="roles/aiplatform.user"
    
    ```
    > Note: The propagation of the permissions may take a few minutes.
