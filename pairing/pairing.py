import difflib
import json
import random
import re
import os
from dotenv import load_dotenv
from openai import APIError, AuthenticationError, OpenAI

# Load the API key from the .env file
load_dotenv("api_key.env")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("API key not found. Please set it in the api_key.env file.")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)
def ai_compare(line1, candidates, use_api=True):
    """Compare a betting option against candidates using API or fallback to rules-based matching."""
    if use_api:
        try:
            # Step 1: Compute similarity scores for all candidates
            similarities = []
            for cand in candidates:
                # Remove odds for fair comparison
                line1_without_odds = " ".join(line1.split()[:-1])
                cand_without_odds = " ".join(cand.split()[:-1])
                ratio = difflib.SequenceMatcher(None, line1_without_odds, cand_without_odds).ratio()
                similarities.append((cand, ratio))

            # Step 2: Sort candidates by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Step 3: Select the top 10 candidates (or fewer if less available)
            N = 10
            top_candidates = [cand for cand, ratio in similarities[:N]]
            print(f"Sending {len(top_candidates)} candidates to API for '{line1}'")

            # Step 4: Construct the prompt with limited candidates
            prompt = (
                "You are an expert in matching betting options from different bookmakers. "
                "Given the following betting option from Stoiximan bookmaker:\n"
                f"'{line1}'\n"
                "Find the most similar option from the following list of options from Winmasters bookmaker:\n"
                + "\n".join([f"- '{cand}'" for cand in top_candidates]) + "\n\n"
                "Important rules:\n"
                "1. In betting terminology, '1' means home team, 'X' means draw, and '2' means away team\n"
                "2. Return ONLY THE EXACT AND COMPLETE match from the candidates list\n"
                "3. Return 'None' if no good match exists\n"
                "Do not add any explanations, just return the exact matching string."
            )

            # Step 5: Call the API
            response = client.chat.completions.create(
                model="google/gemini-flash-1.5-8b ",
                messages=[
                    {"role": "system", "content": "You are a betting market matching expert"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                stream=False
            )

                        # Step 6: Process the API response
            if not response.choices:
                print("No choices returned by API")
                return rules_based_matching(line1, candidates)
            
            result = response.choices[0].message.content.strip().replace("'", "").replace("\"", "")
            print(f"API returned: '{result}'")
            
            # Verify the result is valid
            if result in candidates:
                return result
            else:
                # Try to find the closest candidate
                best_candidate = None
                best_similarity = 0
                
                for candidate in candidates:
                    # Normalize both strings for comparison (remove odds, lowercase)
                    norm_result = " ".join(result.split()[:-1]).lower() if result.split() else ""
                    norm_candidate = " ".join(candidate.split()[:-1]).lower() if candidate.split() else ""
                    
                    # Check for Greek/Latin character mixups
                    norm_result = norm_result.replace('t', 'τ')  # Replace Latin 't' with Greek 'τ'
                    
                    similarity = difflib.SequenceMatcher(None, norm_result, norm_candidate).ratio()
                    if similarity > best_similarity and similarity > 0.9:  # High threshold
                        best_similarity = similarity
                        best_candidate = candidate
                
                if best_candidate:
                    print(f"Found close API match: '{best_candidate}' with confidence {best_similarity:.2f}")
                    return best_candidate
                else:
                    print("API returned invalid match, falling back to rules-based matching")
                    return rules_based_matching(line1, candidates)
        except AuthenticationError as e:
            print(f"Authentication error: {e}")
            return rules_based_matching(line1, candidates)
        except APIError as e:
            print(f"API error: {e}")
            return rules_based_matching(line1, candidates)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return rules_based_matching(line1, candidates)
    else:
        return rules_based_matching(line1, candidates)

def rules_based_matching(line1, candidates):
    """Fallback method to match betting options using string similarity."""
    print(f"Using rules-based matching for: '{line1}'")
    best_match = None
    best_ratio = 0
    for candidate in candidates:
        line1_without_odds = " ".join(line1.split()[:-1])
        candidate_without_odds = " ".join(candidate.split()[:-1])
        ratio = difflib.SequenceMatcher(None, line1_without_odds, candidate_without_odds).ratio()
        if ratio > best_ratio and ratio > 0.7:  # Threshold of 0.7 for a good match
            best_ratio = ratio
            best_match = candidate
    if best_match:
        print(f"Found fuzzy match: '{best_match}' with confidence {best_ratio:.2f}")
        return best_match
    return None

def read_file(file_path):
    """Read lines from a file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file.readlines()]

def write_paired_file(output_file, paired, unpaired_stoiximan, unpaired_winmasters):
    """Write paired and unpaired items to output file"""
    with open(output_file, 'w', encoding='utf-8') as file:
        # Write paired items
        for pair in paired:
            file.write(pair + '\n')
        
        # Write unpaired items
        for unpaired in unpaired_stoiximan:
            file.write(f"stoiximan {unpaired}\n")
        for unpaired in unpaired_winmasters:
            file.write(f"winmasters {unpaired}\n")



def main():
    # File paths
    stoiximan_file = 'bet_names_stoiximan.txt'
    winmasters_file = 'bet_names_winmasters.txt'
    output_file = 'paired.txt'
    
    # Read input files
    print(f"Reading input files: {stoiximan_file} and {winmasters_file}")
    stoiximan_lines = read_file(stoiximan_file)
    winmasters_lines = read_file(winmasters_file)
    
    # Shuffle the stoiximan lines to process them in random order
    random.shuffle(stoiximan_lines)
    
    # Control whether to use API or just rules-based matching
    use_api = True  # Set to False to skip API calls and use only rules-based matching
    
    # Prepare data structures
    paired = []
    unpaired_stoiximan = []
    unpaired_winmasters = winmasters_lines.copy()
    
    # Process each stoiximan line
    print(f"Starting pairing process...")
    for stoix_line in stoiximan_lines:
        matching_line = ai_compare(stoix_line, unpaired_winmasters, use_api)
        
        if matching_line:
            paired.append(f"stoiximan {stoix_line}, winmasters {matching_line}")
            unpaired_winmasters.remove(matching_line)
            print(f"✓ Matched: '{stoix_line}' with '{matching_line}'")
        else:
            unpaired_stoiximan.append(stoix_line)
            print(f"✗ No match found for: '{stoix_line}'")
    
    # Write initial paired file
    write_paired_file(output_file, paired, unpaired_stoiximan, unpaired_winmasters)
    print(f"Initial pairing completed. Results written to {output_file}")
    
    # Interactive feedback loop
    while True:
        feedback = input("\nΘέλεις να δώσεις feedback για τις αντιστοιχίες; (ναι/όχι): ").strip().lower()
        if feedback != 'ναι':
            break
        
        # Display current pairings
        print("\nΤρέχουσες αντιστοιχίες:")
        for i, pair in enumerate(paired):
            print(f"{i}: {pair}")
        
        print("\nΓραμμές stoiximan χωρίς αντιστοιχία:")
        for i, unpaired in enumerate(unpaired_stoiximan):
            print(f"s{i}: stoiximan {unpaired}")
        
        print("\nΓραμμές winmasters χωρίς αντιστοιχία:")
        for i, unpaired in enumerate(unpaired_winmasters):
            print(f"w{i}: winmasters {unpaired}")
        
        # Get user correction
        correction = input("\nΔώσε διόρθωση (π.χ. 's0-w1' για να ταιριάξεις stoiximan 0 με winmasters 1, 'remove N' για να αφαιρέσεις ζεύγος, ή 'skip' για παράλειψη): ").strip()
        if correction == 'skip':
            continue
        
        # Process user correction
        try:
            if correction.startswith('remove '):
                # Remove a pairing
                idx = int(correction.split()[1])
                if 0 <= idx < len(paired):
                    removed = paired.pop(idx)
                    parts = removed.split(', ')
                    stoix_part = parts[0].replace('stoiximan ', '')
                    win_part = parts[1].replace('winmasters ', '')
                    unpaired_stoiximan.append(stoix_part)
                    unpaired_winmasters.append(win_part)
                    print(f"Αφαιρέθηκε: {removed}")
                    write_paired_file(output_file, paired, unpaired_stoiximan, unpaired_winmasters)
                else:
                    print("Μη έγκυρος δείκτης!")
            elif '-' in correction:
                # Add a new pairing
                stoix_idx, win_idx = correction.split('-')
                s_idx = int(stoix_idx[1:]) if stoix_idx.startswith('s') else None
                w_idx = int(win_idx[1:]) if win_idx.startswith('w') else None
                
                if s_idx is not None and w_idx is not None and 0 <= s_idx < len(unpaired_stoiximan) and 0 <= w_idx < len(unpaired_winmasters):
                    new_pair = f"stoiximan {unpaired_stoiximan[s_idx]}, winmasters {unpaired_winmasters[w_idx]}"
                    paired.append(new_pair)
                    unpaired_stoiximan.pop(s_idx)
                    unpaired_winmasters.pop(w_idx)
                    print(f"Προστέθηκε: {new_pair}")
                    write_paired_file(output_file, paired, unpaired_stoiximan, unpaired_winmasters)
                else:
                    print("Μη έγκυροι δείκτες!")
            else:
                print("Λανθασμένη μορφή. Χρησιμοποιήστε 's0-w1' ή 'remove N'.")
        except Exception as e:
            print(f"Σφάλμα: {e}")

    print(f"\nΔιαδικασία ολοκληρώθηκε. Αποτελέσματα αποθηκεύτηκαν στο {output_file}")
    print(f"Συνολικά αντιστοιχίστηκαν {len(paired)} ζεύγη.")
    print(f"Έμειναν χωρίς αντιστοιχία {len(unpaired_stoiximan)} γραμμές stoiximan και {len(unpaired_winmasters)} γραμμές winmasters.")

if __name__ == "__main__":
    main()