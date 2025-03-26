import difflib
import json
import re
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

def ai_compare(line1, candidates, use_api=True):
    """Compare a betting option against candidates using API or fallback to rules-based matching"""
    if use_api:
        try:
            prompt = (
                "You are an expert in matching betting options from different bookmakers. "
                "Given the following betting option from Stoiximan bookmaker:\n"
                f"'{line1}'\n"
                "Find the most similar option from the following list of options from Winmasters bookmaker:\n"
                + "\n".join([f"- '{cand}'" for cand in candidates]) + "\n\n"
                "Important rules:\n"
                "1. In betting terminology, '1' means home team, 'X' means draw, and '2' means away team\n"
                "2. Return ONLY THE EXACT AND COMPLETE match from the candidates list\n"
                "3. Return 'None' if no good match exists\n"
                "Do not add any explanations, just return the exact matching string."
            )
            
            print(f"Comparing via API: '{line1}'")
            response = client.chat.completions.create(
                model="meta-llama/llama-3.2-3b-instruct:free",
                messages=[
                    {"role": "system", "content": "You are a betting market matching expert"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                stream=False
            )
            
            result = response.choices[0].message.content.strip().replace("'", "").replace("\"", "")
            print(f"API returned: '{result}'")
            
            # Verify the result is actually in the candidates list
            if result in candidates:
                return result
            else:
                # Try to find if the returned result is a substring of any candidate
                for candidate in candidates:
                    if result in candidate:
                        print(f"Found partial match: '{result}' in '{candidate}'")
                        return candidate
                
                # Fall back to rules-based matching
                print("API returned invalid match, falling back to rules-based matching")
                return rules_based_matching(line1, candidates)
                
        except Exception as e:
            print(f"API error: {e}")
            # Fall back to rules-based matching on error
            return rules_based_matching(line1, candidates)
    else:
        # Skip API and use rules-based matching directly
        return rules_based_matching(line1, candidates)

def rules_based_matching(line1, candidates):
    """Match betting options using predefined rules and string similarity"""
    print(f"Using rules-based matching for: '{line1}'")
    
    # Extract market type, value and odds
    parts = line1.split()
    market_type = " ".join(parts[:-2]) if len(parts) > 2 else ""
    odds = parts[-1] if len(parts) > 0 else ""
    
    
    # Try fuzzy string matching for everything else
    best_match = None
    best_ratio = 0
    for candidate in candidates:
        # Compare without the odds part
        line1_without_odds = " ".join(line1.split()[:-1])
        candidate_without_odds = " ".join(candidate.split()[:-1])
        
        ratio = difflib.SequenceMatcher(None, line1_without_odds, candidate_without_odds).ratio()
        if ratio > best_ratio and ratio > 0.7:  # 0.7 is the threshold
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