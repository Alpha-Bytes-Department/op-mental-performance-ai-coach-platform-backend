
import openai
import os

# IMPORTANT: Paste your OpenAI API key here
# Make sure it is the exact same key you have in your .env file
API_KEY = ""

def check_key():
    """
    Makes a simple API call to OpenAI to check if the key is valid and has quota.
    """
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please paste your API key into the script before running.")
        return

    print("Setting API key...")
    openai.api_key = API_KEY
    
    print("Making a test call to the OpenAI API...")
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Using a cheaper model for the test
            messages=[{"role": "user", "content": "This is a test."}],
            max_tokens=5
        )
        print("\n--- SUCCESS! ---")
        print("The API key is working correctly.")
        print("Response from OpenAI:")
        print(response)
        
    except Exception as e:
        print("\n--- ERROR ---")
        print("The API key failed the test.")
        print("The error message from OpenAI is:")
        print(str(e))

if __name__ == "__main__":
    check_key()
