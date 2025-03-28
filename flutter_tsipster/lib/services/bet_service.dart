import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/bet.dart';
import '../models/bet_parameters.dart';
import 'sample_data_service.dart';

class BetService extends ChangeNotifier {
  List<Bet> _currentBets = [];
  List<String> _statusLog = ['Welcome to Tsipster! Set parameters and generate bets to start.'];
  double _totalOdds = 0;
  bool _isLoading = false;
  String _errorMessage = '';
  int _maxAvailableMatches = 0; // Store max available matches
  BetParameters _lastParameters = BetParameters.defaultParams(); // Remember last parameters

  // Getters
  List<Bet> get currentBets => _currentBets;
  List<String> get statusLog => _statusLog;
  double get totalOdds => _totalOdds;
  bool get isLoading => _isLoading;
  String get errorMessage => _errorMessage;
  int get maxAvailableMatches => _maxAvailableMatches;

  // For offline mode or testing
  final SampleDataService _sampleDataService = SampleDataService();

  // Base URL for API calls - Fix this to ensure proper connection
  // Note: When running on an Android emulator and connecting to Flask on the same computer,
  // use 10.0.2.2 instead of localhost/127.0.0.1
  final String baseUrl = kIsWeb ? 'http://127.0.0.1:5000' : 'http://10.0.2.2:5000';
  
  // Add log message
  void addLogMessage(String message) {
    _statusLog.add('${DateTime.now().toLocal().toString().split(' ')[1].substring(0, 8)}: $message');
    notifyListeners();
  }

