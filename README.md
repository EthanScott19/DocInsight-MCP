# MCP DocInsight

MCP DocInsight is a document-driven system that parses structured graduate application PDFs, stores the extracted data in a SQLite database, and allows users to query that data using natural language.

## Overview

This system demonstrates a controlled architecture for integrating large language models with databases. Instead of allowing the LLM to generate raw SQL, it produces structured tool calls that are validated and executed by an MCP (Model Context Protocol) layer.

## Features

- Parse structured PDF application forms into JSON
- Store application data in a SQLite database
- Batch ingest directories of PDFs
- Deduplicate files based on filename
- Query data using natural language
- Safe execution through validated tool calls
- Support for filtering and aggregation queries

## How It Works

1. A PDF is parsed into a structured Python dictionary
2. The parsed data is staged as JSON
3. The data is inserted into a SQLite database
4. A user enters a natural language query
5. The LLM converts the query into a structured tool call
6. The MCP layer validates the tool call
7. The database executes the corresponding query
8. Results are returned to the user

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/EthanScott19/DocInsight-MCP.git
```
### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Cohere API Key Setup

This project requires a Cohere API key.

### Step 1: Create an API key

Visit:
https://dashboard.cohere.com/api-keys

Generate a new API key.

### Step 2: Set environment variable

macOS / Linux:
```bash
export COHERE_API_KEY="your_api_key_here"
```
Optional (persist across sessions):
```bash
echo 'export COHERE_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 3: Verify
```bash
echo $COHERE_API_KEY
```

## Running the Application

From the project root:
```bash
cd MCP-DocInsight
./start.sh
```
## Usage

### Option 1: Ask a Question

Example queries:

How many applicants are there?
How many BIO applicants had at least a 3.5 GPA?
Show CSC applicants above 3.2 GPA
Show provisional admissions for Fall 2025

### Option 2: Upload PDFs

You can upload:
- A single PDF file
- A directory of PDFs for batch ingest

Batch ingest behavior:
- Detects new files based on filename
- Allows user to exclude files before processing
- Moves successfully processed files to processed/
- Moves failed files to failed/

## Notes

- API keys are not included in the repository
- Each user must provide their own Cohere API key
- Duplicate PDFs are skipped based on filename

## Future Improvements
- Add more tools
- Improve result formatting

## Authors

- Ethan Scott
- Justin Cornell
- Garrick Mills