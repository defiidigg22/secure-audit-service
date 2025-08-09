# Secure, Tamper-Proof Auditing Service

## Description

This project is a full-stack web service that provides a secure, tamper-proof logging system. It uses cryptographic principles and a Merkle Tree data structure to ensure that once a log is recorded and sealed, it cannot be altered without detection. The service is built with a Python Flask backend, a SQLite database, and a simple vanilla JavaScript frontend for interaction and testing.

This project was built to demonstrate a practical application of data structures and security concepts beyond typical CRUD applications.

---

## Key Features

* **Tamper-Proof Logging:** Utilizes a Merkle Tree to create a verifiable chain of logs. Any modification to a past log will invalidate the Merkle Root.
* **Log Verification:** A dedicated API endpoint (`/verify/log/<id>`) can mathematically prove that a specific log is authentic and part of its sealed batch.
* **Secure API:** Endpoints for adding and sealing logs are protected by API key authentication.
* **Persistent Storage:** All logs and batch metadata are stored in a robust SQLite database.
* **Interactive Dashboard:** A simple HTML/JS frontend allows for easy interaction with the API for adding, sealing, and testing the service.

---

## Tech Stack

* **Backend:** Python 3, Flask
* **Database:** SQLite 3
* **Frontend:** HTML, CSS, Vanilla JavaScript
* **Core Logic:** Merkle Tree implementation in Python

---

## Setup and Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**
    This only needs to be run once to create the `audit.db` file and its tables.
    ```bash
    python init_db.py
    ```

5.  **Run the Flask application:**
    ```bash
    python app.py
    ```
    The service will be running at `http://127.0.0.1:5000`.

6.  **Access the Dashboard:**
    Open your web browser and navigate to `http://127.0.0.1:5000/dashboard`.