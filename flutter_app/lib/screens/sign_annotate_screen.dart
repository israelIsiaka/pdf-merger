import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/file_drop_zone.dart';
import '../widgets/progress_overlay.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

// Each draggable field handle definition
class _Handle {
  final String key;   // N, T, D, C, S
  final String label;
  final Color color;
  double x; // fraction 0..1
  double y; // fraction 0..1
  _Handle(this.key, this.label, this.color, this.x, this.y);
}

class SignAnnotateScreen extends StatefulWidget {
  const SignAnnotateScreen({super.key});

  @override
  State<SignAnnotateScreen> createState() => _SignAnnotateScreenState();
}

class _SignAnnotateScreenState extends State<SignAnnotateScreen> {
  String? _inputPath;
  final TextEditingController _outputCtrl = TextEditingController();
  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _titleCtrl = TextEditingController();
  final TextEditingController _dateCtrl = TextEditingController();
  final TextEditingController _customCtrl = TextEditingController();
  String? _sigImagePath;
  Uint8List? _sigBytes;
  String _frequency = 'first';
  int _fontSize = 12;
  bool _loading = false;

  Uint8List? _previewImage;
  bool _loadingPreview = false;

  // One handle per field in the same order used when building textItems
  final List<_Handle> _handles = [
    _Handle('N', 'Name',   const Color(0xFF1a73e8), 0.12, 0.78),
    _Handle('T', 'Title',  const Color(0xFF0f9d58), 0.12, 0.84),
    _Handle('D', 'Date',   const Color(0xFFf4b400), 0.12, 0.89),
    _Handle('C', 'Custom', const Color(0xFFea4335), 0.12, 0.94),
    _Handle('S', 'Sign',   const Color(0xFF34a853), 0.75, 0.88),
  ];

  static const List<String> _frequencies = ['first', 'last', 'all'];

  @override
  void initState() {
    super.initState();
    _dateCtrl.text = _todayString();
  }

  @override
  void dispose() {
    _outputCtrl.dispose();
    _nameCtrl.dispose();
    _titleCtrl.dispose();
    _dateCtrl.dispose();
    _customCtrl.dispose();
    super.dispose();
  }

