import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';

class FaqScreen extends StatelessWidget {
  const FaqScreen({super.key});

  static const List<_FaqItem> _items = [
    _FaqItem(
      question: 'Is PDF Merger completely free?',
      answer:
          'Yes. PDF Merger is 100% free and open source. There are no subscriptions, no ads, and no hidden charges.',
    ),
    _FaqItem(
      question: 'Do my files leave my device?',
      answer:
          'Never. Every operation runs locally on your machine. No files are uploaded to any server. No internet connection is required.',
    ),
    _FaqItem(
      question: 'How do I merge PDF files?',
      answer:
          'Open the Merge PDFs tool from the home screen. Add your PDFs using the button or drag-and-drop, reorder them if needed, choose an output path, then click Merge.',
    ),
    _FaqItem(
      question: 'How do I password-protect a PDF?',
      answer:
          'Use the Protect PDF tool. Enter a user password (required to open) and an optional owner password (required to edit). The file is encrypted with AES-256.',
    ),
    _FaqItem(
      question: 'What does "Peep PDF" do?',
      answer:
          'Peep PDF removes password protection from a PDF you already have access to. Provide the password, and a new unlocked copy is saved.',
    ),
    _FaqItem(
      question: 'How do I convert PDF to Word or Word to PDF?',
      answer:
          'These tools use LibreOffice for conversion. Install LibreOffice on your system (free at libreoffice.org), then use the PDF to Word or Word to PDF tools.',
    ),
    _FaqItem(
      question: 'How do I split a PDF?',
      answer:
          'Open Split PDF, choose your file, then enter page ranges like "1-3, 5, 7-10". Each range is saved as a separate file in your chosen output folder.',
    ),
    _FaqItem(
      question: 'Can I add a watermark to every page?',
      answer:
          'Yes. The Watermark tool lets you add text with custom opacity, rotation, color, and position. Use "Grid" placement for a repeating tile pattern.',
    ),
    _FaqItem(
      question: 'What image formats are supported for Images to PDF?',
      answer:
          'JPG, JPEG, PNG, BMP, GIF, and TIFF are all supported. Images are scaled to fit A4 proportionally.',
    ),
    _FaqItem(
      question: 'How do I add a signature to a PDF?',
      answer:
          'Use Sign / Annotate. Fill in name, title, date, or custom text, and optionally attach a signature image (PNG or JPG). Choose which pages to apply to, then click Apply.',
    ),
    _FaqItem(
      question: 'Where are output files saved by default?',
      answer:
          'By default, output files are suggested in your Documents folder. You can always change the path using the Browse button before processing.',
    ),
    _FaqItem(
      question: 'Can I reorder PDF pages?',
      answer:
          'You can reorder files before merging using drag-and-drop in the Merge tool. Per-page reordering within a single PDF is on the roadmap.',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Help / FAQ',
      body: ListView.separated(
        padding: const EdgeInsets.all(20),
        itemCount: _items.length,
        separatorBuilder: (_, __) => const SizedBox(height: 8),
        itemBuilder: (context, index) => _FaqCard(item: _items[index]),
      ),
    );
  }
}

class _FaqItem {
  final String question;
  final String answer;
  const _FaqItem({required this.question, required this.answer});
}

class _FaqCard extends StatefulWidget {
  final _FaqItem item;
  const _FaqCard({required this.item});

  @override
  State<_FaqCard> createState() => _FaqCardState();
}

class _FaqCardState extends State<_FaqCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      decoration: BoxDecoration(
        color: AppTheme.cardBackground,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: _expanded
              ? AppTheme.primary.withAlpha(80)
              : AppTheme.cardBorder,
        ),
      ),
      child: InkWell(
        onTap: () => setState(() => _expanded = !_expanded),
        borderRadius: BorderRadius.circular(10),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.item.question,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up_rounded
                        : Icons.keyboard_arrow_down_rounded,
                    color: AppTheme.textSecondary,
                    size: 20,
                  ),
                ],
              ),
              if (_expanded) ...[
                const SizedBox(height: 10),
                const Divider(height: 1),
                const SizedBox(height: 10),
                Text(
                  widget.item.answer,
                  style: const TextStyle(
                    color: AppTheme.textSecondary,
                    fontSize: 13,
                    height: 1.6,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
