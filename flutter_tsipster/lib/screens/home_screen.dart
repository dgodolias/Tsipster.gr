import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/bet_parameters.dart';
import '../services/bet_service.dart';
import '../widgets/bet_parameters_form.dart';
import '../widgets/bet_table.dart';
import '../widgets/status_log.dart';
import '../utils/image_helper.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final betService = Provider.of<BetService>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            ImageHelper.loadAsset(
              'assets/images/tsipster.png',
              height: 40,
            ),
            const SizedBox(width: 10),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () {
              // Show about dialog
              showAboutDialog(
                context: context,
                applicationName: 'Tsipster',
                applicationVersion: '1.0.0',
                applicationLegalese: '© 2025 Tsipster - The Smart Bet Suggestor',
                children: [
                  const Text(
                    'Tsipster is a Flutter application that suggests bets based on machine learning and user preferences.',
                  ),
                ],
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.contact_mail_outlined),
            onPressed: () {
              // Show contact info
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Contact: support@tsipster.com'),
                  duration: Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Stack(
          children: [
            SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Main content in two columns on larger screens
                  LayoutBuilder(
                    builder: (context, constraints) {
                      if (constraints.maxWidth > 600) {
                        // Tablet/desktop layout
                        return Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Left column - Parameters and Status Log
                            Expanded(
                              flex: 1,
                              child: Column(
                                children: [
                                  _buildParametersCard(context),
                                  const SizedBox(height: 16),
                                  _buildStatusLogCard(context),
                                ],
                              ),
                            ),
                            const SizedBox(width: 16),
                            // Right column - Betting Slip
                            Expanded(
                              flex: 2,
                              child: _buildBettingSlipCard(context),
                            ),
                          ],
                        );
                      } else {
                        // Mobile layout - stacked
                        return Column(
                          children: [
                            _buildParametersCard(context),
                            const SizedBox(height: 16),
                            _buildBettingSlipCard(context),
                            const SizedBox(height: 16),
                            _buildStatusLogCard(context),
                          ],
                        );
                      }
                    },
                  ),
                ],
              ),
            ),
            // Loading indicator
            if (betService.isLoading)
              Container(
                color: Colors.black54,
                child: const Center(
                  child: CircularProgressIndicator(),
                ),
              ),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        color: Theme.of(context).primaryColor,
        padding: const EdgeInsets.symmetric(vertical: 16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ImageHelper.loadAsset(
              'assets/images/tsipster.png',
              height: 30,
              color: Colors.white,
            ),
            const SizedBox(width: 10),
            const Text(
              '© 2025 Tsipster - The Smart Bet Suggestor',
              style: TextStyle(color: Colors.white),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersCard(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            color: Theme.of(context).primaryColor,
            padding: const EdgeInsets.all(12),
            child: const Row(
              children: [
                Icon(Icons.tune, color: Colors.white),
                SizedBox(width: 8),
                Text(
                  'Bet Parameters',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: BetParametersForm(
              onSubmit: (params) {
                Provider.of<BetService>(context, listen: false)
                    .generateBets(params);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusLogCard(BuildContext context) {
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            color: Theme.of(context).colorScheme.secondary,
            padding: const EdgeInsets.all(12),
            child: const Row(
              children: [
                Icon(Icons.info, color: Colors.white),
                SizedBox(width: 8),
                Text(
                  'Status Log',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const StatusLog(),
        ],
      ),
    );
  }

  Widget _buildBettingSlipCard(BuildContext context) {
    final betService = Provider.of<BetService>(context);
    
    return Card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            color: Theme.of(context).primaryColor,
            padding: const EdgeInsets.all(12),
            child: const Row(
              children: [
                Icon(Icons.receipt_long, color: Colors.white),
                SizedBox(width: 8),
                Text(
                  'Betting Slip',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const BetTable(),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const Text(
                  'Total Odds: ',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  betService.totalOdds.toStringAsFixed(2),
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.green,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
