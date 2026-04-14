import 'package:flutter/material.dart';

// ---------------------------------------------------------------------------
// AppColors — ThemeExtension providing context-aware colors for dark + light
// ---------------------------------------------------------------------------
class AppColors extends ThemeExtension<AppColors> {
  const AppColors({
    required this.background,
    required this.cardBackground,
    required this.cardBorder,
    required this.inputFill,
    required this.previewBackground,
    required this.textPrimary,
    required this.textSecondary,
    required this.success,
    required this.error,
    required this.warning,
    required this.primary,
  });

  final Color background;
  final Color cardBackground;
  final Color cardBorder;
  final Color inputFill;
  final Color previewBackground;
  final Color textPrimary;
  final Color textSecondary;
  final Color success;
  final Color error;
  final Color warning;
  final Color primary;

  // ── Dark palette ──────────────────────────────────────────────────────────
  static const AppColors dark = AppColors(
    background:        Color(0xFF080c18),
    cardBackground:    Color(0xFF0d1220),
    cardBorder:        Color(0xFF1e2a42),
    inputFill:         Color(0xFF0a0f1e),
    previewBackground: Color(0xFF060a12),
    textPrimary:       Color(0xFFe2e8f0),
    textSecondary:     Color(0xFF64748b),
    success:           Color(0xFF22c55e),
    error:             Color(0xFFef4444),
    warning:           Color(0xFFf59e0b),
    primary:           Color(0xFF4f7ef7),
  );

  // ── Light palette ─────────────────────────────────────────────────────────
  static const AppColors light = AppColors(
    background:        Color(0xFFf1f5f9),
    cardBackground:    Color(0xFFffffff),
    cardBorder:        Color(0xFFdde3ee),
    inputFill:         Color(0xFFf8fafc),
    previewBackground: Color(0xFFe4eaf4),
    textPrimary:       Color(0xFF1e293b),
    textSecondary:     Color(0xFF64748b),
    success:           Color(0xFF16a34a),
    error:             Color(0xFFdc2626),
    warning:           Color(0xFFd97706),
    primary:           Color(0xFF3b6fd4),
  );

  static AppColors of(BuildContext context) =>
      Theme.of(context).extension<AppColors>() ?? dark;

  @override
  AppColors copyWith({
    Color? background,
    Color? cardBackground,
    Color? cardBorder,
    Color? inputFill,
    Color? previewBackground,
    Color? textPrimary,
    Color? textSecondary,
    Color? success,
    Color? error,
    Color? warning,
    Color? primary,
  }) =>
      AppColors(
        background:        background        ?? this.background,
        cardBackground:    cardBackground    ?? this.cardBackground,
        cardBorder:        cardBorder        ?? this.cardBorder,
        inputFill:         inputFill         ?? this.inputFill,
        previewBackground: previewBackground ?? this.previewBackground,
        textPrimary:       textPrimary       ?? this.textPrimary,
        textSecondary:     textSecondary     ?? this.textSecondary,
        success:           success           ?? this.success,
        error:             error             ?? this.error,
        warning:           warning           ?? this.warning,
        primary:           primary           ?? this.primary,
      );

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      background:        Color.lerp(background,        other.background,        t)!,
      cardBackground:    Color.lerp(cardBackground,    other.cardBackground,    t)!,
      cardBorder:        Color.lerp(cardBorder,        other.cardBorder,        t)!,
      inputFill:         Color.lerp(inputFill,         other.inputFill,         t)!,
      previewBackground: Color.lerp(previewBackground, other.previewBackground, t)!,
      textPrimary:       Color.lerp(textPrimary,       other.textPrimary,       t)!,
      textSecondary:     Color.lerp(textSecondary,     other.textSecondary,     t)!,
      success:           Color.lerp(success,           other.success,           t)!,
      error:             Color.lerp(error,             other.error,             t)!,
      warning:           Color.lerp(warning,           other.warning,           t)!,
      primary:           Color.lerp(primary,           other.primary,           t)!,
    );
  }
}

// ---------------------------------------------------------------------------
// AppTheme — static color constants (dark, kept for compat) + ThemeData
// ---------------------------------------------------------------------------
class AppTheme {
  // Keep legacy constants pointing at dark values so existing code that
  // doesn't need theming compiles without touching every file.
  static const Color background    = Color(0xFF080c18);
  static const Color cardBackground= Color(0xFF0d1220);
  static const Color cardBorder    = Color(0xFF1e2a42);
  static const Color primary       = Color(0xFF4f7ef7);
  static const Color textPrimary   = Color(0xFFe2e8f0);
  static const Color textSecondary = Color(0xFF64748b);
  static const Color success       = Color(0xFF22c55e);
  static const Color error         = Color(0xFFef4444);
  static const Color warning       = Color(0xFFf59e0b);

