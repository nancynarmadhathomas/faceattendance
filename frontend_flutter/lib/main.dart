import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'theme.dart';
import 'providers/theme_provider.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/employee_dashboard.dart';
import 'screens/admin_dashboard.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(
    ChangeNotifierProvider(
      create: (context) => ThemeProvider(),
      child: const FaceAttendApp(),
    ),
  );
}

class FaceAttendApp extends StatelessWidget {
  const FaceAttendApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    
    return MaterialApp(
      title: 'Face Attendance System',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProvider.isDark ? ThemeMode.dark : ThemeMode.light,
      initialRoute: '/',
      routes: {
        '/': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/dashboard': (context) => const EmployeeDashboard(),
        '/admin': (context) => const AdminDashboard(),
      },
    );
  }
}
