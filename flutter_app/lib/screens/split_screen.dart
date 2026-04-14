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
      final c = AppColors.of(context);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(msg),
        backgroundColor: error ? c.error : c.success));
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'Split PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Splitting PDF...',
        child: SingleChildScrollView(
          padding: EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Input PDF',
                  style: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: TextField(
                    controller: _inputCtrl, readOnly: true,
                    style: TextStyle(color: c.textPrimary, fontSize: 13),
                    decoration: InputDecoration(
                      hintText: 'Select PDF to split...',
                      prefixIcon: Icon(Icons.picture_as_pdf_rounded, size: 18, color: c.textSecondary),
                    ),
                  ),
                ),
                SizedBox(width: 10),
                OutlinedButton(onPressed: _pickInput, child: Text('Browse')),
              ]),
              if (_pageCount != null) ...[
                SizedBox(height: 6),
                Text('Pages: $_pageCount',
                    style: TextStyle(color: c.textSecondary, fontSize: 12)),
              ],
              SizedBox(height: 20),
              Text('Split Mode',
                  style: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              SizedBox(height: 8),
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
                        style: TextStyle(color: c.textPrimary, fontSize: 13)),
                    activeColor: c.primary,
                    contentPadding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                  )).toList(),
                ),
              ),
              if (_mode == _SplitMode.ranges) ...[
                SizedBox(height: 8),
                TextField(
                  controller: _rangesCtrl,
                  style: TextStyle(color: c.textPrimary, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'e.g. 1-3,4-6,7',
                    prefixIcon: Icon(Icons.format_list_numbered_rounded, size: 18, color: c.textSecondary),
                  ),
                ),
              ],
              if (_mode == _SplitMode.everyN) ...[
                SizedBox(height: 8),
                SizedBox(
                  width: 120,
                  child: TextField(
                    controller: _everyNCtrl,
                    keyboardType: TextInputType.number,
                    style: TextStyle(color: c.textPrimary, fontSize: 13),
                    decoration: InputDecoration(labelText: 'Pages per file'),
                  ),
                ),
              ],
              SizedBox(height: 20),
              Text('Output Folder',
                  style: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
              SizedBox(height: 8),
              Row(children: [
                Expanded(
                  child: Container(
                    padding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: Color(0xFF0a0f1e),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: c.cardBorder),
                    ),
                    child: Text(
                      _outputDir ?? 'No folder selected',
                      style: TextStyle(
                          color: _outputDir != null ? c.textPrimary : c.textSecondary,
                          fontSize: 13),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
                SizedBox(width: 10),
                OutlinedButton(onPressed: _pickOutputDir, child: Text('Choose Folder')),
              ]),
              SizedBox(height: 28),
              SizedBox(
                width: double.infinity, height: 48,
                child: ElevatedButton.icon(
                  onPressed: _split,
                  icon: Icon(Icons.call_split_rounded),
                  label: Text('Split PDF'),
                  style: ElevatedButton.styleFrom(backgroundColor: Color(0xFFf59e0b)),
                ),
              ),
              if (_outputFiles.isNotEmpty) ...[
                SizedBox(height: 24),
                Text('Output files (${_outputFiles.length})',
                    style: TextStyle(color: c.textPrimary, fontWeight: FontWeight.w600, fontSize: 14)),
                SizedBox(height: 8),
                ...(_outputFiles.map((f) => Container(
                  margin: EdgeInsets.only(bottom: 6),
                  padding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: c.cardBackground,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: c.cardBorder),
                  ),
                  child: Row(children: [
                    Icon(Icons.picture_as_pdf_rounded, size: 16, color: Color(0xFFf59e0b)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(p.basename(f),
                          style: TextStyle(color: c.textPrimary, fontSize: 12)),
                    ),
                    Text(_fmtSize(f),
                        style: TextStyle(color: c.textSecondary, fontSize: 11)),
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