  String _todayString() {
    final now = DateTime.now();
    return '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom, allowedExtensions: ['pdf'],
    );
    if (result != null && result.files.first.path != null) {
      final path = result.files.first.path!;
      setState(() {
        _inputPath = path;
        _previewImage = null;
      });
      _suggestOutput();
      _loadPreview(path);
    }
  }

  Future<void> _loadPreview(String path) async {
    setState(() => _loadingPreview = true);
    final bytes = await PdfService.renderPreview(path, targetWidth: 500);
    if (mounted) {
      setState(() {
        _previewImage = bytes;
        _loadingPreview = false;
      });
    }
  }

  void _suggestOutput() async {
    if (_outputCtrl.text.isNotEmpty) return;
    final docs = await getApplicationDocumentsDirectory();
    final baseName = p.basenameWithoutExtension(_inputPath ?? 'document');
    _outputCtrl.text = p.join(docs.path, '${baseName}_signed.pdf');
  }

  Future<void> _pickSignature() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom, allowedExtensions: ['png', 'jpg', 'jpeg'],
    );
    if (result != null && result.files.first.path != null) {
      final path = result.files.first.path!;
      final bytes = await File(path).readAsBytes();
      setState(() {
        _sigImagePath = path;
        _sigBytes = bytes;
      });
    }
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save annotated PDF as',
      fileName: '${p.basenameWithoutExtension(_inputPath ?? 'document')}_signed.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _apply() async {
    if (_inputPath == null || _outputCtrl.text.isEmpty) return;

    final controllers = [_nameCtrl, _titleCtrl, _dateCtrl, _customCtrl];
    final textItems = <Map<String, dynamic>>[];
    for (int i = 0; i < controllers.length; i++) {
      final text = controllers[i].text.trim();
      if (text.isNotEmpty) {
        textItems.add({
          'text': text,
          'x': _handles[i].x,
          'y': _handles[i].y,
        });
      }
    }

    if (textItems.isEmpty && _sigBytes == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Add at least one text field or a signature image.'),
      ));
      return;
    }

    setState(() => _loading = true);
    try {
      await PdfService.annotate(
        _inputPath!,
        _outputCtrl.text,
        textItems,
        _sigBytes,
        _handles[4].x,
        _handles[4].y,
        _fontSize,
        '#1a1a1a',
        _frequency,
      );
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Sign / Annotate',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Saved: ${p.basename(_outputCtrl.text)}'),
          backgroundColor: AppTheme.success,
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: AppTheme.error,
        ));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Sign / Annotate',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Applying annotations...',
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Left: controls
            Expanded(
              flex: 5,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    FileDropZone(
                      onFilesDropped: (paths) {
                        final pdfs = paths.where((p) => p.toLowerCase().endsWith('.pdf'));
                        if (pdfs.isNotEmpty) {
                          setState(() {
                            _inputPath = pdfs.first;
                            _previewImage = null;
                          });
                          _suggestOutput();
                          _loadPreview(pdfs.first);
                        }
                      },
                      label: 'Drop PDF here',
                      sublabel: 'or click to browse',
                    ),
                    const SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: _pickInput,
                      icon: const Icon(Icons.folder_open_rounded, size: 18),
                      label: const Text('Choose PDF'),
                      style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFf97316)),
                    ),
                    if (_inputPath != null) ...[
                      const SizedBox(height: 6),
                      Text(p.basename(_inputPath!),
                          style: const TextStyle(
                              color: AppTheme.textSecondary, fontSize: 12)),
                    ],
                    const SizedBox(height: 20),
                    const Text('Text Fields',
                        style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14)),
                    const SizedBox(height: 4),
                    const Text('Drag the coloured handles on the preview to reposition each field.',
                        style: TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
                    const SizedBox(height: 12),
                    _buildField(_nameCtrl,   'Name',        Icons.person_outline_rounded,   _handles[0]),
                    const SizedBox(height: 10),
                    _buildField(_titleCtrl,  'Title',       Icons.work_outline_rounded,     _handles[1]),
                    const SizedBox(height: 10),
                    _buildField(_dateCtrl,   'Date',        Icons.calendar_today_rounded,   _handles[2]),
                    const SizedBox(height: 10),
                    _buildField(_customCtrl, 'Custom text', Icons.edit_note_rounded,        _handles[3]),
                    const SizedBox(height: 20),
                    const Text('Signature Image (optional)',
                        style: TextStyle(
                            color: AppTheme.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14)),
                    const SizedBox(height: 8),
                    Row(children: [
                      OutlinedButton.icon(
                        onPressed: _pickSignature,
                        icon: const Icon(Icons.draw_rounded, size: 18),
                        label: const Text('Choose Image'),
                      ),
                      if (_sigImagePath != null) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(p.basename(_sigImagePath!),
                              style: const TextStyle(color: AppTheme.success, fontSize: 12),
                              overflow: TextOverflow.ellipsis),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close_rounded,
                              size: 16, color: AppTheme.textSecondary),
                          onPressed: () => setState(() {
                            _sigImagePath = null;
                            _sigBytes = null;
                          }),
                        ),
                      ],
                    ]),
                    const SizedBox(height: 20),
                    Row(children: [
                      Expanded(child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Font Size',
                              style: TextStyle(color: AppTheme.textPrimary,
                                  fontWeight: FontWeight.w600, fontSize: 14)),
                          const SizedBox(height: 4),
                          DropdownButton<int>(
                            value: _fontSize,
                            dropdownColor: AppTheme.cardBackground,
                            isExpanded: true,
                            underline: Container(height: 1, color: AppTheme.cardBorder),
                            style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                            items: [8, 10, 12, 14, 16, 18, 20, 24]
                                .map((s) => DropdownMenuItem(value: s, child: Text('$s pt')))
                                .toList(),
                            onChanged: (v) => setState(() => _fontSize = v ?? 12),
                          ),
                        ],
                      )),
                      const SizedBox(width: 16),
                      Expanded(child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Apply To',
                              style: TextStyle(color: AppTheme.textPrimary,
                                  fontWeight: FontWeight.w600, fontSize: 14)),
                          const SizedBox(height: 4),
                          DropdownButton<String>(
                            value: _frequency,
                            dropdownColor: AppTheme.cardBackground,
                            isExpanded: true,
                            underline: Container(height: 1, color: AppTheme.cardBorder),
                            style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                            items: _frequencies
                                .map((f) => DropdownMenuItem(
                                    value: f,
                                    child: Text(f[0].toUpperCase() + f.substring(1))))
                                .toList(),
                            onChanged: (v) => setState(() => _frequency = v ?? 'first'),
                          ),
                        ],
                      )),
                    ]),
                    const SizedBox(height: 20),
                    const Text('Output File',
                        style: TextStyle(color: AppTheme.textPrimary,
                            fontWeight: FontWeight.w600, fontSize: 14)),
                    const SizedBox(height: 8),
                    Row(children: [
                      Expanded(
                        child: TextField(
                          controller: _outputCtrl,
                          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                          decoration: const InputDecoration(
                            hintText: 'Choose output path...',
                            prefixIcon: Icon(Icons.save_outlined,
                                size: 18, color: AppTheme.textSecondary),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      OutlinedButton(onPressed: _browseOutput, child: const Text('Browse')),
                    ]),
                    const SizedBox(height: 28),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton.icon(
                        onPressed: _inputPath != null && _outputCtrl.text.isNotEmpty
                            ? _apply : null,
                        icon: const Icon(Icons.draw_rounded),
                        label: const Text('Apply Signature / Annotations'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFf97316),
                          disabledBackgroundColor: AppTheme.cardBorder,
                          disabledForegroundColor: AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Divider
            Container(width: 1, color: AppTheme.cardBorder),

            // Right: preview canvas
            Expanded(
              flex: 4,
              child: _buildPreviewPanel(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(TextEditingController ctrl, String label,
      IconData icon, _Handle handle) {
    return Row(children: [
      // Colour dot matching the handle colour
      Container(
        width: 10, height: 10,
        margin: const EdgeInsets.only(right: 8),
        decoration: BoxDecoration(color: handle.color, shape: BoxShape.circle),
      ),
      Expanded(
        child: TextField(
          controller: ctrl,
          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
          decoration: InputDecoration(
            labelText: label,
            prefixIcon: Icon(icon, size: 18, color: AppTheme.textSecondary),
          ),
          onChanged: (_) => setState(() {}),
        ),
      ),
    ]);
  }

  Widget _buildPreviewPanel() {
    return Container(
      color: const Color(0xFF060a12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            decoration: const BoxDecoration(
              border: Border(bottom: BorderSide(color: AppTheme.cardBorder)),
            ),
            child: const Row(
              children: [
                Icon(Icons.preview_rounded, size: 16, color: AppTheme.textSecondary),
                SizedBox(width: 8),
                Text('Preview — drag handles to reposition',
                    style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                        fontWeight: FontWeight.w500)),
              ],
            ),
          ),
          Expanded(
            child: _previewImage == null
                ? Center(
                    child: _loadingPreview
                        ? const CircularProgressIndicator()
                        : Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.picture_as_pdf_rounded,
                                  size: 48,
                                  color: AppTheme.textSecondary.withAlpha(60)),
                              const SizedBox(height: 12),
                              const Text('Select a PDF to preview',
                                  style: TextStyle(
                                      color: AppTheme.textSecondary, fontSize: 13)),
                            ],
                          ),
                  )
                : Padding(
                    padding: const EdgeInsets.all(16),
                    child: Center(
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final maxH = constraints.maxHeight;
                          final maxW = constraints.maxWidth;
                          // A4 ratio ~1.414
                          double w = maxW;
                          double h = w * 1.414;
                          if (h > maxH) {
                            h = maxH;
                            w = h / 1.414;
                          }
                          return SizedBox(
                            width: w,
                            height: h,
                            child: Stack(
                              children: [
                                // PDF page image
                                Positioned.fill(
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(4),
                                    child: Image.memory(_previewImage!, fit: BoxFit.fill),
                                  ),
                                ),
                                // Draggable handles
                                ..._buildHandles(w, h),
                              ],
                            ),
                          );
                        },
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildHandles(double w, double h) {
    final controllers = [_nameCtrl, _titleCtrl, _dateCtrl, _customCtrl, null];
    return List.generate(_handles.length, (i) {
      final handle = _handles[i];
      final isSig = i == 4;
      final text = isSig
          ? (_sigImagePath != null ? 'Sig' : null)
          : controllers[i]!.text.trim().isEmpty
              ? null
              : controllers[i]!.text.trim();
      if (text == null && !isSig) {
        // Field is empty — show ghost handle
      }

      const hSize = 28.0;
      final left = handle.x * w - hSize / 2;
      final top = handle.y * h - hSize / 2;

      return Positioned(
        left: left.clamp(0.0, w - hSize),
        top: top.clamp(0.0, h - hSize),
        child: GestureDetector(
          onPanUpdate: (details) {
            setState(() {
              handle.x = ((handle.x * w + details.delta.dx) / w).clamp(0.0, 1.0);
              handle.y = ((handle.y * h + details.delta.dy) / h).clamp(0.0, 1.0);
            });
          },
          child: Tooltip(
            message: isSig ? 'Signature position' : '${handle.label}: ${text ?? "(empty)"}',
            child: Container(
              width: hSize,
              height: hSize,
              decoration: BoxDecoration(
                color: handle.color.withAlpha(text != null || isSig ? 220 : 80),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white, width: 1.5),
                boxShadow: [
                  BoxShadow(
                      color: handle.color.withAlpha(120),
                      blurRadius: 6,
                      spreadRadius: 1),
                ],
              ),
              child: Center(
                child: Text(handle.key,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold)),
              ),
            ),
          ),
        ),
      );
    });
  }
}
