import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/bet_service.dart';

class StatusLog extends StatelessWidget {
  const StatusLog({super.key});

  @override
  Widget build(BuildContext context) {
    final betService = Provider.of<BetService>(context);
    final logs = betService.statusLog;
    
    return Container(
      height: 200,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey.shade100,
        borderRadius: BorderRadius.circular(4),
      ),
      child: ListView.builder(
        reverse: false,
        itemCount: logs.length,
        itemBuilder: (context, index) {
          final log = logs[index];
          
          // Extract timestamp if present
          final hasTimestamp = log.contains(':');
          String timestamp = '';
          String message = log;
          
          if (hasTimestamp) {
            final parts = log.split(':');
            if (parts.length > 1) {
              timestamp = parts[0].trim();
              message = parts.sublist(1).join(':').trim();
            }
          }
          
          // Highlight important messages
          final bool isLimitMessage = message.contains('Limited to') && message.contains('available unique matches');
          
          return Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (hasTimestamp)
                  Text(
                    timestamp,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey.shade600,
                    ),
                  ),
                Text(
                  message,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: isLimitMessage ? FontWeight.bold : FontWeight.normal,
                    color: isLimitMessage ? Colors.orange.shade800 : null,
                  ),
                ),
                const Divider(height: 4),
              ],
            ),
          );
        },
      ),
    );
  }
}
