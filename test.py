from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

def deepseek_compare(line1, candidates):
    prompt = (
        "You are an expert in matching betting options from different bookmakers. "
        "Given the following betting option from one bookmaker:\n"
        f"'{line1}'\n"
        "Find the most similar option from the following list of options from another bookmaker:\n"
        + "\n".join([f"- '{cand}'" for cand in candidates]) +
        "\nReturn only the most similar option as plain text, or 'None' if no good match exists."
    )
    
    try:
        print(f"Sending request to OpenRouter API for comparing: '{line1}'")
        response = client.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        result = response.choices[0].message.content.strip()
        print(f"API response received: {result}")
        return result if result != "None" else None
    except Exception as e:
        print(f"Error calling OpenRouter API with DeepSeek R1: {e}")
        return None

# Test the function with some sample data
if __name__ == "__main__":
    test_line = "Τελικό Αποτέλεσμα 1 3.40"
    test_candidates = [
        "Τελικό Αποτέλεσμα Μπόντο Γκλιμτ 3.40",
        "Τελικό Αποτέλεσμα Ισοπαλία 3.45",
        "Τελικό Αποτέλεσμα Λάτσιο 2.23"
    ]
    
    print("Testing bet matching...")
    result = deepseek_compare(test_line, test_candidates)
    
    if result:
        print(f"Match found: '{test_line}' matches with '{result}'")
    else:
        print(f"No match found for '{test_line}'")