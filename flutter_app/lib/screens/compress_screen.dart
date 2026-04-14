import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/progress_overlay.dart';
import '../widgets/custom_button.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class CompressScreen extends StatefulWidget {
  const CompressScreen({super.key});

  @override
  State<CompressScreen> createState() => _CompressScreenState();
}

class _CompressScreenState extends State<CompressScreen> {
  final TextEditingController _inputCtrl = TextEditingController();
  final TextEditingController _outputCtrl = TextEditingController();
  bool _loading = false;
  int? _beforeBytes;
  int? _afterBytes;

  @override
  void dispose() {
    _inputCtrl.dispose();
    _outputCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      setState(() {
        _inputCtrl.text = path;
        _beforeBytes = File(path).lengthSync();
        _afterBytes = null;
      });
      final docs = await getApplicationDocumentsDirectory();
      final base = p.basenameWithoutExtension(path);
      _outputCtrl.text = p.join(docs.path, '${base}_compressed.pdf');
    }
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save compressed PDF as',
      fileName: 'compressed.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _compress() async {
    if (_inputCtrl.text.isEmpty) {
      _snack('Select an input PDF.', error: true);
      return;
    }
    if (_outputCtrl.text.isEmpty) {
      _snack('Choose an output path.', error: true);
      return;
    }
    setState(() => _loading = true);
    try {
      await PdfService.compressPdf(_inputCtrl.text, _outputCtrl.text);
      final afterBytes = File(_outputCtrl.text).lengthSync();
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Compress PDF',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      setState(() => _afterBytes = afterBytes);
      _snack('Compressed successfully.', error: false);
    } catch (e) {
      _snack('Error: $e', error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _snack(String msg, {required bool error}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? AppTheme.error : AppTheme.success,
    ));
  }

  String _fmt(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(2)} MB';
  }

  @override
  Widget build(BuildContext context) {
    final saved = (_beforeBytes != null && _afterBytes != null)
        ? _beforeBytes! - _afterBytes!
        : null;
    final pct = (saved != null && _beforeBytes! > 0)
        ? (saved / _beforeBytes! * 100).toStringAsFixed(1)
        : null;

    return AppScaffold(
      title: 'Compress PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Compressing PDF...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Input PDF',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: _inputCtrl,
                    readOnly: true,
                    style: const TextStyle(
                        color: AppTheme.textPrimary, fontSize: 13),
                    decoration: const InputDecoration(
                      hintText: 'Select PDF to compress...',
                      prefixIcon: Icon(Icons.picture_as_pdf_rounded,
                          size: 18, color: AppTheme.textSecondary),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                CustomOutlinedButton(
                    onPressed: _pickInput, label: 'Browse'),
              ]),
              if (_beforeBytes != null) ...[
                const SizedBox(height: 8),
                Text('File size: ${_fmt(_beforeBytes!)}',
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 12)),
              ],
              const SizedBox(height: 20),
              const Text('Output File',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: _outputCtrl,
                    style: const TextStyle(
                        color: AppTheme.textPrimary, fontSize: 13),
                    decoration: const InputDecoration(
                      hintText: 'Output file path...',
                      prefixIcon: Icon(Icons.save_outlined,
                          size: 18, color: AppTheme.textSecondary),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                CustomOutlinedButton(
                    onPressed: _browseOutput, label: 'Browse'),
              ]),
              if (_afterBytes != null && saved != null) ...[
                const SizedBox(height: 20),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.success.withAlpha(18),
                    borderRadius: BorderRadius.circular(10),
                    border:
                        Border.all(color: AppTheme.success.withAlpha(60)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Compression Result',
                          style: TextStyle(
                              color: AppTheme.success,
                              fontWeight: FontWeight.w600,
                              fontSize: 13)),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          _statBox('Before', _fmt(_beforeBytes!)),
                          const SizedBox(width: 12),
                          _statBox('After', _fmt(_afterBytes!)),
                          const SizedBox(width: 12),
                          _statBox(
                              'Saved',
                              saved > 0
                                  ? '${_fmt(saved)} ($pct%)'
                                  : 'No reduction'),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: CustomElevatedButton(
                  onPressed: _compress,
                  label: 'Compress PDF',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _statBox(String label, String value) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppTheme.cardBackground,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppTheme.cardBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label,
                style: const TextStyle(
                    color: AppTheme.textSecondary, fontSize: 11)),
            const SizedBox(height: 4),
            Text(value,
                style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
