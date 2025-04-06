import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../utils/image_helper.dart';

class ProfileSetupScreen extends StatefulWidget {
  const ProfileSetupScreen({Key? key}) : super(key: key);

  @override
  State<ProfileSetupScreen> createState() => _ProfileSetupScreenState();
}

class _ProfileSetupScreenState extends State<ProfileSetupScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;
  bool _isLoading = false;
  
  // User preferences data
  final Map<String, double> _betTypePreferences = {
    'Over/Under': 1.0,
    'Goal-Goal': 1.0,
    'Final Result': 1.0,
    '1X2': 1.0,
    'Handicap': 1.0,
    'Player-Specific': 1.0,
    'Other': 1.0,
  };
  List<String> _selectedLeagues = [];
  int _riskTolerance = 3; // 1-5 scale
  double _minOdds = 1.5;
  double _maxOdds = 3.0;
  bool _liveBetting = false;
  List<String> _favoriteTeams = [];
  final TextEditingController _teamController = TextEditingController();

  @override
  void dispose() {
    _pageController.dispose();
    _teamController.dispose();
    super.dispose();
  }

  void _nextPage() {
    if (_currentPage < 5) {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _saveProfile();
    }
  }

  void _previousPage() {
    if (_currentPage > 0) {
      _pageController.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _saveProfile() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final authService = Provider.of<AuthService>(context, listen: false);
      
      final preferences = {
        'preferences': _betTypePreferences,
        'leagues': _selectedLeagues,
        'risk_tolerance': _riskTolerance,
        'preferred_odds_range': [_minOdds, _maxOdds],
        'live_betting': _liveBetting ? 'Yes' : 'No',
        'favorite_teams': _favoriteTeams,
      };
      
      final success = await authService.saveUserProfile(preferences);
      
      if (success) {
        Navigator.pushReplacementNamed(context, '/home');
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to save profile. Please try again.')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _addTeam() {
    final team = _teamController.text.trim();
    if (team.isNotEmpty && !_favoriteTeams.contains(team)) {
      setState(() {
        _favoriteTeams.add(team);
        _teamController.clear();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Set Up Your Profile'),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Theme.of(context).primaryColor,
      ),
      body: Column(
        children: [
          // Progress indicator
          LinearProgressIndicator(
            value: (_currentPage + 1) / 6,
            backgroundColor: Colors.grey.shade200,
          ),
          
          // Main content - use PageTransformer for smoother transitions
          Expanded(
            child: PageView(
              controller: _pageController,
              physics: const ClampingScrollPhysics(), // Smoother scrolling
              onPageChanged: (index) {
                setState(() {
                  _currentPage = index;
                });
              },
              children: [
                // Use RepaintBoundary to optimize rendering for each page
                RepaintBoundary(child: _buildWelcomePage()),
                RepaintBoundary(child: _buildBetTypePreferencesPage()),
                RepaintBoundary(child: _buildLeaguesPage()),
                RepaintBoundary(child: _buildRiskAndOddsPage()),
                RepaintBoundary(child: _buildLiveBettingPage()),
                RepaintBoundary(child: _buildFavoriteTeamsPage()),
              ],
            ),
          ),
          
          // Navigation buttons
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (_currentPage > 0)
                  OutlinedButton(
                    onPressed: _previousPage,
                    child: const Text('Back'),
                  )
                else
                  const SizedBox(),
                ElevatedButton(
                  onPressed: _isLoading ? null : _nextPage,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2,
                          ),
                        )
                      : Text(_currentPage < 5 ? 'Next' : 'Finish'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomePage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ImageHelper.loadAsset(
              'assets/images/tsipster.png',
              height: 100,
            ),
            const SizedBox(height: 40),
            const Text(
              'Welcome to Tsipster!',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              'Let\'s personalize your betting experience',
              style: TextStyle(fontSize: 18),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 40),
            const Text(
              'We\'ll ask you a few questions to customize our betting suggestions just for you.',
              style: TextStyle(fontSize: 16),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            const Text(
              'This will take less than 2 minutes.',
              style: TextStyle(
                fontSize: 16,
                fontStyle: FontStyle.italic,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBetTypePreferencesPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Bet Type Preferences',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Adjust the sliders to indicate your preference for each bet type:',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 32),
          
          ..._betTypePreferences.entries.map((entry) => _buildPreferenceSlider(
            entry.key,
            entry.value,
            (value) {
              setState(() {
                _betTypePreferences[entry.key] = value;
              });
            },
          )),
        ],
      ),
    );
  }

  Widget _buildPreferenceSlider(String label, double value, Function(double) onChanged) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        Row(
          children: [
            const Text('Low', style: TextStyle(fontSize: 12)),
            Expanded(
              child: Slider(
                value: value,
                min: 0.1,
                max: 2.0,
                divisions: 19,
                label: value.toStringAsFixed(1),
                onChanged: onChanged,
              ),
            ),
            const Text('High', style: TextStyle(fontSize: 12)),
          ],
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildLeaguesPage() {
    final leagues = [
      'English Premier League',
      'La Liga',
      'Serie A',
      'Bundesliga',
      'Ligue 1',
      'Champions League',
      'Europa League',
      'World Cup',
      'Euro Championship',
      'Copa America',
    ];
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Favorite Leagues',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Select the leagues you\'re most interested in:',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 32),
          
          ...leagues.map((league) => CheckboxListTile(
            title: Text(league),
            value: _selectedLeagues.contains(league),
            onChanged: (selected) {
              setState(() {
                if (selected ?? false) {
                  if (!_selectedLeagues.contains(league)) {
                    _selectedLeagues.add(league);
                  }
                } else {
                  _selectedLeagues.remove(league);
                }
              });
            },
          )),
        ],
      ),
    );
  }

  Widget _buildRiskAndOddsPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Risk Tolerance & Odds',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 32),
          
          // Risk tolerance
          const Text(
            'What\'s your risk tolerance?',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Slider(
            value: _riskTolerance.toDouble(),
            min: 1,
            max: 5,
            divisions: 4,
            label: ['Very Low', 'Low', 'Medium', 'High', 'Very High'][_riskTolerance - 1],
            onChanged: (value) {
              setState(() {
                _riskTolerance = value.round();
              });
            },
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text('Very Low', style: TextStyle(fontSize: 12)),
              Text('Very High', style: TextStyle(fontSize: 12)),
            ],
          ),
          
          const SizedBox(height: 40),
          
          // Odds range
          const Text(
            'Preferred odds range:',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          
          // Min odds
          Row(
            children: [
              const Expanded(
                flex: 2,
                child: Text('Minimum odds:'),
              ),
              Expanded(
                flex: 3,
                child: Slider(
                  value: _minOdds,
                  min: 1.0,
                  max: 3.0,
                  divisions: 20,
                  label: _minOdds.toStringAsFixed(1),
                  onChanged: (value) {
                    setState(() {
                      _minOdds = value;
                      if (_maxOdds < _minOdds) {
                        _maxOdds = _minOdds + 0.5;
                      }
                    });
                  },
                ),
              ),
              SizedBox(
                width: 60,
                child: Text(
                  _minOdds.toStringAsFixed(1),
                  textAlign: TextAlign.right,
                ),
              ),
            ],
          ),
          
          // Max odds
          Row(
            children: [
              const Expanded(
                flex: 2,
                child: Text('Maximum odds:'),
              ),
              Expanded(
                flex: 3,
                child: Slider(
                  value: _maxOdds,
                  min: _minOdds + 0.1,
                  max: 10.0,
                  divisions: 89,
                  label: _maxOdds.toStringAsFixed(1),
                  onChanged: (value) {
                    setState(() {
                      _maxOdds = value;
                    });
                  },
                ),
              ),
              SizedBox(
                width: 60,
                child: Text(
                  _maxOdds.toStringAsFixed(1),
                  textAlign: TextAlign.right,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLiveBettingPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Live Betting Preferences',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 40),
          
          const Text(
            'Do you prefer live betting or pre-match betting?',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 24),
          
          SwitchListTile(
            title: const Text(
              'Enable Live Betting',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            subtitle: Text(_liveBetting 
              ? 'We\'ll include live betting options in suggestions' 
              : 'We\'ll focus on pre-match betting options only'),
            value: _liveBetting,
            onChanged: (value) {
              setState(() {
                _liveBetting = value;
              });
            },
          ),
          
          const SizedBox(height: 40),
          
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'About Live Betting',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 12),
                  Text(
                    'Live betting allows you to place bets on a match that is already in progress. Odds change in real-time based on the current state of the game.',
                    style: TextStyle(fontSize: 14),
                  ),
                  SizedBox(height: 12),
                  Text(
                    'While potentially more profitable, live betting requires quick decisions and careful analysis of the match dynamics.',
                    style: TextStyle(fontSize: 14),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFavoriteTeamsPage() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Favorite Teams',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Let us know which teams you follow closely:',
            style: TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 32),
          
          // Add team input
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _teamController,
                  decoration: const InputDecoration(
                    labelText: 'Team name',
                    hintText: 'Enter a team you follow',
                  ),
                  onSubmitted: (_) => _addTeam(),
                ),
              ),
              const SizedBox(width: 16),
              ElevatedButton(
                onPressed: _addTeam,
                child: const Text('Add'),
              ),
            ],
          ),
          
          const SizedBox(height: 24),
          
          // Favorite teams list
          if (_favoriteTeams.isEmpty)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 20.0),
                child: Text(
                  'No favorite teams added yet',
                  style: TextStyle(fontStyle: FontStyle.italic, color: Colors.grey),
                ),
              ),
            )
          else
            Card(
              child: Column(
                children: _favoriteTeams.map((team) => ListTile(
                  title: Text(team),
                  trailing: IconButton(
                    icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                    onPressed: () {
                      setState(() {
                        _favoriteTeams.remove(team);
                      });
                    },
                  ),
                )).toList(),
              ),
            ),
          
          const SizedBox(height: 24),
          
          // Note
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16.0),
              child: Text(
                'Note: Adding your favorite teams helps us suggest bets that might interest you more, but we\'ll still provide objective betting recommendations.',
                style: TextStyle(fontStyle: FontStyle.italic),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
