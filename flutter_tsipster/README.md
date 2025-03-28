# Tsipster Flutter App

A Flutter version of the Tsipster bet suggestion application.

## Features

- Cross-platform (Android, iOS, Web, Desktop)
- Machine learning powered bet suggestions
- Dynamic odds calculations
- Responsive UI
- Online and offline mode with sample data fallback

## Getting Started

### Prerequisites

- Flutter SDK (latest stable version)
- Dart SDK
- Android Studio or Visual Studio Code with Flutter extensions

### Installation

1. Clone the repository
2. Navigate to the project directory
3. Run `flutter pub get` to install dependencies
4. Make sure you have the appropriate assets in the assets folder

### Running the App

#### For Development

```bash
# Run in debug mode on connected device or emulator
flutter run

# Run on Chrome
flutter run -d chrome

# Run on Windows
flutter run -d windows

# Run on macOS
flutter run -d macos
```

#### Building for Production

```bash
# Build APK for Android
flutter build apk

# Build for iOS
flutter build ios

# Build for Web
flutter build web

# Build for Windows
flutter build windows

# Build for macOS
flutter build macos
```

## Project Structure

- `lib/` - Contains all Dart code
  - `main.dart` - Entry point of the application
  - `models/` - Data models
  - `screens/` - UI screens
  - `services/` - Business logic and API services
  - `theme/` - Theme configuration
  - `widgets/` - Reusable UI components

- `assets/` - Contains all static assets
  - `images/` - Image files
  - `data/` - JSON data files

## API Integration

The app connects to the Flask backend on `http://127.0.0.1:5000`. If you're running on an Android emulator and need to connect to the Flask server on your computer, use `10.0.2.2` instead of `localhost`.

To modify the API endpoint, edit the `baseUrl` variable in `lib/services/bet_service.dart`.
