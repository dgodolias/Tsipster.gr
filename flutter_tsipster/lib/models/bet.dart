class Bet {
  final int id;
  final String match;
  final String market;
  final String group;
  final String outcome;
  final double odds;
  bool isSelected;
  bool isNewlyAdded; // Keep this property for highlighting

  Bet({
    required this.id,
    required this.match,
    required this.market,
    this.group = '',
    required this.outcome,
    required this.odds,
    this.isSelected = false,
    this.isNewlyAdded = false,
  });

  factory Bet.fromJson(Map<String, dynamic> json) {
    // Print the incoming JSON for debugging
    print('Converting bet from JSON: $json');
    
    return Bet(
      id: json['id'] ?? 0,
      match: json['match'] ?? 'Unknown Match',
      market: json['market'] ?? 'Unknown Market',
      group: json['group'] ?? '',
      outcome: json['outcome'] ?? 'Unknown Outcome',
      odds: json['odds'] != null ? double.tryParse(json['odds'].toString()) ?? 1.0 : 1.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'match': match,
      'market': market,
      'group': group,
      'outcome': outcome,
      'odds': odds,
    };
  }
}
