import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/progress_overlay.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

enum _SplitMode { ranges, everyN, singlePages }

class SplitScreen extends StatefulWidget {
  const SplitScreen({super.key});

  @override
  State<SplitScreen> createState() => _SplitScreenState();
}

class _SplitScreenState extends State<SplitScreen> {
  final _inputCtrl = TextEditingController();
  final _rangesCtrl = TextEditingController(text: '1-3,4-6');
  final _everyNCtrl = TextEditingController(text: '2');
  String? _outputDir;
  int? _pageCount;
  bool _loading = false;
  _SplitMode _mode = _SplitMode.ranges;
  List<String> _outputFiles = [];

  @override
  void dispose() {
    _inputCtrl.dispose();
    _rangesCtrl.dispose();
    _everyNCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['pdf']);
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      setState(() {
        _inputCtrl.text = path;
        _outputFiles = [];
      });
      try {
        final count = await PdfService.getPageCount(path);
        setState(() => _pageCount = count);
      } catch (_) {}
    }
  }

  Future<void> _pickOutputDir() async {
    final dir = await FilePicker.platform.getDirectoryPath(
        dialogTitle: 'Choose output folder');
    if (dir != null) setState(() => _outputDir = dir);
  }

  String _buildRangesString() {
    if (_mode == _SplitMode.ranges) return _rangesCtrl.text;
    if (_mode == _SplitMode.everyN && _pageCount != null) {
      final n = int.tryParse(_everyNCtrl.text) ?? 1;
      final parts = <String>[];
      for (int i = 1; i <= _pageCount!; i += n) {
        final end = (i + n - 1).clamp(1, _pageCount!);
        parts.add('$i-$end');
      }
      return parts.join(',');
    }
    if (_mode == _SplitMode.singlePages && _pageCount != null) {
      return List.generate(_pageCount!, (i) => '${i + 1}').join(',');
    }
    return _rangesCtrl.text;
  }

  Future<void> _split() async {
    if (_inputCtrl.text.isEmpty) { _snack('Select an input PDF.', error: true); return; }
    if (_outputDir == null) { _snack('Choose an output folder.', error: true); return; }
    setState(() { _loading = true; _outputFiles = []; });
    try {
      final ranges = _buildRangesString();
      final files = await PdfService.splitPdf(_inputCtrl.text, _outputDir!, ranges);
      for (final f in files) {
        await HistoryService.addEntry(HistoryEntry(
            operation: 'Split PDF', outputPath: f, timestamp: DateTime.now()));
      }
      setState(() => _outputFiles = files);
      _snack('Split into ${files.length} file${files.length == 1 ? '' : 's'}.', error: false);
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
        backgroundColor: error ? AppTheme.error : AppTheme.success));
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Split PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Splitting PDF...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Input PDF',
                  style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: _inputCtrl, readOnly: true,
                    style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                    decoration: const InputDecoration(
                      hintText: 'Select PDF to split...',
                      prefixIcon: Icon(Icons.picture_as_pdf_rounded, size: 18, color: AppTheme.textSecondary),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                OutlinedButton(onPressed: _pickInput, child: const Text('Browse')),
              ]),
              if (_pageCount != null) ...[
                const SizedBox(height: 6),
                Text('Pages: $_pageCount',
                    style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12)),
              ],
              const SizedBox(height: 20),
              const Text('Split Mode',
                  style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              const SizedBox(height: 8),
              RadioGroup<_SplitMode>(
                groupValue: _mode,
                onChanged: (v) => setState(() => _mode = v!),
                child: Column(
                  children: [
                    (_SplitMode.ranges, 'By page ranges (e.g. 1-3,4-6)'),
                    (_SplitMode.everyN, 'Every N pages'),
                    (_SplitMode.singlePages, 'Extract each page separately'),
                  ].map((entry) => RadioListTile<_SplitMode>(
                    value: entry.$1,
                    title: Text(entry.$2,
                        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13)),
                    activeColor: AppTheme.primary,
                    contentPadding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                  )).toList(),
                ),
              ),
              if (_mode == _SplitMode.ranges) ...[
                const SizedBox(height: 8),
                TextField(
                  controller: _rangesCtrl,
                  style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                  decoration: const InputDecoration(
                    hintText: 'e.g. 1-3,4-6,7',
                    prefixIcon: Icon(Icons.format_list_numbered_rounded, size: 18, color: AppTheme.textSecondary),
                  ),
                ),
              ],
              if (_mode == _SplitMode.everyN) ...[
                const SizedBox(height: 8),
                SizedBox(
                  width: 120,
                  child: TextField(
                    controller: _everyNCtrl,
                    keyboardType: TextInputType.number,
                    style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                    decoration: const InputDecoration(labelText: 'Pages per file'),
                  ),
                ),
              ],
              const SizedBox(height: 20),
              const Text('Output Folder',
                  style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              const SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0a0f1e),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppTheme.cardBorder),
                    ),
                    child: Text(
                      _outputDir ?? 'No folder selected',
                      style: TextStyle(
                          color: _outputDir != null ? AppTheme.textPrimary : AppTheme.textSecondary,
                          fontSize: 13),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                OutlinedButton(onPressed: _pickOutputDir, child: const Text('Choose Folder')),
              ]),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity, height: 48,
                child: ElevatedButton.icon(
                  onPressed: _split,
                  icon: const Icon(Icons.call_split_rounded),
                  label: const Text('Split PDF'),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFFf59e0b)),
                ),
              ),
              if (_outputFiles.isNotEmpty) ...[
                const SizedBox(height: 24),
                Text('Output files (${_outputFiles.length})',
                    style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
                const SizedBox(height: 8),
                ...(_outputFiles.map((f) => Container(
                  margin: const EdgeInsets.only(bottom: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppTheme.cardBackground,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.cardBorder),
                  ),
                  child: Row(children: [
                    const Icon(Icons.picture_as_pdf_rounded, size: 16, color: Color(0xFFf59e0b)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(p.basename(f),
                          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12)),
                    ),
                    Text(_fmtSize(f),
                        style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
                  ]),
                ))),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _fmtSize(String path) {
    try {
      final b = File(path).lengthSync();
      if (b < 1024) return '$b B';
      if (b < 1024 * 1024) return '${(b / 1024).toStringAsFixed(1)} KB';
      return '${(b / (1024 * 1024)).toStringAsFixed(2)} MB';
    } catch (_) { return ''; }
  }
}