  // Generate bets
  Future<void> generateBets(BetParameters params) async {
    _isLoading = true;
    _errorMessage = '';
    _lastParameters = params; // Save parameters for later use
    notifyListeners();
    
    addLogMessage('Generating bets with numBets=${params.numBets}, minOdds=${params.minOdds}, maxOdds=${params.maxOdds}');
    
    try {
      // Print request details for debugging
      print('Sending request to $baseUrl/api/generate-bets');
      print('Request body: ${jsonEncode(params.toJson())}');
      
      final response = await http.post(
        Uri.parse('$baseUrl/api/generate-bets'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(params.toJson()),
      ).timeout(const Duration(seconds: 20)); // Increased timeout
      
      print('Response status: ${response.statusCode}');
      print('Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Verify the response format
        if (data['bets'] != null && data['totalOdds'] != null) {
          _currentBets = (data['bets'] as List)
              .map((bet) => Bet.fromJson(bet))
              .toList();
          _totalOdds = data['totalOdds'].toDouble();
          
          // Update maximum available matches if provided
          if (data['maxAvailableMatches'] != null) {
            _maxAvailableMatches = data['maxAvailableMatches'];
          }
          
          // Show message if bets were limited due to match availability
          if (data['limitedBets'] == true) {
            addLogMessage('Note: Limited to $_maxAvailableMatches available unique matches');
          }
          
          addLogMessage('Generated ${_currentBets.length} bets with total odds of $_totalOdds');
        } else {
          throw Exception('Invalid response format from server');
        }
      } else {
        throw Exception('Server returned ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      // In case of network error, use sample data
      _errorMessage = 'Network error: $e. Using sample data.';
      addLogMessage(_errorMessage);
      await _useSampleData(params);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Use sample data when offline
  Future<void> _useSampleData(BetParameters params) async {
    final sampleData = await _sampleDataService.getSampleBets(
      params.numBets,
      params.uniqueMatchOnly,
    );
    
    _currentBets = sampleData.bets;
    _totalOdds = sampleData.totalOdds;
    _maxAvailableMatches = sampleData.maxUniqueMatches;
  }
  
  // Accept all bets
  Future<void> acceptAllBets() async {
    if (_currentBets.isEmpty) {
      addLogMessage('No bets to accept');
      return;
    }
    
    _isLoading = true;
    addLogMessage('Accepting all bets...');
    notifyListeners();
    
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/accept_bets'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        addLogMessage(data['message'] ?? 'All bets accepted!');
      } else {
        _errorMessage = 'Server error when accepting bets: ${response.statusCode}';
        addLogMessage(_errorMessage);
      }
    } catch (e) {
      _errorMessage = 'Error accepting bets: $e';
      addLogMessage(_errorMessage);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Reject selected bets and automatically get replacements
  Future<void> rejectSelectedBets() async {
    final selectedIndices = _currentBets
        .asMap()
        .entries
        .where((entry) => entry.value.isSelected)
        .map((entry) => entry.key)
        .toList();
        
    if (selectedIndices.isEmpty) {
      addLogMessage('No bets selected for rejection');
      return;
    }
    
    _isLoading = true;
    addLogMessage('Rejecting ${selectedIndices.length} bet(s) and finding alternatives...');
    notifyListeners();
    
    try {
      // Get the bets that are being rejected
      final rejectedBets = selectedIndices.map((i) => _currentBets[i]).toList();
      
      // Get matches for which we need alternatives
      final rejectedMatches = rejectedBets.map((bet) => bet.match).toList();
      
      // Make a copy of the current bets before any changes
      final List<Bet> currentBetsCopy = List.from(_currentBets);
      
      // Calculate current total odds from all bets
      final double currentTotalOdds = _totalOdds;
      
      // Calculate odds from just the rejected bets - we'll need to divide these out
      final double rejectedOdds = rejectedBets.fold(
        1.0, (prev, bet) => prev * bet.odds);
      
      // The remaining odds after removing the rejected bets
      final double remainingOdds = currentTotalOdds / rejectedOdds;
      
      // Clear selection on all bets
      for (final bet in _currentBets) {
        bet.isSelected = false;
      }
      
      addLogMessage('Finding alternatives for the same matches...');
      
      // Get replacements for rejected bets
      final response = await http.post(
        Uri.parse('$baseUrl/get_same_match_alternatives'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'target_matches': rejectedMatches,
          'num_needed': selectedIndices.length,  // Get exactly as many as we rejected
          'current_odds': remainingOdds,         // The odds without the rejected bets
          'min_total_odds': _lastParameters.minOdds,
          'max_total_odds': _lastParameters.maxOdds,
          'rejected_bet_indices': selectedIndices,
        }),
      ).timeout(const Duration(seconds: 15));
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        if (data['new_bets'] != null && data['new_bets'].isNotEmpty) {
          // Convert the new bets to Bet objects
          final List<Bet> newBets = (data['new_bets'] as List)
              .map((bet) => Bet.fromJson(bet))
              .toList();
          
          // Update total odds
          _totalOdds = data['total_odds'].toDouble();
          
          // Create a new merged bet list:
          // 1. Keep all bets that weren't rejected
          // 2. Add the new replacement bets
          final List<Bet> updatedBets = [];
          
          // Add non-rejected bets
          for (int i = 0; i < currentBetsCopy.length; i++) {
            if (!selectedIndices.contains(i)) {
              updatedBets.add(currentBetsCopy[i]);
            }
          }
          
          // Add the replacement bets
          updatedBets.addAll(newBets);
          
          // Mark the new bets as newly added for visual indication
          for (final bet in newBets) {
            bet.isNewlyAdded = true;
          }
          
          // Update the betting slip with the merged list
          _currentBets = updatedBets;
          
          addLogMessage('Found ${newBets.length} alternative bet(s) for the same matches');
          
          // Clear the "newly added" flag after 3 seconds
          Future.delayed(const Duration(seconds: 3), () {
            for (final bet in _currentBets) {
              bet.isNewlyAdded = false;
            }
            notifyListeners();
          });
        } else {
          // If no alternatives found, just keep the non-rejected bets
          _currentBets = currentBetsCopy
              .asMap()
              .entries
              .where((entry) => !selectedIndices.contains(entry.key))
              .map((entry) => entry.value)
              .toList();
              
          // Recalculate total odds
          _totalOdds = _currentBets.fold(1.0, (prev, bet) => prev * bet.odds);
          
          addLogMessage('No alternatives found for the rejected matches');
        }
      } else {
        throw Exception('Server returned ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      _errorMessage = 'Error: $e';
      addLogMessage(_errorMessage);
      
      // Fall back to local handling - just remove the selected bets
      _removeSelectedBetsLocally(selectedIndices);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  // Local fallback for generating replacement bets
  Future<void> _getFallbackReplacementBets(int numNeeded) async {
    if (numNeeded <= 0) return;
    
    addLogMessage('Getting local fallback for $numNeeded replacement bets');
    
    try {
      // Create a parameter object with additional bets
      final replacementParams = BetParameters(
        numBets: _lastParameters.numBets, // Keep same total count
        minOdds: _lastParameters.minOdds,
        maxOdds: _lastParameters.maxOdds,
        uniqueMatchOnly: _lastParameters.uniqueMatchOnly,
      );
      
      // Generate new bets using the last parameters
      await generateBets(replacementParams);
    } catch (e) {
      addLogMessage('Error getting fallback replacements: $e');
    }
  }
  
  // Local fallback for removing bets when server is unavailable
  void _removeSelectedBetsLocally(List<int> indices) {
    // Sort in descending order to avoid index shifting
    indices.sort((a, b) => b.compareTo(a));
    
    for (final index in indices) {
      if (index >= 0 && index < _currentBets.length) {
        _currentBets.removeAt(index);
      }
    }
    
    // Recalculate total odds
    _totalOdds = _currentBets.fold(1.0, (prev, bet) => prev * bet.odds);
  }
  
  // Toggle selection of a bet
  void toggleBetSelection(int index) {
    if (index >= 0 && index < _currentBets.length) {
      _currentBets[index].isSelected = !_currentBets[index].isSelected;
      notifyListeners();
    }
  }
  
  // Toggle selection of all bets
  void toggleAllBets(bool selected) {
    for (final bet in _currentBets) {
      bet.isSelected = selected;
    }
    notifyListeners();
  }
  
  // Clear all bets
  void clearBets() {
    _currentBets = [];
    _totalOdds = 0;
    notifyListeners();
  }
}
