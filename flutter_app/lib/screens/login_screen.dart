import "package:flutter/material.dart";
import "package:shared_preferences/shared_preferences.dart";

import "../services/api_service.dart";
import "builder_screen.dart";

class LoginScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final bool isDark;
  const LoginScreen({
    super.key,
    required this.onToggleTheme,
    required this.isDark,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  static const _usernameKey = "rf_username";
  final _userCtrl = TextEditingController();
  final _api = ApiService();
  bool _loading = false;
  String _error = "";

  @override
  void initState() {
    super.initState();
    _loadSavedProfile();
  }

  Future<void> _loadSavedProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final savedName = (prefs.getString(_usernameKey) ?? "").trim();
    if (!mounted || savedName.isEmpty) {
      return;
    }
    _userCtrl.text = savedName;
    await _continueToBuilder(savedName);
  }

  Future<void> _continueToBuilder(String username) async {
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => BuilderScreen(
          api: _api,
          username: username,
          onToggleTheme: widget.onToggleTheme,
          isDark: widget.isDark,
        ),
      ),
    );
  }

  Future<void> _onContinue() async {
    final username = _userCtrl.text.trim();
    if (username.isEmpty) {
      setState(() => _error = "Please enter a username");
      return;
    }

    setState(() {
      _loading = true;
      _error = "";
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_usernameKey, username);
      await _continueToBuilder(username);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
            onPressed: widget.onToggleTheme,
            icon: Icon(widget.isDark ? Icons.light_mode : Icons.dark_mode),
            tooltip: "Toggle theme",
          ),
        ],
      ),
      body: Center(
        child: SizedBox(
          width: 360,
          child: Card(
            elevation: 6,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    "Create Profile",
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _userCtrl,
                    decoration: const InputDecoration(labelText: "Username"),
                  ),
                  if (_error.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Text(_error, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _loading ? null : _onContinue,
                      child: Text(_loading ? "Opening..." : "Continue"),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  void dispose() {
    _userCtrl.dispose();
    super.dispose();
  }
}
