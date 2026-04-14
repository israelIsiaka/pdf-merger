import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../theme/theme_notifier.dart';
import '../widgets/constellation_background.dart';
import '../widgets/tool_card.dart';
import 'merge_screen.dart';
import 'protect_screen.dart';
import 'peep_screen.dart';
import 'viewer_screen.dart';
import 'compress_screen.dart';
import 'watermark_screen.dart';
import 'split_screen.dart';
import 'pdf_to_word_screen.dart';
import 'word_to_pdf_screen.dart';
import 'pdf_to_images_screen.dart';
import 'images_to_pdf_screen.dart';
import 'sign_annotate_screen.dart';
import 'history_screen.dart';
import 'faq_screen.dart';
import 'contributors_screen.dart';

class _ToolDef {
  final String name;
  final String description;
  final String symbol;
  final Color color;
  final Widget Function() screenBuilder;

  const _ToolDef({
    required this.name,
    required this.description,
    required this.symbol,
    required this.color,
    required this.screenBuilder,
  });
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  static final List<_ToolDef> _tools = [
    _ToolDef(
      name: 'Merge PDFs',
      description: 'Combine multiple PDF files into one document',
      symbol: '+',
      color: const Color(0xFF4f7ef7),
      screenBuilder: () => const MergeScreen(),
    ),
    _ToolDef(
      name: 'Protect PDF',
      description: 'Encrypt your PDF with a password',
      symbol: 'P',
      color: const Color(0xFFeab308),
      screenBuilder: () => const ProtectScreen(),
    ),
    _ToolDef(
      name: 'Peep PDF',
      description: 'Remove password protection from a PDF',
      symbol: '?',
      color: const Color(0xFFa78bfa),
      screenBuilder: () => const PeepScreen(),
    ),
    _ToolDef(
      name: 'View PDF',
      description: 'Open and read PDF documents',
      symbol: 'V',
      color: const Color(0xFF22d3ee),
      screenBuilder: () => const ViewerScreen(),
    ),
    _ToolDef(
      name: 'Compress PDF',
      description: 'Reduce PDF file size without losing quality',
      symbol: 'Z',
      color: const Color(0xFF8b5cf6),
      screenBuilder: () => const CompressScreen(),
    ),
    _ToolDef(
      name: 'Watermark',
      description: 'Add text or image watermarks to your PDF pages',
      symbol: 'W',
      color: const Color(0xFF06b6d4),
      screenBuilder: () => const WatermarkScreen(),
    ),
    _ToolDef(
      name: 'Split PDF',
      description: 'Extract pages or split into multiple files',
      symbol: '/',
      color: const Color(0xFFf59e0b),
      screenBuilder: () => const SplitScreen(),
    ),
    _ToolDef(
      name: 'PDF to Word',
      description: 'Convert PDF documents to editable Word files',
      symbol: 'W',
      color: const Color(0xFFef4444),
      screenBuilder: () => const PdfToWordScreen(),
    ),
    _ToolDef(
      name: 'Word to PDF',
      description: 'Convert Word documents to PDF format',
      symbol: 'W',
      color: const Color(0xFF3b82f6),
      screenBuilder: () => const WordToPdfScreen(),
    ),
    _ToolDef(
      name: 'PDF to Images',
      description: 'Render PDF pages as PNG or JPEG images',
      symbol: 'I',
      color: const Color(0xFF22c55e),
      screenBuilder: () => const PdfToImagesScreen(),
    ),
    _ToolDef(
      name: 'Images to PDF',
      description: 'Combine images into a single PDF document',
      symbol: 'I',
      color: const Color(0xFFec4899),
      screenBuilder: () => const ImagesToPdfScreen(),
    ),
    _ToolDef(
      name: 'Sign / Annotate',
      description: 'Add signatures and text annotations to PDFs',
      symbol: 'S',
      color: const Color(0xFFf97316),
      screenBuilder: () => const SignAnnotateScreen(),
    ),
    _ToolDef(
      name: 'History',
      description: 'View your recent PDF operations',
      symbol: 'H',
      color: const Color(0xFF64748b),
      screenBuilder: () => const HistoryScreen(),
    ),
    _ToolDef(
      name: 'Help / FAQ',
      description: 'Frequently asked questions and tips',
      symbol: '~',
      color: const Color(0xFF475569),
      screenBuilder: () => const FaqScreen(),
    ),
    _ToolDef(
      name: 'Contributors',
      description: 'Meet the team behind PDF Merger',
      symbol: '\u2605',
      color: const Color(0xFF8b5cf6),
      screenBuilder: () => const ContributorsScreen(),
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return Scaffold(
      backgroundColor: c.background,
      body: Stack(
        children: [
          const ConstellationBackground(),
          SafeArea(
            child: Column(
              children: [
                const SizedBox(height: 40),
                // Header + theme toggle
                Stack(
                  alignment: Alignment.center,
                  children: [
                    Column(
                      children: [
                        Text(
                          'PDF Merger',
                          style: TextStyle(
                            color: c.textPrimary,
                            fontSize: 36,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 0.5,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Professional PDF Processing Suite',
                          style: TextStyle(
                            color: c.textSecondary,
                            fontSize: 16,
                            letterSpacing: 0.3,
                          ),
                        ),
                      ],
                    ),
                    Positioned(
                      right: 24,
                      top: 0,
                      child: ValueListenableBuilder<ThemeMode>(
                        valueListenable: themeNotifier,
                        builder: (_, mode, _) => IconButton(
                          icon: Icon(
                            mode == ThemeMode.dark
                                ? Icons.light_mode_rounded
                                : Icons.dark_mode_rounded,
                          ),
                          color: c.textSecondary,
                          tooltip: mode == ThemeMode.dark
                              ? 'Switch to light mode'
                              : 'Switch to dark mode',
                          onPressed: themeNotifier.toggle,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                // Privacy badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: const Color(0xFF22c55e).withAlpha(20),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF22c55e).withAlpha(60)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.lock_outline_rounded,
                          size: 14, color: Color(0xFF22c55e)),
                      SizedBox(width: 8),
                      Text(
                        '100% offline  |  Your files never leave your device  |  No uploads  |  No accounts  |  No tracking',
                        style: TextStyle(
                          color: Color(0xFF22c55e),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          letterSpacing: 0.2,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 36),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: GridView.builder(
                      gridDelegate:
                          const SliverGridDelegateWithMaxCrossAxisExtent(
                        maxCrossAxisExtent: 230,
                        mainAxisExtent: 148,
                        crossAxisSpacing: 14,
                        mainAxisSpacing: 14,
                      ),
                      itemCount: _tools.length,
                      itemBuilder: (context, index) {
                        final tool = _tools[index];
                        return ToolCard(
                          name: tool.name,
                          description: tool.description,
                          symbol: tool.symbol,
                          color: tool.color,
                          onTap: () => Navigator.of(context).push(
                            MaterialPageRoute(
                                builder: (_) => tool.screenBuilder()),
                          ),
                        );
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
