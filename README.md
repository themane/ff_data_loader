# FF Data Loader

A FastAPI-based application for uploading and processing CSV data using a configurable data loader service.

## Prerequisites

### Installing Python

1. Download Python from the official website: [python.org](https://www.python.org/downloads/)
2. Choose Python 3.8 or higher for best compatibility.
3. During installation, ensure you check the option to "Add Python to PATH" to make it accessible from the command line.
4. Verify installation by opening a terminal and running:
   ```
   python --version
   ```
   You should see the installed Python version.

### Using pip

pip is Python's package installer, included with Python installations. It allows you to install packages from the Python Package Index (PyPI).

- To check if pip is installed: `pip --version`
- To install a package: `pip install package_name`
- To install from a requirements file: `pip install -r requirements.txt`

## Installation

1. Clone this repository to your local machine.
2. Navigate to the project directory.
3. Install the required dependencies using pip:
   ```
   pip install -r requirements.txt
   ```
   This will install FastAPI, Uvicorn (ASGI server), PyYAML, requests, and python-dateutil.

## Usage

### Running the Application

Start the FastAPI server using Uvicorn:
```
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

### API Endpoints

- **GET /**: Returns a welcome message.
- **POST /load**: Upload a CSV file for processing.
  - Accepts a CSV file via multipart/form-data.
  - query parameter: `asset_name` (string) - specifies the name for the asset.
  - Processes the CSV data using the configured DataLoader service.
  - Returns a success message upon completion.

To upload a CSV, use tools like curl, Postman, or any HTTP client:

Example with curl:
```
curl -X POST "http://127.0.0.1:8000/load?asset_name='Amex Credit Card'" -F "file=@your_file.csv"
```

Resource File Example:
```
firefly:
  base_url: "firefly_url"
  token: "generate token and insert here"

app:
  currency: "INR"
  batch_size: 25
  apply_rules: true
```

The application uses FastAPI to provide a simple REST API for CSV uploads, leveraging asynchronous file handling for efficient processing.