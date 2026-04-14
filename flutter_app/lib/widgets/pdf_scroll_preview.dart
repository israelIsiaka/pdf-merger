import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/pdf_service.dart';
import '../theme/app_theme.dart';

/// Callback that returns extra Stack children to overlay on a rendered page.
/// [pageIndex] is 0-based. [w] and [h] are the page's pixel dimensions in
/// the preview (NOT the PDF's physical dimensions).
typedef PageOverlayBuilder = List<Widget> Function(
    int pageIndex, double w, double h);

/// A scrollable list of rendered PDF pages with optional overlays.
/// Pages are loaded lazily as they scroll into view.
class PdfScrollPreview extends StatelessWidget {
  final String pdfPath;
  final int pageCount;

  /// Which pages get an overlay: 'all', 'first', 'last'
  final String frequency;

  /// Called to build overlay widgets for applicable pages.
  final PageOverlayBuilder? overlayBuilder;

  const PdfScrollPreview({
    super.key,
    required this.pdfPath,
    required this.pageCount,
    this.frequency = 'all',
    this.overlayBuilder,
  });

  bool _showOverlay(int idx) {
    switch (frequency) {
      case 'first':
        return idx == 0;
      case 'last':
        return idx == pageCount - 1;
      default:
        return true;
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return Container(
      color: c.previewBackground,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: pageCount,
        itemBuilder: (_, idx) => Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Page number badge
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  'Page ${idx + 1}',
                  style: TextStyle(
                    color: c.textSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              _PdfPageItem(
                pdfPath: pdfPath,
                pageIndex: idx,
                overlayWidgets:
                    (_showOverlay(idx) && overlayBuilder != null)
                        ? null // resolved inside _PdfPageItem after layout
                        : [],
                overlayBuilder:
                    (_showOverlay(idx)) ? overlayBuilder : null,
                cardBorder: c.cardBorder,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PdfPageItem extends StatefulWidget {
  final String pdfPath;
  final int pageIndex;
  final List<Widget>? overlayWidgets;
  final PageOverlayBuilder? overlayBuilder;
  final Color cardBorder;

  const _PdfPageItem({
    required this.pdfPath,
    required this.pageIndex,
    required this.overlayWidgets,
    required this.overlayBuilder,
    required this.cardBorder,
  });

  @override
  State<_PdfPageItem> createState() => _PdfPageItemState();
}

class _PdfPageItemState extends State<_PdfPageItem> {
  Uint8List? _bytes;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(_PdfPageItem old) {
    super.didUpdateWidget(old);
    if (old.pdfPath != widget.pdfPath ||
        old.pageIndex != widget.pageIndex) {
      setState(() {
        _bytes = null;
        _loading = true;
      });
      _load();
    }
  }

  Future<void> _load() async {
    final bytes = await PdfService.renderPreview(
      widget.pdfPath,
      pageIndex: widget.pageIndex,
      targetWidth: 600,
    );
    if (mounted) {
      setState(() {
        _bytes = bytes;
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return AspectRatio(
        aspectRatio: 0.707,
        child: Container(
          decoration: BoxDecoration(
            color: Colors.black12,
            borderRadius: BorderRadius.circular(4),
            border: Border.all(color: widget.cardBorder),
          ),
          child: const Center(child: CircularProgressIndicator()),
        ),
      );
    }
    if (_bytes == null) return const SizedBox.shrink();

    return LayoutBuilder(builder: (context, constraints) {
      final w = constraints.maxWidth;
      final h = w * 1.414; // A4 ratio
      final overlayChildren =
          widget.overlayBuilder?.call(widget.pageIndex, w, h) ?? [];
      return ClipRRect(
        borderRadius: BorderRadius.circular(4),
        child: SizedBox(
          width: w,
          height: h,
          child: Stack(
            fit: StackFit.expand,
            children: [
              Image.memory(_bytes!, fit: BoxFit.fill),
              ...overlayChildren,
            ],
          ),
        ),
      );
    });
  }
}
