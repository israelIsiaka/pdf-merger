import 'package:flutter/material.dart';

class ThemeNotifier extends ValueNotifier<ThemeMode> {
  ThemeNotifier() : super(ThemeMode.dark);

  void toggle() {
    value = value == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
  }

  bool get isDark => value == ThemeMode.dark;
}

/// Singleton so any widget can reach it without InheritedWidget boilerplate.
final themeNotifier = ThemeNotifier();
