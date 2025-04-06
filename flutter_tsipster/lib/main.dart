import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'services/bet_service.dart';
import 'services/auth_service.dart';
import 'screens/home_screen.dart';
import 'screens/landing_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/profile_setup_screen.dart';
import 'theme/app_theme.dart';

void main() async {
  // For debugging network issues
  WidgetsFlutterBinding.ensureInitialized();
  
  // Configure image cache with proper method calls instead of assignments
  PaintingBinding.instance.imageCache.maximumSize = 100;
  PaintingBinding.instance.imageCache.maximumSizeBytes = 50 * 1024 * 1024; // 50 MB
  
  // Initialize shared preferences for auth state
  final prefs = await SharedPreferences.getInstance();
  final isLoggedIn = prefs.getBool('isLoggedIn') ?? false;
  final hasSetupProfile = prefs.getBool('hasSetupProfile') ?? false;
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => BetService()),
        ChangeNotifierProvider(create: (context) => AuthService(isLoggedIn, hasSetupProfile)),
      ],
      child: const TsipsterApp(),
    ),
  );
}

class TsipsterApp extends StatelessWidget {
  const TsipsterApp({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);
    
    return MaterialApp(
      title: 'Tsipster - Your Bet Mentor',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      debugShowCheckedModeBanner: false,
      initialRoute: '/',
      
      // Add restorationScopeId for better state restoration
      restorationScopeId: 'tsipster_app',
      
      routes: {
        '/': (context) => authService.isLoggedIn 
               ? (authService.hasSetupProfile 
                  ? const HomeScreen() 
                  : const ProfileSetupScreen())
               : const LandingScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/profile-setup': (context) => const ProfileSetupScreen(),
        '/home': (context) => const HomeScreen(),
      },
    );
  }
}
