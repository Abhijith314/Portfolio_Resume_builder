import requests
import re

def generate_experience_description(keywords):
    """Generates bullet points for work experience from keywords."""
    prompt = f"""
    Based on the following keywords for a job role, generate 2-3 professional, action-oriented bullet points for a resume's experience section.
    Each bullet point must start with a strong action verb (e.g., "Developed," "Managed," "Implemented").
    Do not use markdown like '*' or '-'. Separate each point with a newline.

    Keywords: "{keywords}"
    Example Output:
    Developed a responsive and user-friendly frontend for an e-commerce website using Angular.
    Worked with tools like Google Analytics and Microsoft Clarity to track user behavior.

    Generate the bullet points:
    """
    return call_gemini_api(prompt)

def generate_project_description(brief):
    """Generates a single bullet point for a project from a brief description."""
    prompt = f"""
    Based on the following brief for a project, write a single, professional, action-oriented bullet point for a resume's project section.
    The bullet point must start with a strong action verb (e.g., "Developed," "Designed," "Built").
    Do not use markdown like '*' or '-'.

    Brief: "{brief}"
    Example Output:
    Developed a responsive and user-friendly frontend for an e-commerce website using Angular.

    Generate the bullet point:
    """
    return call_gemini_api(prompt)

def generate_summary_options(user_data):
    """Generates three distinct professional summary options."""
    details = [f"Professional Title: {user_data.get('title', 'N/A')}"]
    if user_data.get('experiences'):
        details.append(f"Key Experience: " + ", ".join([f"{exp.get('role')}" for exp in user_data['experiences']]))
    if user_data.get('projects'):
        details.append(f"Key Projects: " + ", ".join([proj.get('name') for proj in user_data['projects']]))
    
    prompt = f"""
    Based on these details: {', '.join(details)}.
    Write three distinct, professional summaries for a resume. Each summary should be a single paragraph of 2-3 sentences.
    Format the output with each summary separated by '---'.
    
    Example:
    A determined and self-motivated individual...
    ---
    Results-oriented professional with experience in...
    ---
    Creative and detail-oriented developer with a passion for...

    Generate the three summaries:
    """
    response_text = call_gemini_api(prompt)
    # Split the response into a list of summaries
    return [summary.strip() for summary in response_text.split('---') if summary.strip()]


def call_gemini_api(prompt):
    """A helper function to call the Gemini API."""
    GEMINI_FLASH_API_KEY = "YOUR_GEMINI_API_KEY" # Replace with your actual key
    GOOGLE_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_FLASH_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt.strip()}]}]}

    try:
        response = requests.post(url=GOOGLE_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()['candidates'][0]['content']['parts'][0]['text']
        # Clean up any markdown that might be returned
        return re.sub(r'[\*\-]', '', result).strip()
    except Exception as e:
        print(f"Error calling AI model: {e}")
        return "Failed to generate content."
