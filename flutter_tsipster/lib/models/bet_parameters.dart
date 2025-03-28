class BetParameters {
  final int numBets;
  final double minOdds;
  final double maxOdds;
  final bool uniqueMatchOnly;

  BetParameters({
    required this.numBets,
    required this.minOdds,
    required this.maxOdds,
    required this.uniqueMatchOnly,
  });

  factory BetParameters.defaultParams() {
    return BetParameters(
      numBets: 3,
      minOdds: 2.0,
      maxOdds: 15.0,
      uniqueMatchOnly: true,
    );
  }

  Map<String, dynamic> toJson() {
    // Match the Flask API's expected parameter names
    return {
      'numBets': numBets,
      'minOdds': minOdds,
      'maxOdds': maxOdds,
      'uniqueMatchOnly': uniqueMatchOnly,
    };
  }
}
