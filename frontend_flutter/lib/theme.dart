import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const Color primary = Color(0xFF4F46E5);
  static const Color primaryLight = Color(0xFF6366F1);
  static const Color primaryGlow = Color(0x4D4F46E5); // rgba(79,70,229,.3)
  static const Color bg = Color(0xFF0B0F1A);
  static const Color surface = Color(0xFF131929);
  static const Color surface2 = Color(0xFF1A2236);
  static const Color border = Color(0x12FFFFFF); // rgba(255,255,255,.07)
  static const Color text = Color(0xFFF1F5F9);
  static const Color muted = Color(0xFF64748B);
  static const Color success = Color(0xFF10B981);
  static const Color danger = Color(0xFFEF4444);
  static const Color warning = Color(0xFFF59E0B);
  static const Color accent = Color(0xFF6366F1);
  
  // Dashboard specific (from dashboard.css)
  static const Color sidebarBg = Color(0xFF13161F);
  static const Color cardBg = Color(0xFF1A1F2E);
  static const Color dashBg = Color(0xFF0F1117);

  // Light Mode Colors
  static const Color lightBg = Color(0xFFF8FAFC);
  static const Color lightSurface = Colors.white;
  static const Color lightBorder = Color(0xFFE2E8F0);
  static const Color lightText = Color(0xFF1E293B);
  static const Color lightMuted = Color(0xFF64748B);
}

class AppTheme {
  static ThemeData get darkTheme {
    final base = ThemeData.dark();
    return base.copyWith(
      scaffoldBackgroundColor: AppColors.bg,
      primaryColor: AppColors.primary,
      dividerColor: AppColors.border,
      textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
        bodyColor: AppColors.text,
        displayColor: AppColors.text,
      ),
      cardTheme: base.cardTheme.copyWith(
        color: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: AppColors.border),
        ),
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ),
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        filled: true,
        fillColor: AppColors.surface2,
        hintStyle: const TextStyle(color: AppColors.muted, fontSize: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.primary),
        ),
      ),
    );
  }

  static ThemeData get lightTheme {
    final base = ThemeData.light();
    return base.copyWith(
      scaffoldBackgroundColor: AppColors.lightBg,
      primaryColor: AppColors.primary,
      dividerColor: AppColors.lightBorder,
      textTheme: GoogleFonts.interTextTheme(base.textTheme).apply(
        bodyColor: AppColors.lightText,
        displayColor: AppColors.lightText,
      ),
      cardTheme: base.cardTheme.copyWith(
        color: AppColors.lightSurface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: AppColors.lightBorder),
        ),
        elevation: 0,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
        ),
      ),
      inputDecorationTheme: base.inputDecorationTheme.copyWith(
        filled: true,
        fillColor: const Color(0xFFF1F5F9),
        hintStyle: const TextStyle(color: AppColors.lightMuted, fontSize: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.lightBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.lightBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.primary),
        ),
      ),
    );
  }
}
