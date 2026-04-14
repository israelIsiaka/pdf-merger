import 'dart:io';
import 'dart:typed_data';
import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/progress_overlay.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class WatermarkScreen extends StatefulWidget {
  const WatermarkScreen({super.key});

  @override
  State<WatermarkScreen> createState() => _WatermarkScreenState();
}

class _WatermarkScreenState extends State<WatermarkScreen> {
  final _inputCtrl  = TextEditingController();
  final _outputCtrl = TextEditingController();
  final _textCtrl   = TextEditingController(text: 'CONFIDENTIAL');
  final _colorCtrl  = TextEditingController(text: '#808080');

  // Watermark mode: 'text' or 'image'
  String _mode = 'text';
  String? _wmImagePath;
  Uint8List? _wmImageBytes;
  double _wmImageScale = 0.3;

  double _opacity  = 0.3;
  double _rotation = -45;
  String _position = 'center';
  String _frequency = 'all';
  bool   _loading  = false;

  // Preview state
  Uint8List? _previewImage;
  bool _loadingPreview = false;
  int  _currentPage = 0;
  int  _totalPages  = 1;

  static const _positions  = ['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'grid'];
  static const _frequencies = ['all', 'first', 'last'];

  @override
  void dispose() {
    _inputCtrl.dispose();
    _outputCtrl.dispose();
    _textCtrl.dispose();
    _colorCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['pdf']);
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      final total = await PdfService.getPreviewPageCount(path);
      setState(() {
        _inputCtrl.text = path;
        _previewImage   = null;
        _currentPage    = 0;
        _totalPages     = total;
      });
      final docs = await getApplicationDocumentsDirectory();
      _outputCtrl.text =
          p.join(docs.path, '${p.basenameWithoutExtension(path)}_watermarked.pdf');
      _loadPreview(path, 0);
    }
  }

  Future<void> _pickWmImage() async {
    final result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['png', 'jpg', 'jpeg']);
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      final bytes = await File(path).readAsBytes();
      setState(() {
        _wmImagePath  = path;
        _wmImageBytes = bytes;
      });
    }
  }

  Future<void> _loadPreview(String path, int page) async {
    setState(() => _loadingPreview = true);
    final bytes = await PdfService.renderPreview(path,
        targetWidth: 500, pageIndex: page);
    if (mounted) {
      setState(() {
        _previewImage   = bytes;
        _loadingPreview = false;
      });
    }
  }

  void _goToPage(int page) {
    if (_inputCtrl.text.isEmpty) return;
    final clamped = page.clamp(0, _totalPages - 1);
    setState(() => _currentPage = clamped);
    _loadPreview(_inputCtrl.text, clamped);
  }

  Future<void> _browseOutput() async {
    final r = await FilePicker.platform.saveFile(
        dialogTitle: 'Save watermarked PDF',
        fileName: 'watermarked.pdf',
        type: FileType.custom,
        allowedExtensions: ['pdf']);
    if (r != null) setState(() => _outputCtrl.text = r);
  }

  Future<void> _apply() async {
    if (_inputCtrl.text.isEmpty) {
      _snack('Select an input PDF.', error: true); return;
    }
    if (_outputCtrl.text.isEmpty) {
      _snack('Choose an output path.', error: true); return;
    }
    if (_mode == 'text' && _textCtrl.text.isEmpty) {
      _snack('Enter watermark text.', error: true); return;
    }
    if (_mode == 'image' && _wmImageBytes == null) {
      _snack('Choose a watermark image.', error: true); return;
    }

    setState(() => _loading = true);
    try {
      if (_mode == 'text') {
        await PdfService.addWatermark(
          _inputCtrl.text,
          _outputCtrl.text,
          _textCtrl.text,
          opacity:   _opacity,
          rotation:  _rotation,
          color:     _colorCtrl.text.isEmpty ? '#808080' : _colorCtrl.text,
          position:  _position,
          frequency: _frequency,
        );
      } else {
        await PdfService.addImageWatermark(
          _inputCtrl.text,
          _outputCtrl.text,
          _wmImageBytes!,
          opacity:   _opacity,
          rotation:  _rotation,
          position:  _position,
          frequency: _frequency,
          scale:     _wmImageScale,
        );
      }
      await HistoryService.addEntry(HistoryEntry(
          operation: 'Watermark PDF',
          outputPath: _outputCtrl.text,
          timestamp: DateTime.now()));
      _snack('Watermark applied successfully.', error: false);
    } catch (e) {
      _snack('Error: $e', error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _snack(String msg, {required bool error}) {
      final c = AppColors.of(context);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: error ? c.error : c.success));
  }

  Color get _previewColor {
    try {
      final hex = _colorCtrl.text.replaceAll('#', '');
      if (hex.length == 6) return Color(int.parse('FF$hex', radix: 16));
    } catch (_) {}
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'Add Watermark',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Applying watermark...',
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Left: controls ──────────────────────────────────────────
            Expanded(
              flex: 5,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('Input PDF'),
                    SizedBox(height: 8),
                    _filePicker(_inputCtrl, 'Select PDF...', _pickInput),
                    SizedBox(height: 20),

                    // Mode toggle
                    _label('Watermark Type'),
                    SizedBox(height: 8),
                    Row(children: [
                      _modeChip('text',  'Text',  Icons.text_fields_rounded),
                      SizedBox(width: 8),
                      _modeChip('image', 'Image', Icons.image_outlined),
                    ]),
                    SizedBox(height: 20),

                    // ── Text mode controls ──────────────────────────────
                    if (_mode == 'text') ...[
                      _label('Watermark Text'),
                      SizedBox(height: 8),
                      TextField(
                        controller: _textCtrl,
                        style: TextStyle(
                            color: c.textPrimary, fontSize: 13),
                        decoration:
                            InputDecoration(hintText: 'e.g. CONFIDENTIAL'),
                        onChanged: (_) => setState(() {}),
                      ),
                      SizedBox(height: 20),
                      Row(children: [
                        Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _label('Color (hex)'),
                            SizedBox(height: 8),
                            Row(children: [
                              Expanded(
                                child: TextField(
                                  controller: _colorCtrl,
                                  style: TextStyle(
                                      color: c.textPrimary, fontSize: 13),
                                  decoration: InputDecoration(
                                      hintText: '#808080'),
                                  onChanged: (_) => setState(() {}),
                                ),
                              ),
                              SizedBox(width: 10),
                              Container(
                                width: 36, height: 36,
                                decoration: BoxDecoration(
                                  color: _previewColor,
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: c.cardBorder),
                                ),
                              ),
                            ]),
                          ],
                        )),
                      ]),
                    ],

                    // ── Image mode controls ─────────────────────────────
                    if (_mode == 'image') ...[
                      _label('Watermark Image'),
                      SizedBox(height: 8),
                      Row(children: [
                        OutlinedButton.icon(
                          onPressed: _pickWmImage,
                          icon: Icon(Icons.image_outlined, size: 18),
                          label: Text('Choose Image'),
                        ),
                        if (_wmImagePath != null) ...[
                          SizedBox(width: 12),
                          Expanded(
                            child: Text(p.basename(_wmImagePath!),
                                style: TextStyle(
                                    color: c.success, fontSize: 12),
                                overflow: TextOverflow.ellipsis),
                          ),
                          IconButton(
                            icon: Icon(Icons.close_rounded,
                                size: 16, color: c.textSecondary),
                            onPressed: () => setState(() {
                              _wmImagePath  = null;
                              _wmImageBytes = null;
                            }),
                          ),
                        ],
                      ]),
                      SizedBox(height: 16),
                      _label('Image Scale: ${(_wmImageScale * 100).toStringAsFixed(0)}%'),
                      Slider(
                        value: _wmImageScale,
                        min: 0.05,
                        max: 0.8,
                        divisions: 15,
                        label: '${(_wmImageScale * 100).toStringAsFixed(0)}%',
                        onChanged: (v) => setState(() => _wmImageScale = v),
                      ),
                    ],

                    // ── Shared controls ─────────────────────────────────
                    SizedBox(height: 4),
                    _label('Opacity: ${_opacity.toStringAsFixed(2)}'),
                    Slider(
                      value: _opacity, min: 0.05, max: 0.95, divisions: 18,
                      label: _opacity.toStringAsFixed(2),
                      onChanged: (v) => setState(() => _opacity = v),
                    ),
                    _label('Rotation: ${_rotation.toStringAsFixed(0)}°'),
                    Slider(
                      value: _rotation, min: -90, max: 90, divisions: 36,
                      label: '${_rotation.toStringAsFixed(0)}°',
                      onChanged: (v) => setState(() => _rotation = v),
                    ),
                    SizedBox(height: 16),
                    Row(children: [
                      Expanded(child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _label('Position'),
                          SizedBox(height: 8),
                          DropdownButtonFormField<String>(
                            initialValue: _position,
                            dropdownColor: c.cardBackground,
                            style: TextStyle(
                                color: c.textPrimary, fontSize: 13),
                            decoration: InputDecoration(),
                            items: _positions
                                .map((pos) => DropdownMenuItem(
                                    value: pos, child: Text(pos)))
                                .toList(),
                            onChanged: (v) => setState(() => _position = v!),
                          ),
                        ],
                      )),
                    ]),
                    SizedBox(height: 20),
                    _label('Apply to pages'),
                    SizedBox(height: 8),
                    Row(
                      children: _frequencies.map((f) => Padding(
                        padding: EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(f[0].toUpperCase() + f.substring(1)),
                          selected: _frequency == f,
                          onSelected: (_) => setState(() => _frequency = f),
                          selectedColor: c.primary.withAlpha(60),
                          labelStyle: TextStyle(
                            color: _frequency == f
                                ? c.primary
                                : c.textSecondary,
                            fontSize: 13,
                          ),
                          backgroundColor: c.cardBackground,
                          side: BorderSide(
                              color: _frequency == f
                                  ? c.primary
                                  : c.cardBorder),
                        ),
                      )).toList(),
                    ),
                    SizedBox(height: 20),
                    _label('Output File'),
                    SizedBox(height: 8),
                    Row(children: [
                      Expanded(
                        child: TextField(
                          controller: _outputCtrl,
                          style: TextStyle(
                              color: c.textPrimary, fontSize: 13),
                          decoration: InputDecoration(
                            hintText: 'Output file path...',
                            prefixIcon: Icon(Icons.save_outlined,
                                size: 18, color: c.textSecondary),
                          ),
                        ),
                      ),
                      SizedBox(width: 10),
                      OutlinedButton(
                          onPressed: _browseOutput,
                          child: Text('Browse')),
                    ]),
                    SizedBox(height: 28),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton.icon(
                        onPressed: _apply,
                        icon: Icon(Icons.water_drop_outlined),
                        label: Text('Apply Watermark'),
                        style: ElevatedButton.styleFrom(
                            backgroundColor: Color(0xFF06b6d4)),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            Container(width: 1, color: c.cardBorder),

            // ── Right: preview ───────────────────────────────────────────
            Expanded(
              flex: 4,
              child: _buildPreviewPanel(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _modeChip(String value, String label, IconData icon) {
      final c = AppColors.of(context);
    final selected = _mode == value;
    return GestureDetector(
      onTap: () => setState(() => _mode = value),
      child: AnimatedContainer(
        duration: Duration(milliseconds: 150),
        padding: EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: selected
              ? Color(0xFF06b6d4).withAlpha(25)
              : c.cardBackground,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: selected ? Color(0xFF06b6d4) : c.cardBorder,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(icon,
              size: 16,
              color: selected
                  ? Color(0xFF06b6d4)
                  : c.textSecondary),
          SizedBox(width: 6),
          Text(label,
              style: TextStyle(
                  color: selected
                      ? Color(0xFF06b6d4)
                      : c.textSecondary,
                  fontSize: 13,
                  fontWeight:
                      selected ? FontWeight.w600 : FontWeight.normal)),
        ]),
      ),
    );
  }

  Widget _buildPreviewPanel() {
      final c = AppColors.of(context);
    return Container(
      color: Color(0xFF060a12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with page nav
          Container(
            padding:
                EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              border:
                  Border(bottom: BorderSide(color: c.cardBorder)),
            ),
            child: Row(
              children: [
                Icon(Icons.preview_rounded,
                    size: 16, color: c.textSecondary),
                SizedBox(width: 8),
                Expanded(
                  child: Text('Preview',
                      style: TextStyle(
                          color: c.textSecondary,
                          fontSize: 13,
                          fontWeight: FontWeight.w500)),
                ),
                if (_totalPages > 1) ...[
                  IconButton(
                    icon: Icon(Icons.chevron_left_rounded, size: 20),
                    color: _currentPage > 0
                        ? c.textPrimary
                        : c.textSecondary,
                    padding: EdgeInsets.zero,
                    constraints: BoxConstraints(),
                    onPressed: _currentPage > 0
                        ? () => _goToPage(_currentPage - 1)
                        : null,
                  ),
                  SizedBox(width: 6),
                  Text('${_currentPage + 1} / $_totalPages',
                      style: TextStyle(
                          color: c.textPrimary,
                          fontSize: 12,
                          fontWeight: FontWeight.w500)),
                  SizedBox(width: 6),
                  IconButton(
                    icon: Icon(Icons.chevron_right_rounded, size: 20),
                    color: _currentPage < _totalPages - 1
                        ? c.textPrimary
                        : c.textSecondary,
                    padding: EdgeInsets.zero,
                    constraints: BoxConstraints(),
                    onPressed: _currentPage < _totalPages - 1
                        ? () => _goToPage(_currentPage + 1)
                        : null,
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: _previewImage == null
                ? Center(
                    child: _loadingPreview
                        ? CircularProgressIndicator()
                        : Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.picture_as_pdf_rounded,
                                  size: 48,
                                  color:
                                      c.textSecondary.withAlpha(60)),
                              SizedBox(height: 12),
                              Text('Select a PDF to preview',
                                  style: TextStyle(
                                      color: c.textSecondary,
                                      fontSize: 13)),
                            ],
                          ),
                  )
                : Stack(
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: LayoutBuilder(
                          builder: (context, constraints) {
                            return Center(
                              child: AspectRatio(
                                aspectRatio: 0.707,
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(4),
                                  child: Stack(
                                    fit: StackFit.expand,
                                    children: [
                                      Image.memory(_previewImage!,
                                          fit: BoxFit.fill),
                                      // Text watermark overlay
                                      if (_mode == 'text' &&
                                          _textCtrl.text.isNotEmpty)
                                        IgnorePointer(
                                          child: CustomPaint(
                                            painter: _WatermarkPainter(
                                              text:     _textCtrl.text,
                                              opacity:  _opacity,
                                              rotation: _rotation,
                                              color:    _previewColor,
                                              position: _position,
                                            ),
                                          ),
                                        ),
                                      // Image watermark overlay
                                      if (_mode == 'image' &&
                                          _wmImageBytes != null)
                                        IgnorePointer(
                                          child: CustomPaint(
                                            painter: _ImageWatermarkPainter(
                                              imageBytes: _wmImageBytes!,
                                              opacity:    _opacity,
                                              rotation:   _rotation,
                                              position:   _position,
                                              scale:      _wmImageScale,
                                            ),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                      if (_loadingPreview)
                        Container(
                          color: Colors.black45,
                          child: Center(
                              child: CircularProgressIndicator()),
                        ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _label(String t) {
    final c = AppColors.of(context);
    return Text(t,
        style: TextStyle(
            color: c.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 14));
  }

  Widget _filePicker(TextEditingController ctrl, String hint,
      VoidCallback onBrowse) {
    final c = AppColors.of(context);
    return Row(children: [
      Expanded(
        child: TextField(
          controller: ctrl,
          readOnly: true,
          style:
              TextStyle(color: c.textPrimary, fontSize: 13),
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: Icon(Icons.picture_as_pdf_rounded,
                size: 18, color: c.textSecondary),
          ),
        ),
      ),
      SizedBox(width: 10),
      OutlinedButton(onPressed: onBrowse, child: Text('Browse')),
    ]);
  }
}

// ── Text watermark preview painter ─────────────────────────────────────────
class _WatermarkPainter extends CustomPainter {
  final String text;
  final double opacity;
  final double rotation;
  final Color  color;
  final String position;

  const _WatermarkPainter({
    required this.text,
    required this.opacity,
    required this.rotation,
    required this.color,
    required this.position,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final tp = TextPainter(
      text: TextSpan(
        text: text,
        style: TextStyle(
          color: color.withAlpha((opacity * 255).round()),
          fontSize: size.width * 0.12,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();

    final tw  = tp.width;
    final th  = tp.height;
    final rad = rotation * math.pi / 180;

    if (position == 'grid') {
      for (double x = -size.width; x < size.width * 2; x += tw + 40) {
        for (double y = -size.height; y < size.height * 2; y += th + 40) {
          canvas.save();
          canvas.translate(x + size.width / 2, y + size.height / 2);
          canvas.rotate(rad);
          tp.paint(canvas, Offset(-tw / 2, -th / 2));
          canvas.restore();
        }
      }
    } else {
      final cx = _cx(size.width, tw);
      final cy = _cy(size.height, th);
      canvas.save();
      canvas.translate(cx, cy);
      canvas.rotate(rad);
      tp.paint(canvas, Offset(-tw / 2, -th / 2));
      canvas.restore();
    }
  }

  double _cx(double pw, double tw) {
    switch (position) {
      case 'top-left':    return tw / 2 + pw * 0.05;
      case 'top-right':   return pw - tw / 2 - pw * 0.05;
      case 'bottom-left': return tw / 2 + pw * 0.05;
      case 'bottom-right':return pw - tw / 2 - pw * 0.05;
      default:            return pw / 2;
    }
  }

  double _cy(double ph, double th) {
    switch (position) {
      case 'top-left':
      case 'top-right':    return th / 2 + ph * 0.05;
      case 'bottom-left':
      case 'bottom-right': return ph - th / 2 - ph * 0.05;
      default:             return ph / 2;
    }
  }

  @override
  bool shouldRepaint(_WatermarkPainter old) =>
      old.text != text || old.opacity != opacity ||
      old.rotation != rotation || old.color != color ||
      old.position != position;
}

// ── Image watermark preview painter ────────────────────────────────────────
class _ImageWatermarkPainter extends CustomPainter {
  final Uint8List imageBytes;
  final double opacity;
  final double rotation;
  final String position;
  final double scale;

  _ImageWatermarkPainter({
    required this.imageBytes,
    required this.opacity,
    required this.rotation,
    required this.position,
    required this.scale,
  });

  // Decoded image cached after first decode
  ui.Image? _cached;

  @override
  void paint(Canvas canvas, Size size) {
    if (_cached == null) {
      // Decode asynchronously and repaint once ready
      _decodeImage().then((_) {});
      return;
    }
    final img = _cached!;
    final imgW = img.width  * scale * (size.width / 500);
    final imgH = img.height * scale * (size.width / 500);
    final rad  = rotation * math.pi / 180;
    final paint = Paint()..color = Colors.white.withAlpha((opacity * 255).round());

    void drawAt(double cx, double cy) {
      canvas.save();
      canvas.translate(cx, cy);
      canvas.rotate(rad);
      canvas.drawImageRect(
        img,
        Rect.fromLTWH(0, 0, img.width.toDouble(), img.height.toDouble()),
        Rect.fromLTWH(-imgW / 2, -imgH / 2, imgW, imgH),
        paint,
      );
      canvas.restore();
    }

    if (position == 'grid') {
      for (double x = -size.width; x < size.width * 2; x += imgW + 40) {
        for (double y = -size.height; y < size.height * 2; y += imgH + 40) {
          drawAt(x + size.width / 2, y + size.height / 2);
        }
      }
    } else {
      drawAt(_cx(size.width, imgW), _cy(size.height, imgH));
    }
  }

  Future<void> _decodeImage() async {
    final codec = await ui.instantiateImageCodec(imageBytes);
    final frame = await codec.getNextFrame();
    _cached = frame.image;
  }

  double _cx(double pw, double imgW) {
    switch (position) {
      case 'top-left':     return imgW / 2 + pw * 0.05;
      case 'top-right':    return pw - imgW / 2 - pw * 0.05;
      case 'bottom-left':  return imgW / 2 + pw * 0.05;
      case 'bottom-right': return pw - imgW / 2 - pw * 0.05;
      default:             return pw / 2;
    }
  }

  double _cy(double ph, double imgH) {
    switch (position) {
      case 'top-left':
      case 'top-right':    return imgH / 2 + ph * 0.05;
      case 'bottom-left':
      case 'bottom-right': return ph - imgH / 2 - ph * 0.05;
      default:             return ph / 2;
    }
  }

  @override
  bool shouldRepaint(_ImageWatermarkPainter old) =>
      old.imageBytes != imageBytes || old.opacity != opacity ||
      old.rotation != rotation || old.position != position ||
      old.scale != scale;
}
