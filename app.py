from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS  # Import CORS
import json
import math
import threading
import importlib
import sys
from pathlib import Path
import random
from functools import reduce

# Make sure the current directory is included in the path
current_dir = str(Path(__file__).parent.absolute())
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app)
app.secret_key = 'tsipster_secret_key'  # Required for session management

# Import the bet_suggestor module
try:
    import bet_suggestor
    bs_imported = True
except ImportError as e:
    print(f"Could not import bet_suggestor module: {e}")
    bs_imported = False

# Sample data for demonstration purposes
sample_matches = [
    {"id": 1, "name": "Liverpool vs Manchester United", "markets": [
        {"name": "1X2", "outcomes": [{"name": "1", "odds": 1.90}, {"name": "X", "odds": 3.50}, {"name": "2", "odds": 4.20}]},
        {"name": "Over/Under 2.5", "outcomes": [{"name": "Over", "odds": 1.85}, {"name": "Under", "odds": 1.95}]}
    ]},
    {"id": 2, "name": "Barcelona vs Real Madrid", "markets": [
        {"name": "1X2", "outcomes": [{"name": "1", "odds": 2.10}, {"name": "X", "odds": 3.30}, {"name": "2", "odds": 3.40}]},
        {"name": "Over/Under 2.5", "outcomes": [{"name": "Over", "odds": 1.75}, {"name": "Under", "odds": 2.05}]}
    ]},
    {"id": 3, "name": "Bayern Munich vs Dortmund", "markets": [
        {"name": "1X2", "outcomes": [{"name": "1", "odds": 1.60}, {"name": "X", "odds": 3.80}, {"name": "2", "odds": 5.50}]},
        {"name": "Over/Under 2.5", "outcomes": [{"name": "Over", "odds": 1.55}, {"name": "Under", "odds": 2.45}]}
    ]},
]

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/generate-bets', methods=['POST'])
def generate_bets_api():
    try:
        data = request.json
        print(f"Received request: {data}")  # Debug logging
        
        # Update parameter names to match Flutter app
        requested_bets = int(data.get('numBets', 3))
        min_odds = float(data.get('minOdds', 2.0))
        max_odds = float(data.get('maxOdds', 15.0))
        unique_match_only = data.get('uniqueMatchOnly', True)
        
        if not bs_imported:
            # Use sample data if bet_suggestor module is not available
            return generate_sample_bets(requested_bets, min_odds, max_odds, unique_match_only)
        
        # Get reference to the bet suggestor module
        bs = bet_suggestor
        
        # Get the maximum number of unique matches available
        max_matches = bs.get_max_unique_matches()
        
        # Limit number of bets to available unique matches if unique match only is enabled
        if unique_match_only and requested_bets > max_matches:
            num_bets = max_matches
            print(f"Requested {requested_bets} bets but limited to {max_matches} available unique matches")
        else:
            num_bets = requested_bets
        
        print(f"Processing with: num_bets={num_bets}, min_odds={min_odds}, max_odds={max_odds}")
        
        # Get the available bets from the module
        bets = bs.bets
        market_types = bs.market_types
        model = bs.model
        
        # Our betting slip
        selected_bets = []
        current_total_odds = 1.0
        used_matches = set()
        
        # Select bets with dynamic odds filtering
        for k in range(num_bets):
            low, high = bs.get_next_odds_range(current_total_odds, k, num_bets, min_odds, max_odds)
            
            # Filter bets within the current odds range
            if unique_match_only:
                available_bets = [bet for bet in bets if bet['match'] not in used_matches and low <= bet['odds'] <= high]
            else:
                available_bets = [bet for bet in bets if low <= bet['odds'] <= high]
            
            if not available_bets:
                if unique_match_only:
                    available_bets = [bet for bet in bets if bet['match'] not in used_matches]
                else:
                    available_bets = bets
                
                if not available_bets:
                    # If we're trying for unique matches but can't find any, allow duplicates
                    if unique_match_only:
                        unique_match_only = False
                        available_bets = [bet for bet in bets if low <= bet['odds'] <= high]
                        if not available_bets:
                            available_bets = bets  # Use all bets if none in range
                    
                    if not available_bets:
                        break
            
            # Score available bets
            for bet in available_bets:
                features = bs.get_bet_features(bet, market_types)
                with bs.torch.no_grad():
                    nn_score = model(features).item()
                base_score = bet['preference_score'] * nn_score
                if bs.random.random() < 0.2:
                    base_score *= bs.random.uniform(0.8, 1.2)
                bet['total_score'] = base_score
            
            # Select the highest-scored bet
            best_bet = max(available_bets, key=lambda bet: bet['total_score'])
            
            # Store all relevant bet information
            bet_info = {
                'id': len(selected_bets),
                'match': best_bet['match'],
                'market': best_bet['market'],
                'group': best_bet['group'] if 'group' in best_bet else '',
                'outcome': best_bet['outcome'],
                'odds': best_bet['odds']
            }
            selected_bets.append(bet_info)
            
            if unique_match_only:
                used_matches.add(best_bet['match'])
            current_total_odds *= best_bet['odds']
        
        # Store in session for later access
        session['selected_bets'] = selected_bets
        session['current_total_odds'] = current_total_odds
        
        # Format response for API - ensure consistent format
        formatted_bets = []
        for bet in selected_bets:
            formatted_bets.append({
                "id": bet["id"],
                "match": bet["match"],
                "market": bet["market"],
                "group": bet["group"] if "group" in bet else "",
                "outcome": bet["outcome"],
                "odds": bet["odds"]
            })
        
        result = {
            "bets": formatted_bets,
            "totalOdds": round(current_total_odds, 2),
            "limitedBets": num_bets != requested_bets,
            "maxAvailableMatches": max_matches
        }
        print(f"Returning result: {result}")  # Debug logging
        return jsonify(result)
        
    except Exception as e:
        print(f"Error generating bets: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_sample_bets(num_bets, min_odds, max_odds, unique_match_only):
    """Generate sample bets when bet_suggestor is not available"""
    generated_bets = []
    used_match_ids = set()
    
    # Get maximum unique matches available from sample data
    max_matches = len(sample_matches)
    
    # Limit number of bets to available unique matches if unique match only is enabled
    if unique_match_only and num_bets > max_matches:
        actual_num_bets = max_matches
        print(f"Requested {num_bets} bets but limited to {max_matches} available unique matches")
    else:
        actual_num_bets = num_bets
    
    for _ in range(min(actual_num_bets, 10)):
        eligible_matches = [m for m in sample_matches if (unique_match_only and m["id"] not in used_match_ids) or not unique_match_only]
        if not eligible_matches:
            break
            
        match = random.choice(eligible_matches)
        market = random.choice(match["markets"])
        outcome = random.choice(market["outcomes"])
        
        bet = {
            "id": len(generated_bets),
            "match": match["name"],
            "market": market["name"],
            "group": "",
            "outcome": outcome["name"],
            "odds": outcome["odds"]
        }
        
        generated_bets.append(bet)
        used_match_ids.add(match["id"])
    
    # Calculate total odds
    total_odds = round(reduce(lambda x, y: x * y, [bet["odds"] for bet in generated_bets], 1), 2)
    
    return jsonify({
        "bets": generated_bets,
        "totalOdds": total_odds,
        "limitedBets": actual_num_bets != num_bets,
        "maxAvailableMatches": max_matches
    })

@app.route('/accept_bets', methods=['POST'])
def accept_bets():
    """Accept all bets and train the model"""
    try:
        selected_bets = session.get('selected_bets', [])
        
        if not selected_bets:
            return jsonify({'message': 'No bets to accept'}), 400
            
        # Train the neural network with positive examples
        if bs_imported:
            bs = bet_suggestor
            market_types = bs.market_types
            model = bs.model
            optimizer = bs.optimizer
            criterion = bs.criterion
            
            training_data = []
            
            for bet in selected_bets:
                # Recreate the original bet format for feature extraction
                original_format_bet = {
                    'match': bet['match'],
                    'market': bet['market'],
                    'group': bet['group'],
                    'outcome': bet['outcome'],
                    'odds': bet['odds']
                }
                features = bs.get_bet_features(original_format_bet, market_types)
                training_data.append((features, bs.torch.tensor([1.0], dtype=bs.torch.float32)))
            
            model.train()
            for features, label in training_data:
                optimizer.zero_grad()
                output = model(features)
                loss = criterion(output, label)
                loss.backward()
                optimizer.step()
            model.eval()
            bs.torch.save(model.state_dict(), 'nn_model.pth')
        
        return jsonify({'message': 'All bets accepted and neural network updated!'})
    
    except Exception as e:
        print(f"Error accepting bets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/reject_bets', methods=['POST'])
def reject_bets():
    """Reject selected bets and train the model"""
    try:
        data = request.json
        reject_indices = data.get('reject_indices', [])
        get_replacements = data.get('get_replacements', True)  # Default to true
        
        selected_bets = session.get('selected_bets', [])
        current_total_odds = session.get('current_total_odds', 1.0)
        
        if not selected_bets:
            return jsonify({'message': 'No bets to reject'}), 400
            
        # Train the neural network with negative examples
        if bs_imported:
            bs = bet_suggestor
            market_types = bs.market_types
            model = bs.model
            optimizer = bs.optimizer
            criterion = bs.criterion
            
            training_data = []
            
            for idx in reject_indices:
                if 0 <= idx < len(selected_bets):
                    bet = selected_bets[idx]
                    # Recreate the original bet format for feature extraction
                    original_format_bet = {
                        'match': bet['match'],
                        'market': bet['market'],
                        'group': bet['group'],
                        'outcome': bet['outcome'],
                        'odds': bet['odds']
                    }
                    features = bs.get_bet_features(original_format_bet, market_types)
                    training_data.append((features, bs.torch.tensor([0.0], dtype=bs.torch.float32)))
            
            model.train()
            for features, label in training_data:
                optimizer.zero_grad()
                output = model(features)
                loss = criterion(output, label)
                loss.backward()
                optimizer.step()
            model.eval()
            bs.torch.save(model.state_dict(), 'nn_model.pth')
        
        # Remove rejected bets
        updated_bets = [bet for i, bet in enumerate(selected_bets) if i not in reject_indices]
        
        # Recalculate total odds
        if updated_bets:
            new_total_odds = math.prod(bet['odds'] for bet in updated_bets)
        else:
            new_total_odds = 0
            
        # Update session
        session['selected_bets'] = updated_bets
        session['current_total_odds'] = new_total_odds
        
        return jsonify({
            'message': 'Bets rejected and neural network updated!',
            'updated_bets': updated_bets,
            'total_odds': round(new_total_odds, 2),
            'replacements_needed': len(reject_indices) if get_replacements else 0
        })
    
    except Exception as e:
        print(f"Error rejecting bets: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_replacement_bets', methods=['POST'])
def get_replacement_bets():
    """Get replacement bets for rejected ones"""
    try:
        data = request.json
        num_needed = int(data.get('num_needed', 1))
        min_odds = float(data.get('min_odds', 2.0))
        max_odds = float(data.get('max_odds', 15.0))
        unique_match_only = data.get('unique_match_only', True)
        avoid_matches = data.get('avoid_matches', [])  # NEW: matches to avoid
        
        selected_bets = session.get('selected_bets', [])
        current_total_odds = session.get('current_total_odds', 1.0)
        
        if num_needed <= 0:
            return jsonify({'message': 'No replacement bets needed'}), 400
            
        if not bs_imported:
            # Use sample data for replacements if model not available
            return generate_replacement_sample_bets(num_needed, selected_bets, unique_match_only, avoid_matches)
        
        bs = bet_suggestor
        bets = bs.bets
        market_types = bs.market_types
        model = bs.model
        
        # Get already used matches to avoid them when unique_match_only is True
        used_matches = set(bet['match'] for bet in selected_bets)
        # Add rejected matches to the avoid list
        used_matches.update(avoid_matches)
        
        new_bets = []
        
        # For logging purposes
        print(f"Getting {num_needed} replacements. Current bets: {len(selected_bets)}")
        print(f"Avoiding matches: {avoid_matches}")
        
        for k in range(num_needed):
            # Calculate appropriate odds range for this replacement
            total_target_bets = len(selected_bets) + num_needed
            current_position = len(selected_bets) + k
            low, high = bs.get_next_odds_range(current_total_odds, current_position, total_target_bets, min_odds, max_odds)
            
            print(f"Replacement {k+1}: Odds range {low} to {high}, current total: {current_total_odds}")
            
            # Filter bets - IMPORTANT: Avoid using already rejected matches
            if unique_match_only:
                available_bets = [bet for bet in bets if bet['match'] not in used_matches and low <= bet['odds'] <= high]
            else:
                # Still avoid the explicitly rejected matches even if not requiring unique matches
                available_bets = [bet for bet in bets if bet['match'] not in avoid_matches and low <= bet['odds'] <= high]
            
            if not available_bets:
                # Relaxed filtering strategy if no bets available in the initial range
                if unique_match_only:
                    available_bets = [bet for bet in bets if bet['match'] not in used_matches]
                    if not available_bets:
                        print("No unique matches left - allowing duplicates for this replacement")
                        unique_match_only = False
                        available_bets = [bet for bet in bets if bet['match'] not in avoid_matches and low <= bet['odds'] <= high]
                        if not available_bets:
                            available_bets = [bet for bet in bets if bet['match'] not in avoid_matches]
                else:
                    available_bets = [bet for bet in bets if bet['match'] not in avoid_matches]
            
            if not available_bets:
                print("No available bets found for replacement")
                break
            
            # Score and select
            for bet in available_bets:
                features = bs.get_bet_features(bet, market_types)
                with bs.torch.no_grad():
                    nn_score = model(features).item()
                base_score = bet['preference_score'] * nn_score
                if bs.random.random() < 0.2:
                    base_score *= bs.random.uniform(0.8, 1.2)
                bet['total_score'] = base_score
            
            best_bet = max(available_bets, key=lambda bet: bet['total_score'])
            
            # Create bet info
            bet_info = {
                'id': len(selected_bets) + len(new_bets),  # Assign appropriate ID
                'match': best_bet['match'],
                'market': best_bet['market'],
                'group': best_bet['group'] if 'group' in best_bet else '',
                'outcome': best_bet['outcome'],
                'odds': best_bet['odds']
            }
            new_bets.append(bet_info)
            
            if unique_match_only:
                used_matches.add(best_bet['match'])
            current_total_odds *= best_bet['odds']
        
        # Update session with both existing bets and new replacements
        updated_bets = selected_bets + new_bets
        session['selected_bets'] = updated_bets
        session['current_total_odds'] = current_total_odds
        
        print(f"Added {len(new_bets)} replacement bets. New total: {len(updated_bets)}")
        
        return jsonify({
            'new_bets': new_bets,
            'all_bets': updated_bets,
            'total_odds': round(current_total_odds, 2)
        })
        
    except Exception as e:
        print(f"Error getting replacement bets: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_replacement_sample_bets(num_needed, existing_bets, unique_match_only, avoid_matches=[]):
    """Generate sample replacement bets when bet_suggestor is not available"""
    generated_bets = []
    used_match_ids = set()
    
    # Track already used matches from existing bets
    for bet in existing_bets:
        match_name = bet['match']
        for sample_match in sample_matches:
            if sample_match['name'] == match_name:
                used_match_ids.add(sample_match['id'])
    
    # Also track matches to avoid (from rejected bets)
    avoid_match_ids = set()
    for avoid_match in avoid_matches:
        for sample_match in sample_matches:
            if sample_match['name'] == avoid_match:
                avoid_match_ids.add(sample_match['id'])
    
    current_total_odds = reduce(lambda x, y: x * y, [bet['odds'] for bet in existing_bets], 1.0)
    
    for _ in range(min(num_needed, 10)):
        # Filter out both used and avoided matches
        eligible_matches = [
            m for m in sample_matches 
            if (unique_match_only and m["id"] not in used_match_ids and m["id"] not in avoid_match_ids) 
            or (not unique_match_only and m["id"] not in avoid_match_ids)
        ]
        
        if not eligible_matches:
            break
            
        match = random.choice(eligible_matches)
        market = random.choice(match["markets"])
        outcome = random.choice(market["outcomes"])
        
        bet = {
            "id": len(existing_bets) + len(generated_bets),
            "match": match["name"],
            "market": market["name"],
            "group": "",
            "outcome": outcome["name"],
            "odds": outcome["odds"]
        }
        
        generated_bets.append(bet)
        used_match_ids.add(match["id"])
        current_total_odds *= outcome["odds"]
    
    # Create final bet list with existing and new bets
    all_bets = existing_bets + generated_bets
    
    return jsonify({
        "new_bets": generated_bets,
        "all_bets": all_bets,
        "total_odds": round(current_total_odds, 2)
    })

@app.route('/get_same_match_alternatives', methods=['POST'])
def get_same_match_alternatives():
    """Get alternative bets for the same matches"""
    try:
        data = request.json
        target_matches = data.get('target_matches', [])
        num_needed = int(data.get('num_needed', 1))
        current_odds = float(data.get('current_odds', 1.0))
        min_total_odds = float(data.get('min_total_odds', 2.0))
        max_total_odds = float(data.get('max_total_odds', 15.0))
        rejected_indices = data.get('rejected_bet_indices', [])
        
        # Get current bets from session
        selected_bets = session.get('selected_bets', [])
        
        # Keep track of which bets were kept (not rejected)
        kept_bets = [bet for i, bet in enumerate(selected_bets) if i not in rejected_indices]
        
        # Identify which matches we need alternatives for
        rejected_bets = [bet for i, bet in enumerate(selected_bets) if i in rejected_indices]
        
        if not target_matches or num_needed <= 0:
            return jsonify({'message': 'No alternatives needed'}), 400
        
        print(f"Finding alternatives for matches: {target_matches}")
        print(f"Current odds from kept bets: {current_odds}")
        
        if not bs_imported:
            return generate_alternative_sample_bets(
                target_matches, kept_bets, num_needed, current_odds, min_total_odds, max_total_odds)
        
        bs = bet_suggestor
        bets = bs.bets
        market_types = bs.market_types
        model = bs.model
        
        new_bets = []
        
        # We'll process one match at a time to ensure we get exactly one bet per rejected match
        for match_name in target_matches:
            # Filter bets to only include those from this specific match
            match_bets = [bet for bet in bets if bet['match'] == match_name]
            
            print(f"Found {len(match_bets)} potential alternatives for match: {match_name}")
            
            if not match_bets:
                print(f"No alternatives found for match: {match_name}")
                continue
                
            # Calculate ideal odds for this bet to keep the total within range
            # This approximates what we need for this match to get total odds in range
            ideal_odds = 1.0
            if min_total_odds > current_odds:
                ideal_odds = min_total_odds / current_odds
            
            # Score all available bets for this match
            scored_bets = []
            for bet in match_bets:
                # Don't use the exact same bet we rejected
                skip = False
                for rejected in rejected_bets:
                    if (bet['match'] == rejected['match'] and 
                        bet['market'] == rejected['market'] and 
                        bet['outcome'] == rejected['outcome']):
                        skip = True
                        break
                
                if skip:
                    continue
                
                features = bs.get_bet_features(bet, market_types)
                with bs.torch.no_grad():
                    nn_score = model(features).item()
                base_score = bet['preference_score'] * nn_score
                
                # Adjust score based on how close odds are to ideal
                odds_factor = 1.0 - abs(bet['odds'] - ideal_odds) / 10.0  # Prioritize odds close to ideal
                bet['total_score'] = base_score * odds_factor
                
                scored_bets.append(bet)
            
            if not scored_bets:
                print(f"No valid alternatives for match: {match_name}")
                continue
                
            # Sort by score and take the best option for this match
            best_bet = max(scored_bets, key=lambda bet: bet['total_score'])
            
            # Create bet info
            bet_info = {
                'id': len(kept_bets) + len(new_bets),
                'match': best_bet['match'],
                'market': best_bet['market'],
                'group': best_bet['group'] if 'group' in best_bet else '',
                'outcome': best_bet['outcome'],
                'odds': best_bet['odds']
            }
            new_bets.append(bet_info)
        
        # Calculate new total odds
        total_odds = current_odds
        for bet in new_bets:
            total_odds *= bet['odds']
        
        # Update session with both kept and new bets
        updated_bets = kept_bets + new_bets
        session['selected_bets'] = updated_bets
        session['current_total_odds'] = total_odds
        
        print(f"Returning {len(new_bets)} alternatives with new total odds: {total_odds}")
        
        return jsonify({
            'new_bets': new_bets,
            'all_bets': updated_bets,
            'total_odds': round(total_odds, 2)
        })
    
    except Exception as e:
        print(f"Error getting alternatives: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_alternative_sample_bets(target_matches, kept_bets, num_needed, current_odds, min_total_odds, max_total_odds):
    """Generate alternative sample bets for the specified matches"""
    generated_bets = []
    
    # Desired odds range for the new bets combined
    min_combined_new_odds = min_total_odds / current_odds
    max_combined_new_odds = max_total_odds / current_odds
    
    # For each target match, find samples that match
    for match_name in target_matches:
        if len(generated_bets) >= num_needed:
            break
            
        # Find the corresponding sample match
        sample_match = None
        for match in sample_matches:
            if match["name"] == match_name:
                sample_match = match
                break
        
        if not sample_match:
            # Try to find a close match if exact match not found
            for match in sample_matches:
                if len(generated_bets) < num_needed:
                    sample_match = match
                    break
        
        if sample_match:
            # Randomly choose an alternative market and outcome
            market = random.choice(sample_match["markets"])
            outcome = random.choice(market["outcomes"])
            
            # Choose an outcome with odds that will fit the total odds range if possible
            target_odds = (min_combined_new_odds + max_combined_new_odds) / 2
            if num_needed > 1:
                target_odds = target_odds ** (1 / num_needed)  # Distribute evenly
                
            # Find closest outcome to target odds
            closest_outcome = min(market["outcomes"], 
                                 key=lambda o: abs(o["odds"] - target_odds))
            
            bet = {
                "id": len(kept_bets) + len(generated_bets),
                "match": sample_match["name"],
                "market": market["name"],
                "group": "",
                "outcome": closest_outcome["name"],
                "odds": closest_outcome["odds"]
            }
            
            generated_bets.append(bet)
    
    # Calculate total odds
    total_odds = current_odds
    for bet in generated_bets:
        total_odds *= bet["odds"]
    
    # Combine with kept bets
    all_bets = kept_bets + generated_bets
    
    return jsonify({
        "new_bets": generated_bets,
        "all_bets": all_bets,
        "total_odds": round(total_odds, 2)
    })

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('images/favicon.png')

if __name__ == "__main__":
    # 0.0.0.0 makes the server accessible from other devices on the network
    # Use 127.0.0.1 for local access only
    app.run(debug=True, host='127.0.0.1', port=5000)
