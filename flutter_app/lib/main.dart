import "package:flutter/material.dart";

import "screens/login_screen.dart";

void main() {
  runApp(const ResumeForgeApp());
}

class ResumeForgeApp extends StatefulWidget {
  const ResumeForgeApp({super.key});

  @override
  State<ResumeForgeApp> createState() => _ResumeForgeAppState();
}

class _ResumeForgeAppState extends State<ResumeForgeApp> {
  ThemeMode _themeMode = ThemeMode.light;

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: "ResumeForge Flutter",
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF0D9488),
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorSchemeSeed: const Color(0xFF0D9488),
      ),
      themeMode: _themeMode,
      home: LoginScreen(
        onToggleTheme: _toggleTheme,
        isDark: _themeMode == ThemeMode.dark,
      ),
    );
  }
}
