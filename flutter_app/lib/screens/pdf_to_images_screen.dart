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
      final c = AppColors.of(context);
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
              SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _pickInput,
                icon: Icon(Icons.folder_open_rounded, size: 18),
                label: Text('Choose PDF'),
                style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF22c55e)),
              ),
              if (_inputPath != null) ...[
                SizedBox(height: 12),
                Container(
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: c.cardBackground,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: c.cardBorder),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.picture_as_pdf_rounded,
                          color: Color(0xFF22c55e), size: 20),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(p.basename(_inputPath!),
                            style: TextStyle(
                                color: c.textPrimary, fontSize: 13),
                            overflow: TextOverflow.ellipsis),
                      ),
                    ],
                  ),
                ),
              ],
              SizedBox(height: 24),
              Text('Resolution (DPI)',
                  style: TextStyle(
                      color: c.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              SizedBox(height: 4),
              Text('$_dpi DPI — higher = better quality, larger files',
                  style: TextStyle(
                      color: c.textSecondary, fontSize: 12)),
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
                children: [
                  Text('72', style: TextStyle(color: c.textSecondary, fontSize: 11)),
                  Text('150', style: TextStyle(color: c.textSecondary, fontSize: 11)),
                  Text('300', style: TextStyle(color: c.textSecondary, fontSize: 11)),
                ],
              ),
              SizedBox(height: 24),
              Text('Output Folder',
                  style: TextStyle(
                      color: c.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: EdgeInsets.symmetric(
                          horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: Color(0xFF0a0f1e),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: c.cardBorder),
                      ),
                      child: Text(
                        _outputDir ?? 'Choose output folder...',
                        style: TextStyle(
                            color: _outputDir != null
                                ? c.textPrimary
                                : c.textSecondary,
                            fontSize: 13),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                  SizedBox(width: 10),
                  OutlinedButton(
                      onPressed: _pickOutputDir,
                      child: Text('Browse')),
                ],
              ),
              SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _inputPath != null && _outputDir != null
                      ? _convert
                      : null,
                  icon: Icon(Icons.image_rounded),
                  label: Text('Export as Images'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFF22c55e),
                    disabledBackgroundColor: c.cardBorder,
                    disabledForegroundColor: c.textSecondary,
                  ),
                ),
              ),
              if (_outputPaths.isNotEmpty) ...[
                SizedBox(height: 24),
                Text('${_outputPaths.length} image(s) exported:',
                    style: TextStyle(
                        color: c.textSecondary, fontSize: 13)),
                SizedBox(height: 8),
                ...(_outputPaths.take(5).map((path) => Padding(
                      padding: EdgeInsets.only(bottom: 4),
                      child: Text(
                        p.basename(path),
                        style: TextStyle(
                            color: c.success, fontSize: 12),
                      ),
                    ))),
                if (_outputPaths.length > 5)
                  Text('... and ${_outputPaths.length - 5} more',
                      style: TextStyle(
                          color: c.textSecondary, fontSize: 12)),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
