# SLRmentor 

The app is a tool designed to assist researchers in initiating their **Systematic Literature Reviews**. The app helps generate search strings for academic databases and define inclusion/exclusion criteria based on user inputted context such as their research topic and research questions. Featuring a ChatGPT-style web interface, the app enables users to interact with an AI using natural language to create and refine search strategies and criteria. Users can continue the conversation to tailor the results to their specific needs. Additionally, the app saves chat histories using a unique generated hash, allowing for easy sharing of conversations without the need for user login—ideal for collaborative use when the app is deployed online.

---

## Overview

The app consists of two main parts:

- **Backend:**  
  A Flask-based server application that handles all the core logic, API endpoints, and connects to a MongoDB database to store and manage data.

- **Frontend:**  
  A user-friendly website interface through which researchers interact with the app to generate search queries and manage their review parameters.

---

## Running the App Locally

To run the app locally on your machine, please follow the recommended order by visiting the README files inside the backend and frontend folders of this repository:

1. **Backend README:**  
   Contains detailed instructions on setting up the Python environment, configuring the `.env` file, running MongoDB, and starting the Flask server.

2. **Frontend README:**  
   Explains how to install dependencies and run the frontend web application that connects to the backend.

Following these README files in order will ensure the app runs smoothly on your system.

---
