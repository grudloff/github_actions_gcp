
This repository contains a GitHub Actions workflow that trains a custom model using Vertex AI. The workflow is triggered by a push to the main branch.

The only assumption is that you have a GCP valid project.

## Set up environment

1. Create conda environment

```sh
conda env create -f environment.yml
```

2. Activate conda environment

```sh
conda activate github_actions_gcp
```

## Setup GCP

1. Authenticate with gcloud
```sh	
gcloud auth login
```

2. Set the project
```sh
gcloud config set project ${PROJECT_ID}
```

3. Create the bucket
```sh
gcloud storage create ${BUCKET_NAME} --location=${LOCATION}
```

4. Activate necessary services
```sh
gcloud services enable \
    aiplatform.googleapis.com \
    iam.googleapis.com \
    storage-api.googleapis.com
```

5. Create a service account for the custom training job
```sh
gcloud iam service-accounts create ${VERTEX_SA} \
    --display-name "Vertex AI Service Account"
```

6. Grant the service account the necessary permissions
```sh
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${VERTEX_SA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.serviceAgent"
```

## Set up Workload Identity for GitHub Actions

1. Add the PROJECT_ID as a secret in your GitHub repository.

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

    For security reasons, you should limit the Workload Identity Provider. A general recomendation is to restrict based on the organization. The following example shows how to restrict the provider to a specific GitHub user:

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

    Here we need to grant permissions to create the custom training job as well as using the service agent used by default in the custom training job. (You can check out the Vertex AI Service Agents [here](https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents))

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
    # ${VERTEX_SA} is the service account used to run the custom training job.

    gcloud iam service-accounts add-iam-policy-binding \
        --member="principalSet://iam.googleapis.com/${WORKLOAD_IDENTITY_POOL_ID}/attribute.repository/${REPO}" \
        --role="roles/iam.serviceAccountUser" \
        ${VERTEX_SA}@${PROJECT_ID}.iam.gserviceaccount.com
    ```
