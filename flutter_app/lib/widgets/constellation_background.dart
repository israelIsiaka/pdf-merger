import 'dart:math';
import 'package:flutter/material.dart';

class _Star {
  double x;
  double y;
  double radius;
  double pulseOffset;

  _Star({
    required this.x,
    required this.y,
    required this.radius,
    required this.pulseOffset,
  });
}

class ConstellationBackground extends StatefulWidget {
  const ConstellationBackground({super.key});

  @override
  State<ConstellationBackground> createState() =>
      _ConstellationBackgroundState();
}

class _ConstellationBackgroundState extends State<ConstellationBackground>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late List<_Star> _stars;
  final Random _rng = Random(42);

  static const int _starCount = 90;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 8),
    )..repeat();
    _stars = List.generate(_starCount, (i) {
      return _Star(
        x: _rng.nextDouble(),
        y: _rng.nextDouble(),
        radius: 0.8 + _rng.nextDouble() * 1.4,
        pulseOffset: _rng.nextDouble() * 2 * pi,
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return CustomPaint(
          painter: _ConstellationPainter(
            stars: _stars,
            progress: _controller.value,
          ),
          child: const SizedBox.expand(),
        );
      },
    );
  }
}

class _ConstellationPainter extends CustomPainter {
  final List<_Star> stars;
  final double progress;

  _ConstellationPainter({required this.stars, required this.progress});

  @override
  void paint(Canvas canvas, Size size) {
    // Background
    canvas.drawRect(
      Rect.fromLTWH(0, 0, size.width, size.height),
      Paint()..color = const Color(0xFF080c18),
    );

    final t = progress * 2 * pi;

    // Connection lines
    const double connectionDistance = 120.0;

    for (int i = 0; i < stars.length; i++) {
      for (int j = i + 1; j < stars.length; j++) {
        final a = stars[i];
        final b = stars[j];
        final dx = (a.x - b.x) * size.width;
        final dy = (a.y - b.y) * size.height;
        final dist = sqrt(dx * dx + dy * dy);
        if (dist < connectionDistance) {
          final opacity =
              (1.0 - dist / connectionDistance) * 0.11;
          canvas.drawLine(
            Offset(a.x * size.width, a.y * size.height),
            Offset(b.x * size.width, b.y * size.height),
            Paint()
              ..color = Color.fromRGBO(60, 120, 255, opacity)
              ..strokeWidth = 0.6,
          );
        }
      }
    }

    // Stars
    for (final star in stars) {
      final pulse = 0.7 + 0.3 * sin(t + star.pulseOffset);
      final r = star.radius * pulse;
      final cx = star.x * size.width;
      final cy = star.y * size.height;

      // Glow
      final glowPaint = Paint()
        ..color = const Color(0xFF7ab4ff).withAlpha(30)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
      canvas.drawCircle(Offset(cx, cy), r * 2.5, glowPaint);

      // Core
      canvas.drawCircle(
        Offset(cx, cy),
        r,
        Paint()..color = const Color(0xFF7ab4ff).withAlpha((200 * pulse).toInt()),
      );
    }
  }

  @override
  bool shouldRepaint(_ConstellationPainter old) =>
      old.progress != progress;
}
