# common

The `common` folder contains the basic components for running and configuring the project: dependencies, database connection settings, and environment variables.

## Folder contents

- **requirements.txt** — a list of required Python libraries. Install dependencies with the command:
    ```
    pip install -r requirements.txt
    ```
- **db.connect.py** — a script for connecting to the database. Uses parameters from the `.env` file.
- **.env.example** — an example file with environment variables. Copy and rename it to `.env`, then specify your values:
    ```
    cp .env.example .env
    ```
    Example contents:
    ```
    DB_HOST=localhost
    DB_PORT=6432
    DB_USER=username
    DB_PASSWORD=yourpassword
    DB_NAME=yourdatabase
    ```
- **.gitignore** — ignores the `.env` file and other sensitive or temporary files to avoid publishing secrets to the repository.

## Quick Start

1. Copy `.env.example` and rename it to `.env`, then fill in your data.
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Use the `db.connect.py` script to connect to your database.

## Security

The `.env` file should not be included in the public repository. For this purpose, `.gitignore` is used.