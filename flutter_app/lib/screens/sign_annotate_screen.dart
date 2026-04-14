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

class _Handle {
  final String key;
  final String label;
  final Color color;
  double x;
  double y;
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
  int _currentPage = 0;
  int _totalPages = 1;

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
      final total = await PdfService.getPreviewPageCount(path);
      setState(() {
        _inputPath = path;
        _previewImage = null;
        _currentPage = 0;
        _totalPages = total;
      });
      _suggestOutput();
      _loadPreview(path, 0);
    }
  }

  Future<void> _loadPreview(String path, int page) async {
    setState(() => _loadingPreview = true);
    final bytes = await PdfService.renderPreview(path,
        targetWidth: 500, pageIndex: page);
    if (mounted) {
      setState(() {
        _previewImage = bytes;
        _loadingPreview = false;
      });
    }
  }

  void _goToPage(int page) {
    if (_inputPath == null) return;
    final clamped = page.clamp(0, _totalPages - 1);
    setState(() => _currentPage = clamped);
    _loadPreview(_inputPath!, clamped);
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
      final c = AppColors.of(context);
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
          backgroundColor: c.success,
        ));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Error: $e'),
          backgroundColor: c.error,
        ));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
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
                      onFilesDropped: (paths) async {
                        final pdfs = paths
                            .where((p) => p.toLowerCase().endsWith('.pdf'));
                        if (pdfs.isNotEmpty) {
                          final path = pdfs.first;
                          final total =
                              await PdfService.getPreviewPageCount(path);
                          setState(() {
                            _inputPath = path;
                            _previewImage = null;
                            _currentPage = 0;
                            _totalPages = total;
                          });
                          _suggestOutput();
                          _loadPreview(path, 0);
                        }
                      },
                      label: 'Drop PDF here',
                      sublabel: 'or click to browse',
                    ),
                    SizedBox(height: 12),
                    ElevatedButton.icon(
                      onPressed: _pickInput,
                      icon: Icon(Icons.folder_open_rounded, size: 18),
                      label: Text('Choose PDF'),
                      style: ElevatedButton.styleFrom(
                          backgroundColor: Color(0xFFf97316)),
                    ),
                    if (_inputPath != null) ...[
                      SizedBox(height: 6),
                      Text(p.basename(_inputPath!),
                          style: TextStyle(
                              color: c.textSecondary, fontSize: 12)),
                    ],
                    SizedBox(height: 20),
                    Text('Text Fields',
                        style: TextStyle(
                            color: c.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14)),
                    SizedBox(height: 4),
                    Text(
                        'Drag the coloured handles on the preview to reposition.',
                        style: TextStyle(
                            color: c.textSecondary, fontSize: 12)),
                    SizedBox(height: 12),
                    _buildField(_nameCtrl, 'Name',
                        Icons.person_outline_rounded, _handles[0]),
                    SizedBox(height: 10),
                    _buildField(_titleCtrl, 'Title',
                        Icons.work_outline_rounded, _handles[1]),
                    SizedBox(height: 10),
                    _buildField(_dateCtrl, 'Date',
                        Icons.calendar_today_rounded, _handles[2]),
                    SizedBox(height: 10),
                    _buildField(_customCtrl, 'Custom text',
                        Icons.edit_note_rounded, _handles[3]),
                    SizedBox(height: 20),
                    Text('Signature Image (optional)',
                        style: TextStyle(
                            color: c.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14)),
                    SizedBox(height: 8),
                    Row(children: [
                      OutlinedButton.icon(
                        onPressed: _pickSignature,
                        icon: Icon(Icons.draw_rounded, size: 18),
                        label: Text('Choose Image'),
                      ),
                      if (_sigImagePath != null) ...[
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(p.basename(_sigImagePath!),
                              style: TextStyle(
                                  color: c.success, fontSize: 12),
                              overflow: TextOverflow.ellipsis),
                        ),
                        IconButton(
                          icon: Icon(Icons.close_rounded,
                              size: 16, color: c.textSecondary),
                          onPressed: () => setState(() {
                            _sigImagePath = null;
                            _sigBytes = null;
                          }),
                        ),
                      ],
                    ]),
                    SizedBox(height: 20),
                    Row(children: [
                      Expanded(
                          child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Font Size',
                              style: TextStyle(
                                  color: c.textPrimary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14)),
                          SizedBox(height: 4),
                          DropdownButton<int>(
                            value: _fontSize,
                            dropdownColor: c.cardBackground,
                            isExpanded: true,
                            underline: Container(
                                height: 1, color: c.cardBorder),
                            style: TextStyle(
                                color: c.textPrimary, fontSize: 13),
                            items: [8, 10, 12, 14, 16, 18, 20, 24]
                                .map((s) => DropdownMenuItem(
                                    value: s, child: Text('$s pt')))
                                .toList(),
                            onChanged: (v) =>
                                setState(() => _fontSize = v ?? 12),
                          ),
                        ],
                      )),
                      SizedBox(width: 16),
                      Expanded(
                          child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Apply To',
                              style: TextStyle(
                                  color: c.textPrimary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 14)),
                          SizedBox(height: 4),
                          DropdownButton<String>(
                            value: _frequency,
                            dropdownColor: c.cardBackground,
                            isExpanded: true,
                            underline: Container(
                                height: 1, color: c.cardBorder),
                            style: TextStyle(
                                color: c.textPrimary, fontSize: 13),
                            items: _frequencies
                                .map((f) => DropdownMenuItem(
                                    value: f,
                                    child: Text(f[0].toUpperCase() +
                                        f.substring(1))))
                                .toList(),
                            onChanged: (v) =>
                                setState(() => _frequency = v ?? 'first'),
                          ),
                        ],
                      )),
                    ]),
                    SizedBox(height: 20),
                    Text('Output File',
                        style: TextStyle(
                            color: c.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 14)),
                    SizedBox(height: 8),
                    Row(children: [
                      Expanded(
                        child: TextField(
                          controller: _outputCtrl,
                          style: TextStyle(
                              color: c.textPrimary, fontSize: 13),
                          decoration: InputDecoration(
                            hintText: 'Choose output path...',
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
                        onPressed:
                            _inputPath != null && _outputCtrl.text.isNotEmpty
                                ? _apply
                                : null,
                        icon: Icon(Icons.draw_rounded),
                        label: Text('Apply Signature / Annotations'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Color(0xFFf97316),
                          disabledBackgroundColor: c.cardBorder,
                          disabledForegroundColor: c.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            Container(width: 1, color: c.cardBorder),

            // Right: preview
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
    final c = AppColors.of(context);
    return Row(children: [
      Container(
        width: 10,
        height: 10,
        margin: EdgeInsets.only(right: 8),
        decoration:
            BoxDecoration(color: handle.color, shape: BoxShape.circle),
      ),
      Expanded(
        child: TextField(
          controller: ctrl,
          style:
              TextStyle(color: c.textPrimary, fontSize: 13),
          decoration: InputDecoration(
            labelText: label,
            prefixIcon:
                Icon(icon, size: 18, color: c.textSecondary),
          ),
          onChanged: (_) => setState(() {}),
        ),
      ),
    ]);
  }

  Widget _buildPreviewPanel() {
      final c = AppColors.of(context);
    return Container(
      color: Color(0xFF060a12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with page navigation
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
                  child: Text('Preview — drag handles to reposition',
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
                    onPressed:
                        _currentPage > 0 ? () => _goToPage(_currentPage - 1) : null,
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
                        child: Center(
                          child: LayoutBuilder(
                            builder: (context, constraints) {
                              final maxH = constraints.maxHeight;
                              final maxW = constraints.maxWidth;
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
                                    Positioned.fill(
                                      child: ClipRRect(
                                        borderRadius:
                                            BorderRadius.circular(4),
                                        child: Image.memory(_previewImage!,
                                            fit: BoxFit.fill),
                                      ),
                                    ),
                                    ..._buildHandles(w, h),
                                  ],
                                ),
                              );
                            },
                          ),
                        ),
                      ),
                      // Loading spinner overlay while flipping pages
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

  List<Widget> _buildHandles(double w, double h) {
      final c = AppColors.of(context);
    final controllers = [_nameCtrl, _titleCtrl, _dateCtrl, _customCtrl, null];
    return List.generate(_handles.length, (i) {
      final handle = _handles[i];
      final isSig = i == 4;
      final fieldText = isSig
          ? (_sigImagePath != null ? p.basename(_sigImagePath!) : null)
          : controllers[i]!.text.trim().isEmpty
              ? null
              : controllers[i]!.text.trim();
      final hasContent = fieldText != null;

      const circleSize = 24.0;
      final cx = (handle.x * w).clamp(circleSize / 2, w - circleSize / 2);
      final cy = (handle.y * h).clamp(circleSize / 2, h - circleSize / 2);

      // Label text: value if filled, else field name dimmed
      final labelText = hasContent ? fieldText : handle.label;

      return Positioned(
        left: cx - circleSize / 2,
        top: cy - circleSize / 2,
        child: GestureDetector(
          onPanUpdate: (details) {
            setState(() {
              handle.x =
                  ((handle.x * w + details.delta.dx) / w).clamp(0.0, 1.0);
              handle.y =
                  ((handle.y * h + details.delta.dy) / h).clamp(0.0, 1.0);
            });
          },
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              // Drag circle
              Container(
                width: circleSize,
                height: circleSize,
                decoration: BoxDecoration(
                  color: handle.color
                      .withAlpha(hasContent ? 230 : 100),
                  shape: BoxShape.circle,
                  border:
                      Border.all(color: Colors.white, width: 1.5),
                  boxShadow: [
                    BoxShadow(
                        color: handle.color.withAlpha(140),
                        blurRadius: 6,
                        spreadRadius: 1),
                  ],
                ),
                child: Center(
                  child: Text(handle.key,
                      style: TextStyle(
                          color: Colors.white,
                          fontSize: 10,
                          fontWeight: FontWeight.bold)),
                ),
              ),
              SizedBox(width: 4),
              // Visible label pill
              Container(
                constraints: BoxConstraints(maxWidth: 110),
                padding: EdgeInsets.symmetric(
                    horizontal: 6, vertical: 3),
                decoration: BoxDecoration(
                  color: Color(0xFF0d1117).withAlpha(210),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                      color: handle.color
                          .withAlpha(hasContent ? 180 : 60),
                      width: 1),
                ),
                child: Text(
                  labelText,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: hasContent
                        ? Colors.white
                        : c.textSecondary,
                    fontSize: 10,
                    fontWeight: hasContent
                        ? FontWeight.w500
                        : FontWeight.normal,
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    });
  }
}
