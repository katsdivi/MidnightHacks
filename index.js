#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Get the arguments passed to the CLI
const args = process.argv.slice(2);

// Construct the path to the Python executable inside the virtual environment
const pythonExecutable = path.join(__dirname, 'venv', 'bin', 'python');
const pythonScriptPath = path.join(__dirname, 'main.py');

// Check if the venv python exists, otherwise fall back to system python3
const pythonCmd = fs.existsSync(pythonExecutable) ? pythonExecutable : 'python3';

// Execute the Python script
const pythonProcess = spawn(pythonCmd, [pythonScriptPath, ...args], {
    stdio: 'inherit'
});

pythonProcess.on('error', (err) => {
    console.error('Failed to start Python process.');
    console.error('Please ensure Python 3 is installed and you have run the setup steps in the README.');
    console.error(err);
});