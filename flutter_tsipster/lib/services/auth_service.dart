import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService with ChangeNotifier {
  bool _isLoggedIn = false;
  bool _hasSetupProfile = false;
  String _username = '';
  String _email = '';
  Map<String, dynamic> _userPreferences = {};

  AuthService(bool isLoggedIn, bool hasSetupProfile) {
    _isLoggedIn = isLoggedIn;
    _hasSetupProfile = hasSetupProfile;
    _loadUserData();
  }

  bool get isLoggedIn => _isLoggedIn;
  bool get hasSetupProfile => _hasSetupProfile;
  String get username => _username;
  String get email => _email;
  Map<String, dynamic> get userPreferences => _userPreferences;

  Future<void> _loadUserData() async {
    if (_isLoggedIn) {
      final prefs = await SharedPreferences.getInstance();
      _username = prefs.getString('username') ?? '';
      _email = prefs.getString('email') ?? '';
      
      final prefsJson = prefs.getString('userPreferences');
      if (prefsJson != null) {
        _userPreferences = json.decode(prefsJson);
      }
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    // Add admin credentials check
    if (email == 'admin@tsipster.com' && password == 'Admin123') {
      _isLoggedIn = true;
      _hasSetupProfile = true;  // Skip profile setup for admin
      _username = 'Admin';
      _email = email;
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('isLoggedIn', true);
      await prefs.setBool('hasSetupProfile', true);
      await prefs.setString('username', _username);
      await prefs.setString('email', _email);
      
      // Add admin preferences
      final adminPrefs = {
        'preferences': {
          'Over/Under': 1.2,
          'Goal-Goal': 1.0,
          'Final Result': 1.1,
          '1X2': 1.3,
          'Handicap': 1.0,
          'Player-Specific': 0.9,
          'Other': 0.8
        },
        'leagues': ['Premier League', 'La Liga', 'Champions League'],
        'risk_tolerance': 4,
        'preferred_odds_range': [1.5, 5.0],
        'live_betting': 'Yes',
        'favorite_teams': ['Manchester United', 'Barcelona']
      };
      
      await prefs.setString('userPreferences', json.encode(adminPrefs));
      _userPreferences = adminPrefs;
      
      notifyListeners();
      return true;
    }
    
    // Original login logic
    try {
      // Simulated authentication
      await Future.delayed(const Duration(seconds: 1));
      
      // For demo, we'll accept any non-empty credentials
      if (email.isNotEmpty && password.isNotEmpty) {
        _isLoggedIn = true;
        _username = email.split('@').first;
        _email = email;
        
        // Check if profile is set up
        final prefs = await SharedPreferences.getInstance();
        _hasSetupProfile = prefs.getBool('hasSetupProfile') ?? false;
        
        await prefs.setBool('isLoggedIn', true);
        await prefs.setString('username', _username);
        await prefs.setString('email', _email);
        
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      print('Login error: $e');
      return false;
    }
  }

  Future<bool> register(String username, String email, String password) async {
    // In production, replace with actual API call
    try {
      // Simulated registration
      await Future.delayed(const Duration(seconds: 1));
      
      if (username.isNotEmpty && email.isNotEmpty && password.isNotEmpty) {
        _isLoggedIn = true;
        _username = username;
        _email = email;
        _hasSetupProfile = false;
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('isLoggedIn', true);
        await prefs.setBool('hasSetupProfile', false);
        await prefs.setString('username', _username);
        await prefs.setString('email', _email);
        
        notifyListeners();
        return true;
      }
      return false;
    } catch (e) {
      print('Registration error: $e');
      return false;
    }
  }

  Future<bool> saveUserProfile(Map<String, dynamic> preferences) async {
    try {
      _userPreferences = preferences;
      _hasSetupProfile = true;
      
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('hasSetupProfile', true);
      await prefs.setString('userPreferences', json.encode(preferences));
      
      // In production, you'd also update this on server
      // await _updateProfileOnServer(preferences);
      
      notifyListeners();
      return true;
    } catch (e) {
      print('Error saving profile: $e');
      return false;
    }
  }

  Future<void> logout() async {
    _isLoggedIn = false;
    _hasSetupProfile = false;
    _username = '';
    _email = '';
    _userPreferences = {};
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isLoggedIn', false);
    await prefs.setBool('hasSetupProfile', false);
    
    notifyListeners();
  }
}
