import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/bet_service.dart';
import 'screens/home_screen.dart';
import 'theme/app_theme.dart';

void main() {
  // For debugging network issues
  WidgetsFlutterBinding.ensureInitialized();
  
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (context) => BetService()),
      ],
      child: const TsipsterApp(),
    ),
  );
}

class TsipsterApp extends StatelessWidget {
  const TsipsterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tsipster - Bet Suggestor',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      home: const HomeScreen(),
      debugShowCheckedModeBanner: true, // Show debug banner
    );
  }
}