  // ── Dark ThemeData ────────────────────────────────────────────────────────
  static ThemeData get darkTheme => _build(AppColors.dark, Brightness.dark);

  // ── Light ThemeData ───────────────────────────────────────────────────────
  static ThemeData get lightTheme => _build(AppColors.light, Brightness.light);

  static ThemeData _build(AppColors c, Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    return ThemeData(
      useMaterial3: false,
      brightness: brightness,
      scaffoldBackgroundColor: c.background,
      extensions: [c],
      colorScheme: ColorScheme(
        brightness: brightness,
        surface:    c.background,
        primary:    c.primary,
        secondary:  isDark ? const Color(0xFF7ab4ff) : const Color(0xFF5b8fe8),
        error:      c.error,
        onPrimary:  Colors.white,
        onSurface:  c.textPrimary,
        onSecondary:Colors.white,
        onError:    Colors.white,
        outline:    c.cardBorder,
      ),
      cardTheme: CardThemeData(
        color: c.cardBackground,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: c.cardBorder),
        ),
        margin: EdgeInsets.zero,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: c.background,
        foregroundColor: c.textPrimary,
        elevation: 0,
        titleTextStyle: TextStyle(
          color: c.textPrimary,
          fontSize: 18,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.3,
        ),
        iconTheme: IconThemeData(color: c.textPrimary),
      ),
      textTheme: TextTheme(
        displayLarge:  TextStyle(color: c.textPrimary, fontWeight: FontWeight.bold),
        displayMedium: TextStyle(color: c.textPrimary, fontWeight: FontWeight.bold),
        displaySmall:  TextStyle(color: c.textPrimary, fontWeight: FontWeight.bold),
        headlineLarge: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600),
        headlineMedium:TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600),
        headlineSmall: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600),
        titleLarge:    TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600),
        titleMedium:   TextStyle(color: c.textPrimary, fontWeight: FontWeight.w500),
        titleSmall:    TextStyle(color: c.textPrimary, fontWeight: FontWeight.w500),
        bodyLarge:     TextStyle(color: c.textPrimary),
        bodyMedium:    TextStyle(color: c.textPrimary),
        bodySmall:     TextStyle(color: c.textSecondary),
        labelLarge:    TextStyle(color: c.textPrimary, fontWeight: FontWeight.w500),
        labelMedium:   TextStyle(color: c.textSecondary),
        labelSmall:    TextStyle(color: c.textSecondary),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: c.inputFill,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: c.cardBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: c.cardBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: c.primary, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: c.error),
        ),
        labelStyle: TextStyle(color: c.textSecondary),
        hintStyle:  TextStyle(color: c.textSecondary),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: c.primary,
          foregroundColor: Colors.white,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          elevation: 0,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: c.textPrimary,
          side: BorderSide(color: c.cardBorder),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(foregroundColor: c.primary),
      ),
      iconButtonTheme: IconButtonThemeData(
        style: IconButton.styleFrom(foregroundColor: c.textPrimary),
      ),
      dividerTheme: DividerThemeData(
        color: c.cardBorder, thickness: 1, space: 1,
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: c.primary,
        inactiveTrackColor: c.cardBorder,
        thumbColor: c.primary,
        overlayColor: c.primary.withAlpha(50),
        valueIndicatorColor: c.primary,
        valueIndicatorTextStyle: const TextStyle(color: Colors.white),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((s) =>
            s.contains(WidgetState.selected) ? c.primary : Colors.transparent),
        side: BorderSide(color: c.cardBorder, width: 1.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(3)),
      ),
      radioTheme: RadioThemeData(
        fillColor: WidgetStateProperty.resolveWith((s) =>
            s.contains(WidgetState.selected) ? c.primary : c.textSecondary),
      ),
      dropdownMenuTheme: DropdownMenuThemeData(
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: c.inputFill,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: c.cardBorder),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: c.cardBorder),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide(color: c.primary),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        ),
        menuStyle: MenuStyle(
          backgroundColor: WidgetStateProperty.all(c.cardBackground),
          side: WidgetStateProperty.all(BorderSide(color: c.cardBorder)),
          shape: WidgetStateProperty.all(
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: isDark ? const Color(0xFF1e2a42) : const Color(0xFF1e293b),
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        behavior: SnackBarBehavior.floating,
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(
        color: c.primary,
        linearTrackColor: c.cardBorder,
      ),
      scrollbarTheme: ScrollbarThemeData(
        thumbColor: WidgetStateProperty.all(
            isDark ? const Color(0xFF2d3f5e) : const Color(0xFFb0bec5)),
        trackColor: WidgetStateProperty.all(Colors.transparent),
        radius: const Radius.circular(4),
        thickness: WidgetStateProperty.all(4),
      ),
    );
  }
}
