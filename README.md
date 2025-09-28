# Midnight AI Smart Contract Assistant (Python Edition)

This is a command-line tool that uses AI to help you review, debug, and improve smart contracts for the Midnight protocol. This version uses a powerful **Python backend** for all the core logic, wrapped by a lightweight Node.js executable for easy installation.



## Features

- **AI-Powered Code Review**: Get a detailed analysis of your smart contract for security vulnerabilities, privacy leaks, and logic errors.
- **Auto-Fixing**: Automatically apply the AI's suggested fixes to your code after your approval.
- **Interactive Chat**: Ask questions about your code or general Midnight concepts and get instant answers.
- **Python Core**: All logic is handled by a robust Python script.

## Setup and Installation

### 1. Prerequisites

- [**Python 3**](https://www.python.org/downloads/)
- [**Node.js**](https://nodejs.org/) (for the `npm` installer)
- A **Google Gemini API Key**

### 2. Get Your API Key

1.  Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Sign in with your Google account.
3.  Click "**Create API key in new project**".
4.  Copy the generated API key.

### 3. Installation Steps

1.  **Save all the files** provided into a new directory on your computer.

2.  **Set up your environment variables**:
    -   Find the `.env` file in the project.
    -   Open it and replace `YOUR_API_KEY_HERE` with the API key you copied from Google AI Studio.

3.  **Install Python dependencies**: Open your terminal in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install the Node.js wrapper**: This step creates the global `midnight-ai` command.
    ```bash
    npm install -g .
    ```
    *(Note: On some systems, you may need to run this with `sudo`)*

## How to Use (Testing the Tool)

You can test the tool using the provided `sample_contract.ts` file.

### Reviewing Code

To get a simple, read-only review of the contract, run this command from any directory:
```bash
midnight-ai review sample_contract.ts