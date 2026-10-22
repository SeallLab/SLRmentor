# SLRmentor Backend

[![Latest Docker Image Version](https://img.shields.io/docker/v/seallabuofc/slrmentor-backend?sort=semver&label=Latest%20Docker%20Version)](https://hub.docker.com/r/seallabuofc/slrmentor-backend/tags)

[Docker Hub repository](https://hub.docker.com/r/seallabuofc/slrmentor-backend)

SLRmentor is a SEALL application that supports systematic literature reviews with AI-assisted academic search string generation and conversion, inclusion/exclusion criteria refinement, and research guidance.

The backend uses **Flask**, **MongoDB Atlas**, **Google Gemini**, and **OpenAI**. Retrieval-Augmented Generation (RAG) uses MongoDB Atlas Vector Search with Automated Embedding, so the backend does not need to host an embedding model locally.

---

## 1. Requirements

### Local development

- [Python](https://www.python.org/downloads/) **3.14.5 or later**, as declared in `pyproject.toml`.
- [uv](https://docs.astral.sh/uv/) for Python environment and dependency management.
- Access to a MongoDB Atlas cluster with the required collections and Vector Search index.
- API credentials for the LLM providers you plan to use.

For Docker-based execution, install [Docker](https://docs.docker.com/get-docker/). You do not need Conda or a local MongoDB Community Server for the Atlas-based configuration.

## 2. Project Structure

```text
BackendRefactor/
├── .env
├── .dockerignore
├── .gitignore
├── Dockerfile
├── README.md
├── pyproject.toml
├── uv.lock
└── app/
    ├── __init__.py
    ├── app.py
    └── helpers/
        ├── RAG/
        │   └── RetrieverManager.py
        ├── db/
        │   └── mongodbhelpers.py
        ├── llm/
        │   ├── promptBuilder.py
        │   ├── llmPromptingUtils.py
        │   ├── llmReturnFormat.py
        │   └── prompts/
        ├── cryptographic_helpers.py
        └── scholarlyapi.py
```

Commands in this README assume you are in the **project root**, where `pyproject.toml` and `Dockerfile` are located.

## 3. Environment Configuration

Create `.env` in the backend folder:

```env
# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://your-username:your-password@your-cluster.mongodb.net/
MONGO_USERNAME=your-mongodb-username
MONGO_USERNAME_PASSWORD=your-mongodb-password
MONGO_DB_NAME=your-database-name
MONGO_DB_RAG_COLLECTION_NAME=your-rag-collection-name
VECTOR_SEARCH_INDEX=autoembed_index

# LLM API Keys
GPT_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Other Configurations
RAG_doc_limit=5
message_history_limit=30
chat_hash_length=8
hash_byte_length=16
```

Replace the placeholders with your actual configuration. **Do not add surrounding quotation marks or spaces around `=` in this `.env` file.** Docker's `--env-file` can include literal quotation marks in environment variable values, which causes PyMongo to reject a quoted `MONGO_URI` with `Invalid URI scheme`. The unquoted format above works with both Docker's `--env-file` and `python-dotenv` during local Flask development.

The current `app.py` and `RetrieverManager.py` use `MONGO_URI` directly; the separate username/password variables are retained from the project's environment template. If your credentials include reserved URL characters, encode them correctly in `MONGO_URI`.

The backend includes Gemini-to-OpenAI fallback behavior. Configure both API keys for fallback to work; check individual routes if you intend to use only one provider.

| Variable | Purpose |
|---|---|
| `MONGO_URI` | MongoDB Atlas connection string |
| `MONGO_USERNAME` | Optional separate MongoDB username setting retained in the project configuration |
| `MONGO_USERNAME_PASSWORD` | Optional separate MongoDB password setting retained in the project configuration |
| `MONGO_DB_NAME` | Database name |
| `MONGO_DB_RAG_COLLECTION_NAME` | Collection containing RAG documents |
| `VECTOR_SEARCH_INDEX` | Atlas Vector Search index name |
| `GPT_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Gemini API key |
| `RAG_doc_limit` | Maximum RAG documents to retrieve |
| `message_history_limit` | Maximum recent messages used in conversation context |
| `chat_hash_length` | Chat hash length configuration |
| `hash_byte_length` | Hash byte length configuration |

**Security:** Keep `.env` in both `.gitignore` and `.dockerignore`. Do not commit secrets or copy `.env` into the Docker image. Other helper modules may require additional environment variables.

## 4. Local Development with uv

Install uv following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/), then verify:

```bash
uv --version
```

Install dependencies from the lockfile:

```bash
uv sync --locked
```

Run the Flask development server:

```bash
uv run flask --app app.app run --debug
```

Open <http://127.0.0.1:5000/>. The root endpoint returns:

```text
Server is live ;)
```

You do not need to activate `.venv` when using `uv run`. Use the Flask development server only for local development.

## 5. MongoDB Atlas and RAG

The backend performs semantic retrieval using **MongoDB Atlas Vector Search with Automated Embedding**:

1. A Flask route receives a query and passes it to `RetrieverManager`.
2. MongoDB Atlas generates the query embedding remotely.
3. Atlas Vector Search returns the most relevant document chunks.
4. The backend formats the retrieved text and includes it in the LLM prompt.

No local embedding model is loaded by this workflow.

### Vector Search index

The project uses the following index configuration:

```json
{
  "fields": [
    {
      "modality": "text",
      "model": "voyage-4-lite",
      "numDimensions": 256,
      "path": "content",
      "similarity": "cosine",
      "type": "autoEmbed"
    }
  ]
}
```

Create the index on the collection designated by `MONGO_DB_NAME` and `MONGO_DB_RAG_COLLECTION_NAME`. Its name must match `VECTOR_SEARCH_INDEX`. Verify that the selected Automated Embedding configuration is supported by your Atlas deployment.

### Retrieval interface

```python
rm.get_relevant_documents(query)
```

This method returns native Python dictionaries rather than LangChain document objects. Results may include `content`, `paper_id`, `source`, `page`, `chunk_index`, and `score`. The `RAG_doc_limit` setting controls the maximum number of documents retrieved.

Ensure the Atlas cluster is reachable, its user has the necessary permissions, and the index is ready before testing RAG routes.

## 6. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Server health check |
| `/createchat` | POST | Create a chat session |
| `/getchathistory` | POST | Retrieve search string chat history |
| `/getcriteriachathistory` | POST | Retrieve criteria chat history |
| `/getmentorchathistory` | POST | Retrieve mentor chat history |
| `/getsystemcontext` | POST | Retrieve system context |
| `/setsystemcontext` | POST | Update system context |
| `/prompt` | POST | Generate or refine academic search strings |
| `/conversionformats` | GET | List supported search string formats |
| `/convertsearchstring` | POST | Convert a search string into another format |
| `/criteria` | POST | Generate or refine inclusion/exclusion criteria |
| `/mentor` | POST | Provide AI-assisted SLR guidance |
| `/ragquery` | POST | Query retrieved RAG documents without an LLM call |

### Example: test RAG retrieval

Send a `POST` request to `http://127.0.0.1:5000/ragquery` with JSON:

```json
{
  "query": "What is a systematic literature review?"
}
```

The response contains the query, the number of results, and the retrieved document data. This endpoint tests retrieval independently of LLM generation.

## 7. Docker Configuration

The Dockerfile uses Python 3.14.5 slim, uv, and Gunicorn:

```dockerfile
FROM python:3.14.5-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /backend

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project --no-dev

COPY app ./app

ENV PATH="/backend/.venv/bin:$PATH"

EXPOSE 5000

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --timeout 120 app.app:app"]
```

The server listens on port 5000 unless `PORT` is set to a different value. The Dockerfile does **not** include the `.env` file; configure variables when starting the container.

## 8. Build and Run Docker Locally

Build the image:

```bash
docker build -t slrmentor-backend .
```

Run it with the environment file:

```bash
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env slrmentor-backend
```

Although `.env` is excluded by `.dockerignore`, `docker run --env-file .env` still reads it from your local machine at **runtime**. The `.env` file must use unquoted `KEY=value` entries, as shown in Section 3. If you change `.env`, stop and remove the existing container, then create a new container with `--env-file .env`; **rebuilding the image is not required** for environment-only changes.

Verify:

```bash
docker ps
docker logs slrmentor-backend
```

Then open <http://localhost:5000/>.

Stop and remove the container:

```bash
docker stop slrmentor-backend
docker rm slrmentor-backend
```

## 9. Publish a Docker Image to Docker Hub

**Docker Hub repository:** [seallabuofc/slrmentor-backend](https://hub.docker.com/r/seallabuofc/slrmentor-backend)

**Latest published version:**

[![Latest Docker Image Version](https://img.shields.io/docker/v/seallabuofc/slrmentor-backend?sort=semver&label=Latest%20Docker%20Version)](https://hub.docker.com/r/seallabuofc/slrmentor-backend/tags)

The badge queries Docker Hub through Shields.io and updates as its cache refreshes. It shows the highest semantic-version tag recognized by the badge service. It does **not** guarantee that the `latest` tag points to the same version.

Replace **`vX.X`** below with your new release version (for example, `v2.3`).

### 1. Build the versioned image

```bash
docker build -t seallabuofc/slrmentor-backend:vX.X .
```

### 2. Tag the image as latest

```bash
docker tag seallabuofc/slrmentor-backend:vX.X seallabuofc/slrmentor-backend:latest
```

### 3. Test the image locally

```bash
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:vX.X
```

Check logs:

```bash
docker logs slrmentor-backend
```

When finished:

```bash
docker stop slrmentor-backend
docker rm slrmentor-backend
```

If a container named `slrmentor-backend` already exists, stop and remove it before starting the test container.

### 4. Log in to Docker Hub

```bash
docker login
```

### 5. Push the versioned image and latest tag

```bash
docker push seallabuofc/slrmentor-backend:vX.X
docker push seallabuofc/slrmentor-backend:latest
```

Publishing an image does not automatically update running containers on other machines.

## 10. Run from Docker Hub on Another Machine (Including AWS EC2)

Ensure Docker is installed and the target machine has an `.env` file containing its runtime credentials. MongoDB Atlas must allow connections from the deployment environment.

### 1. Stop and remove the existing container

```bash
docker stop slrmentor-backend
docker rm slrmentor-backend
```

Skip these commands on the first deployment.

### 2. Pull the image tagged latest

```bash
docker pull seallabuofc/slrmentor-backend:latest
```

The `latest` tag is maintained by the publisher. For reproducible deployment and rollbacks, prefer an explicit version tag such as `vX.X` (replaced with an actual release number).

### 3. Run without a memory limit

```bash
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:latest
```

### Or run with a 1 GiB memory limit

```bash
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env --memory=1g --memory-swap=1g seallabuofc/slrmentor-backend:latest
```

Choose **one** of the two `docker run` commands, not both. Adjust memory according to observed resource usage.

### 4. Verify the deployment

```bash
docker ps
docker logs -f slrmentor-backend
```

To see which image reference was used to create the running container:

```bash
docker inspect slrmentor-backend --format '{{.Config.Image}}'
```

On AWS EC2, configure the instance's security group and any reverse proxy to expose only necessary traffic; use HTTPS for public deployments.

## 11. Manage Dependencies with uv

Add a package:

```bash
uv add package-name
```

Remove a package:

```bash
uv remove package-name
```

Sync dependencies:

```bash
uv sync
```

Update the lockfile if necessary:

```bash
uv lock
```

Commit `pyproject.toml` and `uv.lock` together after dependency changes. Rebuild and republish the Docker image when application code or dependencies change.

The native RAG retriever does not require a locally hosted embedding model or LangChain for its retrieval path.

## 12. Troubleshooting

### Flask fails to start

Check Python compatibility, dependencies, `.env`, and the application package layout:

```bash
uv sync --locked
uv run flask --app app.app run --debug
```

### MongoDB connection fails

Check the `MONGO_URI`, database user permissions, Atlas cluster availability, and Atlas network access settings.

### RAG retrieval fails

Check that `VECTOR_SEARCH_INDEX` matches the Atlas index, the correct collection is selected, the index uses the `content` field, Automated Embedding is configured, and `RAG_doc_limit` is positive. Test `/ragquery` separately from LLM requests.

### LLM requests fail

Check provider API keys, quotas, rate limits, and logs for authentication or timeout errors.

### Docker container exits immediately

```bash
docker logs slrmentor-backend
```

Verify that the runtime `.env` file was passed using `--env-file`.

### Docker build fails after dependency edits

```bash
uv lock
docker build -t slrmentor-backend .
```

## 13. Quick Start

### Local development

```bash
uv sync --locked
uv run flask --app app.app run --debug
```

### Docker on your computer

```bash
docker build -t slrmentor-backend .
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env slrmentor-backend
docker logs slrmentor-backend
```

### Update an existing Docker Hub deployment

```bash
docker stop slrmentor-backend
docker rm slrmentor-backend
docker pull seallabuofc/slrmentor-backend:latest
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:latest
```

For a first-time deployment, skip stop/remove. For production, consider using an explicit numbered release tag and a restart policy.

---

## Notes

- MongoDB Atlas hosts query embeddings and vector retrieval; the backend does not load a local embedding model.
- The application runs with Flask during local development and Gunicorn inside the production Docker image.
- `.env` is excluded from the Docker build but passed to the container with `--env-file`.
- The Docker Hub badge displays the latest recognized numbered version automatically, subject to caching.
- Publishing commands use `vX.X` as a placeholder; deployment examples use the publisher-maintained `:latest` tag.
- Existing containers must be recreated to run an updated image.
