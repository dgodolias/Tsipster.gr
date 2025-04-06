import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/bet_service.dart';

class BetTable extends StatelessWidget {
  const BetTable({super.key});

  @override
  Widget build(BuildContext context) {
    final betService = Provider.of<BetService>(context);
    final bets = betService.currentBets;
    
    if (bets.isEmpty) {
      return const Padding(
        padding: EdgeInsets.all(16.0),
        child: Center(
          child: Text(
            'No bets generated yet',
            style: TextStyle(fontSize: 16, fontStyle: FontStyle.italic),
          ),
        ),
      );
    }
    
    return Column(
      children: [
        // Table header with fixed position
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8.0),
          child: Row(
            children: [
              SizedBox(
                width: 40,
                child: Checkbox(
                  value: bets.every((bet) => bet.isSelected),
                  tristate: bets.any((bet) => bet.isSelected) && !bets.every((bet) => bet.isSelected),
                  onChanged: (value) {
                    betService.toggleAllBets(value ?? false);
                  },
                ),
              ),
              const SizedBox(width: 8),
              const Expanded(
                flex: 3,
                child: Text(
                  'Match',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              const Expanded(
                flex: 2,
                child: Text(
                  'Market',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              const Expanded(
                flex: 2,
                child: Text(
                  'Outcome',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(
                width: 60,
                child: Text(
                  'Odds',
                  style: TextStyle(fontWeight: FontWeight.bold),
                  textAlign: TextAlign.right,
                ),
              ),
            ],
          ),
        ),
        
        const Divider(),
        
        // Use ListView.builder instead of ListView.separated for better performance
        // Constrain the height to avoid layout issues
        ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.of(context).size.height * 0.5,
            minHeight: 100,
          ),
          child: ListView.builder(
            shrinkWrap: true,
            physics: const AlwaysScrollableScrollPhysics(),
            itemCount: bets.length,
            itemBuilder: (context, index) {
              final bet = bets[index];
              return Column(
                children: [
                  Material(
                    color: bet.isNewlyAdded 
                      ? Colors.green.withOpacity(0.1)  
                      : (bet.isSelected ? Colors.blue.withOpacity(0.1) : null),
                    child: InkWell(
                      onTap: () {
                        betService.toggleBetSelection(index);
                      },
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 8.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                SizedBox(
                                  width: 40,
                                  child: Checkbox(
                                    value: bet.isSelected,
                                    onChanged: (value) {
                                      betService.toggleBetSelection(index);
                                    },
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  flex: 3,
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          bet.match,
                                          style: TextStyle(
                                            fontSize: 14, 
                                            fontWeight: FontWeight.bold,
                                            color: bet.isNewlyAdded ? Colors.green.shade800 : null,
                                          ),
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      // Show a small "NEW" indicator for newly added bets
                                      if (bet.isNewlyAdded)
                                        Container(
                                          margin: const EdgeInsets.only(left: 4),
                                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: Colors.green,
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: const Text(
                                            'NEW',
                                            style: TextStyle(
                                              color: Colors.white,
                                              fontSize: 10,
                                              fontWeight: FontWeight.bold,
                                            ),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Expanded(
                                  flex: 2,
                                  child: Text(
                                    bet.market,
                                    style: const TextStyle(fontSize: 14),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                Expanded(
                                  flex: 2,
                                  child: Text(
                                    bet.outcome,
                                    style: const TextStyle(fontSize: 14),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                SizedBox(
                                  width: 60,
                                  child: Text(
                                    bet.odds.toStringAsFixed(2),
                                    style: const TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.green,
                                    ),
                                    textAlign: TextAlign.right,
                                  ),
                                ),
                              ],
                            ),
                            if (bet.group.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(left: 48.0, top: 4.0),
                                child: Text(
                                  bet.group,
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey.shade600,
                                    fontStyle: FontStyle.italic,
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  if (index < bets.length - 1) const Divider(height: 1),
                ],
              );
            },
          ),
        ),
      ],
    );
  }
}
