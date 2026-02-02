# SLRmentor App Backend

This is the backend for the **SEALL** application — a tool for generating and refining academic search strings and inclusion/exclusion criteria using AI (Gemini & GPT), MongoDB, and Flask.

---

## Requirements

Make sure you have the following installed:

- [Python](https://www.python.org/downloads/)
- [Anaconda](https://www.anaconda.com/download)
- [MongoDB Community Edition](https://www.mongodb.com/try/download/community)
- Create .env file
---

## Project Structure

```
SEALL/
├── backend/
│   ├── .env
│   ├── app.py
│   ├── environment.yml
│   └── helpers/
│       ├── llm/
│       ├── xploreapi/
│       └── ...
```

---

## .env File

Create a file called `.env` inside the `backend/` directory with the following content:

```env
GPT_API_KEY="your-gpt-api-key"
GEMINI_API_KEY="your-gemini-api-key"
ENCRYPTION_KEY="your-encryption-key"
MONGO_URI="mongodb://localhost:27017/seall"
MONGO_USER="sealluser"
MONGO_PASSWORD="securepassword123"
MONGO_DATABASE="SEALLDB"
```

Change the placeholder values to your actual keys, encryption key, and MongoDB credentials if different.
You will need to aquire the AI API keys by yourself. You only really need one, either Gemini free tier key or the OPENAI key.
Both are recommended.
---

## Setting Up the Conda Environment

Open a terminal and navigate to the `backend/` directory:

```bash
cd backend
```

Create the environment from the existing `environment.yml` file:

```bash
conda env create -f environment.yml
```

Activate the environment:

```bash
conda activate seallapp
```

---

# Running MongoDB

You must have MongoDB running **before** starting the Flask app. Here's how:

### 🔸 Linux (Ubuntu/Debian)
You can figure out how to install it for your distro....
Start MongoDB using systemd:

```bash
sudo systemctl start mongod
```
Check status with:
```
sudo systemctl status mongod
```
---

### 🔸 Windows

1. **Install MongoDB** from the official MSI installer:  
   https://www.mongodb.com/try/download/community

2. By default, MongoDB is installed as a **Windows service** and starts automatically.  
   If it's not running, open **Command Prompt as Administrator** and run:

   ```cmd
   net start MongoDB
   ```

3. If you prefer to run it manually (not as a service), use:

   ```cmd
   "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath C:\data\db
   ```

   > Replace `7.0` with your installed version, and make sure `C:\data\db` exists.  
   You can create it with:

   ```cmd
   mkdir C:\data\db
   ```

---

## Running the Flask App

From the activated Conda environment in the `backend/` directory, run:

```bash
python -m flask run
```

If everything is working, you’ll see something like:

```
* Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

You can visit [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to check if the server is live.

---

## API Endpoints Overview

| Endpoint                    | Method | Description                              |
|-----------------------------|--------|------------------------------------------|
| `/`                         | GET    | Test if server is live                   |
| `/createchat`              | POST   | Creates a new chat session               |
| `/getchathistory`          | POST   | Retrieves search string chat history     |
| `/prompt`                  | POST   | Sends a message and gets LLM response. This is for search strings  |
| `/conversionformats`       | GET    | Lists available search string formats    |
| `/convertsearchstring`     | POST   | Converts search string to another format |
| `/criteria`                | POST   | Generates/refines inclusion criteria     |
| `/getcriteriachathistory`  | POST   | Retrieves criteria chat history          |

---

## 🛠 Notes

- MongoDB must be running **before** starting the Flask app.
- The `.env` file is critical — missing keys will cause the app to fail.
- 

---

## ✅ Example Workflow

1. Start MongoDB
2. Navigate to backend: `cd backend`
3. Activate Conda env: `conda activate seallapp`
4. Run: `python -m flask run`
5. Access at: `http://127.0.0.1:5000/`

---

1️⃣ Build the image from the current directory in the backend
docker build -t seallabuofc/slrmentor-backend:v2.1 .

Optionally, also tag it as latest:
docker tag seallabuofc/slrmentor-backend:v2.1 seallabuofc/slrmentor-backend:latest


2️⃣ Run the container with the .env file
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:v2.0

3️⃣ Log in to Docker Hub (if not already)
docker login

4️⃣ Push the new image to Docker Hub

Push the version tag:

docker push seallabuofc/slrmentor-backend:v2.1

docker push seallabuofc/slrmentor-backend:latest


6️⃣ Pull the updated image on other machines

If you want to run this updated image elsewhere:

docker pull seallabuofc/slrmentor-backend:latest
docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:lat


## In ec2 instance

docker stop slrmentor-backend

docker rm slrmentor-backend

docker pull seallabuofc/slrmentor-backend:latest

docker run -d --name slrmentor-backend -p 5000:5000 --env-file .env seallabuofc/slrmentor-backend:latest

