import 'dart:math';
import '../models/bet.dart';

class SampleBetResult {
  final List<Bet> bets;
  final double totalOdds;
  final int maxUniqueMatches;
  
  SampleBetResult({
    required this.bets, 
    required this.totalOdds,
    this.maxUniqueMatches = 0,
  });
}

class SampleDataService {
  final List<Map<String, dynamic>> _sampleMatches = [
    {
      "id": 1,
      "name": "Liverpool vs Manchester United",
      "markets": [
        {
          "name": "1X2",
          "outcomes": [
            {"name": "1", "odds": 1.90},
            {"name": "X", "odds": 3.50},
            {"name": "2", "odds": 4.20}
          ]
        },
        {
          "name": "Over/Under 2.5",
          "outcomes": [
            {"name": "Over", "odds": 1.85},
            {"name": "Under", "odds": 1.95}
          ]
        }
      ]
    },
    {
      "id": 2,
      "name": "Barcelona vs Real Madrid",
      "markets": [
        {
          "name": "1X2",
          "outcomes": [
            {"name": "1", "odds": 2.10},
            {"name": "X", "odds": 3.30},
            {"name": "2", "odds": 3.40}
          ]
        },
        {
          "name": "Over/Under 2.5",
          "outcomes": [
            {"name": "Over", "odds": 1.75},
            {"name": "Under", "odds": 2.05}
          ]
        }
      ]
    },
    {
      "id": 3,
      "name": "Bayern Munich vs Dortmund",
      "markets": [
        {
          "name": "1X2",
          "outcomes": [
            {"name": "1", "odds": 1.60},
            {"name": "X", "odds": 3.80},
            {"name": "2", "odds": 5.50}
          ]
        },
        {
          "name": "Over/Under 2.5",
          "outcomes": [
            {"name": "Over", "odds": 1.55},
            {"name": "Under", "odds": 2.45}
          ]
        }
      ]
    },
  ];

  Future<SampleBetResult> getSampleBets(int numBets, bool uniqueMatchOnly) async {
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 500));
    
    final Random random = Random();
    final List<Bet> generatedBets = [];
    final Set<int> usedMatchIds = {};
    
    // Get maximum unique matches available
    final int maxUniqueMatches = _sampleMatches.length;
    
    // Limit number of bets to available unique matches if unique match only is enabled
    int actualNumBets = numBets;
    if (uniqueMatchOnly && numBets > maxUniqueMatches) {
      actualNumBets = maxUniqueMatches;
    }
    
    for (int i = 0; i < min(actualNumBets, 10); i++) {
      final eligibleMatches = _sampleMatches.where((m) {
        if (uniqueMatchOnly) {
          return !usedMatchIds.contains(m["id"]);
        }
        return true;
      }).toList();
      
      if (eligibleMatches.isEmpty) break;
      
      final match = eligibleMatches[random.nextInt(eligibleMatches.length)];
      final markets = match["markets"] as List;
      final market = markets[random.nextInt(markets.length)];
      final outcomes = market["outcomes"] as List;
      final outcome = outcomes[random.nextInt(outcomes.length)];
      
      generatedBets.add(Bet(
        id: i,
        match: match["name"],
        market: market["name"],
        group: "", // Sample data doesn't have group
        outcome: outcome["name"],
        odds: outcome["odds"],
      ));
      
      usedMatchIds.add(match["id"] as int);
    }
    
    // Calculate total odds
    final totalOdds = generatedBets.fold(1.0, (prev, bet) => prev * bet.odds);
    
    return SampleBetResult(
      bets: generatedBets,
      totalOdds: totalOdds,
      maxUniqueMatches: maxUniqueMatches,
    );
  }
}
