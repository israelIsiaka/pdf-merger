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

class WordToPdfScreen extends StatefulWidget {
  const WordToPdfScreen({super.key});

  @override
  State<WordToPdfScreen> createState() => _WordToPdfScreenState();
}

class _WordToPdfScreenState extends State<WordToPdfScreen> {
  String? _inputPath;
  final TextEditingController _outputCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _outputCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['docx', 'doc', 'odt'],
    );
    if (result != null && result.files.first.path != null) {
      setState(() => _inputPath = result.files.first.path);
      _suggestOutput();
    }
  }

  void _suggestOutput() async {
    if (_inputPath == null || _outputCtrl.text.isNotEmpty) return;
    final docs = await getApplicationDocumentsDirectory();
    final baseName = p.basenameWithoutExtension(_inputPath!);
    _outputCtrl.text = p.join(docs.path, '$baseName.pdf');
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save PDF as',
      fileName: '${p.basenameWithoutExtension(_inputPath ?? 'output')}.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _convert() async {
    if (_inputPath == null || _outputCtrl.text.isEmpty) return;
    setState(() => _loading = true);
    try {
      await PdfService.wordToPdf(_inputPath!, _outputCtrl.text);
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Word to PDF',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Converted: ${p.basename(_outputCtrl.text)}'),
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
      title: 'Word to PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Converting Word to PDF...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF3b82f6).withAlpha(15),
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: const Color(0xFF3b82f6).withAlpha(40)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline_rounded,
                        size: 16, color: Color(0xFF3b82f6)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Requires LibreOffice installed on your system.',
                        style:
                            TextStyle(color: Color(0xFF3b82f6), fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              FileDropZone(
                onFilesDropped: (paths) {
                  final docs = paths.where((path) {
                    final ext = path.toLowerCase();
                    return ext.endsWith('.docx') ||
                        ext.endsWith('.doc') ||
                        ext.endsWith('.odt');
                  });
                  if (docs.isNotEmpty) {
                    setState(() => _inputPath = docs.first);
                    _suggestOutput();
                  }
                },
                label: 'Drop Word document here',
                sublabel: 'Supports .docx, .doc, .odt',
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _pickInput,
                icon: const Icon(Icons.folder_open_rounded, size: 18),
                label: const Text('Choose Word File'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3b82f6)),
              ),
              if (_inputPath != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppTheme.cardBackground,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.cardBorder),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.description_rounded,
                          color: Color(0xFF3b82f6), size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          p.basename(_inputPath!),
                          style: const TextStyle(
                              color: AppTheme.textPrimary, fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
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
                  onPressed:
                      _inputPath != null && _outputCtrl.text.isNotEmpty
                          ? _convert
                          : null,
                  icon: const Icon(Icons.picture_as_pdf_rounded),
                  label: const Text('Convert to PDF'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF3b82f6),
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
}
