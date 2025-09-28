import os
import sys
import json
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Confirm
from rich.panel import Panel
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

def get_ai_fixes(code: str) -> str:
    """
    Communicates with the AI model to get fixes for the smart contract code.
    """
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
        return "[]"

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

def get_ai_audit_section(code: str, section_name: str, contract_name: str) -> str:
    """
    Gets a specific section of the AI audit report.
    """
    is_list_section = section_name not in ["Line by Line Analysis", "Conclusion"]

    if section_name == "Conclusion":
        prompt = f"""
          You are an expert security auditor for Midnight smart contracts.
          Analyze the following code for the contract named '{contract_name}'.
          I want you to provide the content for the 'Conclusion' section of the audit report.

          Return your response as a single, unbroken line of text with no newlines.
          The text should be a short, concise paragraph (max 150 words).
          Make important words bold using markdown `**word**` and wrap variables in backticks (e.g., `my_variable`).
          If there are no findings for this section, return an empty string.

          Here is the code:
          ```typescript
          {code}
          ```
        """
    elif is_list_section:
        prompt = f"""
          You are an expert security auditor for Midnight smart contracts.
          Analyze the following code for the contract named '{contract_name}'.
          I want you to provide the content for the '{section_name}' section of the audit report.

          Return your response as a list of bullet points, where each bullet point starts with a `- `.
          Keep the text for each bullet point concise and readable.
          If a bullet point contains a code snippet, place the snippet on a new line and indent it.
          
          For example:
          - This is a finding about a variable.
            `my_variable` has an issue.
            
          Make important words bold using markdown `**word**` and wrap variables in backticks (e.g., `my_variable`).
          If there are no findings for this section, return an empty string.

          Here is the code:
          ```typescript
          {code}
          ```
        """
    else: # Narrative section
        prompt = f"""
          You are an expert security auditor for Midnight smart contracts.
          Analyze the following code for the contract named '{contract_name}'.
          I want you to provide the content for the '{section_name}' section of the audit report.

          Return the response as a single raw string, formatted with Markdown.
          **Do not use bullet points for this section.**

          For the 'Line by Line Analysis' section, please structure your analysis as follows:
          - For each line or block of code you are analyzing, first present the code inside a Markdown code block (using triple backticks).
          - Immediately following the code block, provide your narrative analysis of that code.
          
          For example:
          ```typescript
          const from = this.owner;
          ```
          This line hardcodes the sender to be the contract owner...

          Make important words bold using markdown `**word**` and wrap variables in backticks (e.g., `my_variable`) when mentioned in the narrative text.
          If there are no findings for this section, return an empty string.

          Here is the code:
          ```typescript
          {code}
          ```
        """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        console.print(f"[bold red]Error getting '{section_name}': {e}[/bold red]")
        return ""

def review_command(file_path: str, fix: bool):
    """Handler for the 'review' command."""
    console.print(f"[blue]Analyzing {file_path}...[/blue]")
    try:
        with open(file_path, 'r') as f:
            code = f.read()
    except FileNotFoundError:
        console.print(f"[bold red]Error: File not found at '{file_path}'.[/bold red]")
        return

    if fix:
        review_data_str = get_ai_fixes(code)
        if not review_data_str or review_data_str == "[]":
            console.print("[bold red]Could not get AI review.[/bold red]")
            return
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
        # Get contract name
        with console.status("Identifying contract..."):
            contract_name_prompt = f"What is the name of the smart contract in this code? Return just the name as a plain string. \n\n```typescript\n{code}\n```"
            try:
                response = model.generate_content(contract_name_prompt)
                contract_name = response.text.strip()
            except Exception as e:
                console.print(f"[bold red]Error getting contract name: {e}[/bold red]")
                contract_name = "Unknown"

        # 1. Main Heading
        title = f"Security Audit Report - {contract_name} Smart Contract"
        console.print(Panel(title, style="bold", border_style="blue"), justify="center")

        # 2. Description Text
        description = f"This report details the findings of a security audit performed on the provided {contract_name} smart contract code. The audit focused on identifying security vulnerabilities, privacy leaks, logic errors, and deviations from best practices."
        console.print(description, justify="center")
        console.print() # Spacer

        # 3. Code Snippet
        console.print("[bold underline]Code Snippet[/bold underline]")
        console.print(Markdown(f"```typescript\n{code}\n```", code_theme="monokai"))
        console.print() # Spacer

        # 4. Audit Findings
        console.print("[bold underline]Audit Findings[/bold underline]", justify="center")
        console.print() # Spacer

        sections = [
            "Security Vulnerabilities",
            "Privacy Leaks",
            "Logic Errors",
            "Line by Line Analysis",
            "Best Practices",
            "Recommendations",
            "Conclusion"
        ]

        for i, section_name in enumerate(sections, 1):
            console.print(f"[bold]{i}. {section_name}[/bold]", justify="center")
            with console.status(f"Generating {section_name}..."):
                section_content_str = get_ai_audit_section(code, section_name, contract_name)
            
            if section_content_str.strip():
                console.print(Markdown(section_content_str, code_theme="monokai"))
            else:
                console.print("[dim]No findings for this section.[/dim]")
            
            console.print() # Spacer
def chat_command(file_path: str | None = None):
    """Handler for the 'chat' command."""
    console.print("[green]Starting interactive chat... (Type 'exit' to quit)[/green]")

    initial_prompt = "You are a helpful AI assistant specializing in Midnight smart contracts. Keep your answers concise and clear."

    if file_path:
        try:
            with open(file_path, 'r') as f:
                file_content = f.read()
            initial_prompt += f"\n\nThe user has provided the following file for context:\n\n---\n{file_path}\n---\n\n{file_content}\n\n---"
            console.print(f"[blue]Chatting about {file_path}...[/blue]")
        except FileNotFoundError:
            console.print(f"[bold red]Error: File not found at '{file_path}'. Starting a general chat session.[/bold red]")
        except Exception as e:
            console.print(f"[bold red]Error reading file: {e}. Starting a general chat session.[/bold red]")

    chat_model.send_message(initial_prompt)

    while True:
        try:
            user_input = console.input("[bold cyan]You: [/bold cyan]")
            if user_input.lower() == 'exit':
                break

            match = re.match(r"^(?:load|read) file (.+)$", user_input.strip(), re.IGNORECASE)
            if match:
                file_path = match.group(1)
                try:
                    with open(file_path, 'r') as f:
                        file_content = f.read()
                    
                    file_prompt = f"The user has requested to load a new file for context:\n\n---\n{file_path}\n---\n\n{file_content}\n\n---"
                    response = chat_model.send_message(file_prompt)
                    
                    console.print(f"[blue]Loaded {file_path} into the conversation.[/blue]")
                    console.print("[bold yellow]AI:[/bold yellow]", Markdown(response.text))

                except FileNotFoundError:
                    console.print(f"[bold red]Error: File not found at '{file_path}'.[/bold red]")
                except Exception as e:
                    console.print(f"[bold red]Error reading file: {e}.[/bold red]")
                continue

            response = chat_model.send_message(user_input)
            console.print("[bold yellow]AI:[/bold yellow]", Markdown(response.text))

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
        if len(args) > 2:
            console.print("[bold red]Usage: midnight-ai chat [file][/bold red]")
            return
        file_path = args[1] if len(args) > 1 else None
        chat_command(file_path)
    else:
        console.print(f"[bold red]Unknown command: {command}[/bold red]")
if __name__ == "__main__":
    main()