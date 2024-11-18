# RelyHome Parser

A script to automate data parsing and interaction with Google Sheets and a web application.

## Features

- Integration with Google Sheets API.
- Environment variable-based configuration for enhanced security.
- Supports flexible configuration of city and system values.
- Logs with customizable log levels for debugging and monitoring.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Environment Variables](#environment-variables)
5. [Customization](#customization)
6. [Logging](#logging)

---

## Requirements

- Python 3.8 or later
- `pip` for managing Python dependencies

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/relyhome-parser.git
    cd relyhome-parser
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory with your environment variables. (See [Environment Variables](#environment-variables))

## Usage

Run the script with the following command:
```bash
python main.py
 ```

# Environment Variables
 - Create a `.env` file in rely_home_parser folder to securely store sensitive data. Example:
```
# Logging
LOGLEVEL=INFO

# Google API
SAMPLE_SPREADSHEET_ID=your_google_sheet_id
SAMPLE_RANGE_NAME=your_sheet_name !B2:B
TOKEN_FILE=token.json
CREDENTIALS_FILE=credentials.json

# Web application credentials
MAIN_URL=https://relyhome.com/login/
LOGIN=your_login
PASSWORD=your_password
```

# Environment Variables Explained
`LOGLEVEL`: Defines the log level. Options: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET.
`SAMPLE_SPREADSHEET_ID`: Your Google Sheets ID.
`SAMPLE_RANGE_NAME`: The range in your Google Sheets to fetch data.
`TOKEN_FILE`: Path to the token file for Google API authorization.
`CREDENTIALS_FILE`: Path to the credentials JSON file for Google API.
`FILE_PATH`: Path to the local file to interact with (e.g., .xlsx).
`MAIN_URL`: URL of the web application.
`LOGIN`: Login credentials for the web application.
`PASSWORD`: Password for the web application.

# Customization
### Systems with Value.
- You can configure system-specific values by modifying the `SYSTEMS_WITH_VALUE` dictionary in the script:
``SYSTEMS_WITH_VALUE = {
    "Dryer": 1,
    "Microwave": 1,
}``
### Cities with Value
- Edit the CITIES_WITH_VALUE dictionary to customize city-specific logic:
``CITIES_WITH_VALUE = {
    "Dallas": 1,
    "Irving": 1,
    "Arlington": 1,
    "Garland": 0,
    "Sachse": 0,
    "Wylie": 0,
    "Rowlett": 0,
    "Mesquite": 0,
}``
### Zip Codes
- Add zip codes in the ZIP_CODES dictionary as needed:
``ZIP_CODES = {
    "75001": 1,
    "75002": 0,
}``
### Logging
Logs are written to the console with the specified log level. The default is `INFO`. Modify the `LOGLEVEL` variable in your .env file to adjust.

Supported levels:

- ``CRITICAL``
- ``ERROR``
- ``WARNING``
- ``INFO``
- ``DEBUG``
- ``NOTSET``
- 
#### Example log output:
```2024-11-18 14:00:00 INFO relyhome.parser Configuration loaded: LOGLEVEL=DEBUG, ...```
