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

class PdfToImagesScreen extends StatefulWidget {
  const PdfToImagesScreen({super.key});

  @override
  State<PdfToImagesScreen> createState() => _PdfToImagesScreenState();
}

class _PdfToImagesScreenState extends State<PdfToImagesScreen> {
  String? _inputPath;
  String? _outputDir;
  int _dpi = 150;
  bool _loading = false;
  List<String> _outputPaths = [];

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null && result.files.first.path != null) {
      setState(() {
        _inputPath = result.files.first.path;
        _outputPaths = [];
      });
      _suggestOutputDir();
    }
  }

  void _suggestOutputDir() async {
    if (_outputDir != null) return;
    final docs = await getApplicationDocumentsDirectory();
    setState(() => _outputDir = docs.path);
  }

  Future<void> _pickOutputDir() async {
    final dir = await FilePicker.platform.getDirectoryPath(
        dialogTitle: 'Choose output folder');
    if (dir != null) setState(() => _outputDir = dir);
  }

  Future<void> _convert() async {
    if (_inputPath == null || _outputDir == null) return;
    setState(() {
      _loading = true;
      _outputPaths = [];
    });
    try {
      final paths =
          await PdfService.pdfToImages(_inputPath!, _outputDir!, _dpi);
      await HistoryService.addEntry(HistoryEntry(
        operation: 'PDF to Images (${paths.length} pages)',
        outputPath: _outputDir!,
        timestamp: DateTime.now(),
      ));
      if (mounted) {
        setState(() => _outputPaths = paths);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Exported ${paths.length} image(s) to output folder'),
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
      title: 'PDF to Images',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Rendering pages...',
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
                    setState(() {
                      _inputPath = pdfs.first;
                      _outputPaths = [];
                    });
                    _suggestOutputDir();
                  }
                },
                label: 'Drop PDF here',
                sublabel: 'Each page will be exported as a PNG image',
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _pickInput,
                icon: const Icon(Icons.folder_open_rounded, size: 18),
                label: const Text('Choose PDF'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF22c55e)),
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
                      const Icon(Icons.picture_as_pdf_rounded,
                          color: Color(0xFF22c55e), size: 20),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(p.basename(_inputPath!),
                            style: const TextStyle(
                                color: AppTheme.textPrimary, fontSize: 13),
                            overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 24),
              const Text('Resolution (DPI)',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 4),
              Text('$_dpi DPI — higher = better quality, larger files',
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 12)),
              Slider(
                value: _dpi.toDouble(),
                min: 72,
                max: 300,
                divisions: 8,
                label: '$_dpi DPI',
                onChanged: (v) => setState(() => _dpi = v.round()),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: const [
                  Text('72', style: TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
                  Text('150', style: TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
                  Text('300', style: TextStyle(color: AppTheme.textSecondary, fontSize: 11)),
                ],
              ),
              const SizedBox(height: 24),
              const Text('Output Folder',
                  style: TextStyle(
                      color: AppTheme.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0a0f1e),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppTheme.cardBorder),
                      ),
                      child: Text(
                        _outputDir ?? 'Choose output folder...',
                        style: TextStyle(
                            color: _outputDir != null
                                ? AppTheme.textPrimary
                                : AppTheme.textSecondary,
                            fontSize: 13),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  OutlinedButton(
                      onPressed: _pickOutputDir,
                      child: const Text('Browse')),
                ],
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _inputPath != null && _outputDir != null
                      ? _convert
                      : null,
                  icon: const Icon(Icons.image_rounded),
                  label: const Text('Export as Images'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF22c55e),
                    disabledBackgroundColor: AppTheme.cardBorder,
                    disabledForegroundColor: AppTheme.textSecondary,
                  ),
                ),
              ),
              if (_outputPaths.isNotEmpty) ...[
                const SizedBox(height: 24),
                Text('${_outputPaths.length} image(s) exported:',
                    style: const TextStyle(
                        color: AppTheme.textSecondary, fontSize: 13)),
                const SizedBox(height: 8),
                ...(_outputPaths.take(5).map((path) => Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text(
                        p.basename(path),
                        style: const TextStyle(
                            color: AppTheme.success, fontSize: 12),
                      ),
                    ))),
                if (_outputPaths.length > 5)
                  Text('... and ${_outputPaths.length - 5} more',
                      style: const TextStyle(
                          color: AppTheme.textSecondary, fontSize: 12)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
