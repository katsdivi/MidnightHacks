import os
import sys
import json
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
import difflib
import re

# --- Setup ---
load_dotenv()
console = Console()

try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # CORRECTED: Using a current, widely available model
    model = genai.GenerativeModel('gemini-2.0-flash')
    chat_model = model.start_chat(history=[])
except Exception as e:
    console.print(f"[bold red]Error configuring AI model: {e}[/bold red]")
    console.print("Please make sure your .env file and API key are set up correctly.")
    sys.exit(1)
    
# --- Core Functions ---

def get_ai_review(code: str, enable_fix: bool = False) -> str:
    """
    Communicates with the AI model to get a review of the smart contract code.
    """
    if enable_fix:
        prompt = f"""
          You are an expert security auditor and code refactoring tool for Midnight smart contracts.
          Analyze the following code for security, privacy, logic, and best-practice issues.
          Your response MUST be a valid JSON array of objects. Each object represents a single issue and suggested fix.
          Each JSON object must have the following keys:
          - "lineNumber": The starting line number of the code to be replaced.
          - "endLineNumber": The ending line number of the code block to be replaced. For a single-line change, this is the same as lineNumber.
          - "explanation": A brief, one-sentence explanation of the issue and the fix.
          - "originalCode": The exact original code snippet that needs to be replaced.
          - "suggestedCode": The exact code snippet that should replace the original.
          If there are no issues, return an empty array [].
          Here is the code:
          ```typescript
          {code}
          ```
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_message = str(e)
            if "is not found" in error_message or "does not have access" in error_message:
                console.print("[bold red]AI Model Access Error:[/bold red]")
                console.print("The configured model is not available for your API key or project.")
                console.print("1. Ensure billing is enabled on your Google Cloud project.")
                console.print("2. Check that the 'Generative Language API' (or 'Vertex AI API') is enabled.")
                console.print(f"3. Verify your project has access to the model being used.")
                console.print(f"[dim]Details: {error_message}[/dim]")
            else:
                console.print(f"[bold red]Error contacting AI model: {e}[/bold red]")
            return "[]" if enable_fix else "Could not get AI review."
    else:
        prompt = f"""
          You are an expert security auditor for Midnight smart contracts.
          Provide a line-by-line review of the following smart contract code.
          Focus on:
          1. Security Vulnerabilities
          2. Privacy Leaks
          3. Logic Errors
          4. Best Practices
          Provide your output as a Markdown-formatted report.
          Here is the code:
          ```typescript
          {code}
          ```
        """
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_message = str(e)
            if "is not found" in error_message or "does not have access" in error_message:
                console.print("[bold red]AI Model Access Error:[/bold red]")
                console.print("The configured model is not available for your API key or project.")
                console.print("1. Ensure billing is enabled on your Google Cloud project.")
                console.print("2. Check that the 'Generative Language API' (or 'Vertex AI API') is enabled.")
                console.print(f"3. Verify your project has access to the model being used.")
                console.print(f"[dim]Details: {error_message}[/dim]")
            else:
                console.print(f"[bold red]Error contacting AI model: {e}[/bold red]")
            return "[]" if enable_fix else "Could not get AI review."

def apply_fixes(file_path: str, fixes: list):
    """
    Applies the suggested fixes to the file after user confirmation.
    """
    if not fixes:
        console.print("[green]✅ No issues found or no fixes suggested.[/green]")
        return

    with open(file_path, 'r') as f:
        original_code_lines = f.readlines()

    modified_code_lines = list(original_code_lines)

    for fix in sorted(fixes, key=lambda x: x['lineNumber'], reverse=True):
        start = fix['lineNumber'] - 1
        end = fix.get('endLineNumber', start + 1) -1
        replacement = fix['suggestedCode'].splitlines(True)
        # Ensure we add a newline if the replacement doesn't have one, but the original did
        if replacement and not replacement[-1].endswith('\n') and original_code_lines[end].endswith('\n'):
            replacement[-1] += '\n'
        modified_code_lines[start : end + 1] = replacement

    diff = difflib.unified_diff(original_code_lines, modified_code_lines, fromfile=f"a/{file_path}", tofile=f"b/{file_path}")
    console.print("\n[yellow bold]--- Proposed Changes ---[/yellow bold]")
    for line in diff:
        line = line.strip()
        if line.startswith('+') and not line.startswith('+++'):
            console.print(f"[green]{line}[/green]")
        elif line.startswith('-') and not line.startswith('---'):
            console.print(f"[red]{line}[/red]")
    console.print("[yellow bold]--- End of Changes ---\n[/yellow bold]")

    if Confirm.ask("Do you want to apply these fixes?"):
        with open(file_path, 'w') as f:
            f.writelines(modified_code_lines)
        console.print("[green]✅ Fixes applied successfully![/green]")
    else:
        console.print("[gray]Aborted. No changes were made.[/gray]")

def review_command(file_path: str, fix: bool):
    """Handler for the 'review' command."""
    console.print(f"[blue]Analyzing {file_path}...[/blue]")
    try:
        with open(file_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        console.print(f"[bold red]Error: File not found at '{file_path}'.[/bold red]")
        return

    review_data_str = get_ai_review(code, enable_fix=fix)

    if fix:
        try:
            json_str = review_data_str.replace("```json", "").replace("```", "").strip()
            # Sanitize the JSON response by removing all control characters except for the ones that are allowed in JSON.
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
            fixes = json.loads(json_str)
            apply_fixes(file_path, fixes)
        except json.JSONDecodeError as e:
            console.print("[bold red]Error: Could not parse JSON from AI response.[/bold red]")
            console.print(f"Error: {e}")
            console.print(f"Raw Response: {review_data_str}")
    else:
        console.print("\n[blue bold]--- AI Review ---[/blue bold]")
        console.print(Markdown(review_data_str))
        console.print("[blue bold]--- End of Review ---\n[/blue bold]")
def chat_command():
    """Handler for the 'chat' command."""
    console.print("[green]Starting interactive chat... (Type 'exit' to quit)[/green]")

    chat_model.send_message("You are a helpful AI assistant specializing in Midnight smart contracts. Keep your answers concise and clear.")

    while True:
        try:
            user_input = console.input("[bold cyan]You: [/bold cyan]")
            if user_input.lower() == 'exit':
                break
            
            response = chat_model.send_message(user_input)
            console.print(f"[bold yellow]AI:[/bold yellow] {Markdown(response.text)}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]An error occurred: {e}[/bold red]")
            break
    console.print("\n[yellow]Chat session ended.[/yellow]")
def main():
    """Main function to parse arguments and run commands."""
    args = sys.argv[1:]

    if not args:
        console.print("[bold red]Usage: midnight-ai <command> [options][/bold red]")
        console.print("Commands: review, chat")
        return

    command = args[0]

    if command == 'review':
        if len(args) < 2:
            console.print("[bold red]Usage: midnight-ai review <file> [--fix][/bold red]")
            return
        file_path = args[1]
        fix_flag = '--fix' in args
        review_command(file_path, fix=fix_flag)
    elif command == 'chat':
        chat_command()
    else:
        console.print(f"[bold red]Unknown command: {command}[/bold red]")
if __name__ == "__main__":
    main()