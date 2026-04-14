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
  String _color = '#1a1a1a';
  bool _loading = false;

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
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null && result.files.first.path != null) {
      setState(() => _inputPath = result.files.first.path);
      _suggestOutput();
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
      type: FileType.custom,
      allowedExtensions: ['png', 'jpg', 'jpeg'],
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

    final textItems = <Map<String, dynamic>>[];
    void addItem(String text, double x, double y) {
      if (text.isNotEmpty) textItems.add({'text': text, 'x': x, 'y': y});
    }

    addItem(_nameCtrl.text.trim(), 0.12, 0.78);
    addItem(_titleCtrl.text.trim(), 0.12, 0.84);
    addItem(_dateCtrl.text.trim(), 0.12, 0.89);
    addItem(_customCtrl.text.trim(), 0.12, 0.94);

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
        0.75,
        0.88,
        _fontSize,
        _color,
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
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FileDropZone(
                onFilesDropped: (paths) {
                  final pdfs =
                      paths.where((p) => p.toLowerCase().endsWith('.pdf'));
                  if (pdfs.isNotEmpty) {
                    setState(() => _inputPath = pdfs.first);
                    _suggestOutput();
                  }
                },
                label: 'Drop PDF here',
                sublabel: 'or click to browse',
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _pickInput,
                icon: const Icon(Icons.folder_open_rounded, size: 18),
                label: const Text('Choose PDF'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFFf97316)),
              ),
              if (_inputPath != null) ...[
                const SizedBox(height: 8),
                Text(p.basename(_inputPath!),
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 12)),
              ],
              const SizedBox(height: 24),
              const Text('Text Fields',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 12),
              _buildTextField(_nameCtrl, 'Name', Icons.person_outline_rounded),
              const SizedBox(height: 10),
              _buildTextField(_titleCtrl, 'Title / Position',
                  Icons.work_outline_rounded),
              const SizedBox(height: 10),
              _buildTextField(_dateCtrl, 'Date', Icons.calendar_today_rounded),
              const SizedBox(height: 10),
              _buildTextField(_customCtrl, 'Custom text',
                  Icons.edit_note_rounded),
              const SizedBox(height: 20),
              const Text('Signature Image (optional)',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 8),
              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: _pickSignature,
                    icon: const Icon(Icons.draw_rounded, size: 18),
                    label: const Text('Choose Image'),
                  ),
                  if (_sigImagePath != null) ...[
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        p.basename(_sigImagePath!),
                        style: const TextStyle(
                            color: AppTheme.success, fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close_rounded,
                          size: 16, color: AppTheme.textSecondary),
                      onPressed: () =>
                          setState(() {
                            _sigImagePath = null;
                            _sigBytes = null;
                          }),
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Font Size',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.w600,
                                fontSize: 14)),
                        const SizedBox(height: 4),
                        DropdownButton<int>(
                          value: _fontSize,
                          dropdownColor: AppTheme.cardBackground,
                          style: const TextStyle(
                              color: AppTheme.textPrimary, fontSize: 13),
                          isExpanded: true,
                          underline: Container(height: 1, color: AppTheme.cardBorder),
                          items: [8, 10, 12, 14, 16, 18, 20, 24]
                              .map((s) => DropdownMenuItem(
                                    value: s,
                                    child: Text('$s pt'),
                                  ))
                              .toList(),
                          onChanged: (v) =>
                              setState(() => _fontSize = v ?? 12),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Apply To',
                            style: TextStyle(
                                color: AppTheme.textPrimary,
                                fontWeight: FontWeight.w600,
                                fontSize: 14)),
                        const SizedBox(height: 4),
                        DropdownButton<String>(
                          value: _frequency,
                          dropdownColor: AppTheme.cardBackground,
                          style: const TextStyle(
                              color: AppTheme.textPrimary, fontSize: 13),
                          isExpanded: true,
                          underline: Container(height: 1, color: AppTheme.cardBorder),
                          items: _frequencies
                              .map((f) => DropdownMenuItem(
                                    value: f,
                                    child: Text(f[0].toUpperCase() +
                                        f.substring(1)),
                                  ))
                              .toList(),
                          onChanged: (v) =>
                              setState(() => _frequency = v ?? 'first'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text('Output File',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _outputCtrl,
                      style: const TextStyle(
                          color: AppTheme.textPrimary, fontSize: 13),
                      decoration: const InputDecoration(
                        hintText: 'Choose output path...',
                        prefixIcon: Icon(Icons.save_outlined,
                            size: 18, color: AppTheme.textSecondary),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  OutlinedButton(
                      onPressed: _browseOutput, child: const Text('Browse')),
                ],
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _inputPath != null && _outputCtrl.text.isNotEmpty
                      ? _apply
                      : null,
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
    );
  }

  Widget _buildTextField(
      TextEditingController ctrl, String label, IconData icon) {
    return TextField(
      controller: ctrl,
      style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 18, color: AppTheme.textSecondary),
      ),
    );
  }
}
