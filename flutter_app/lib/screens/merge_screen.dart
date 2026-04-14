import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/file_drop_zone.dart';
import '../widgets/progress_overlay.dart';
import '../widgets/custom_button.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class MergeScreen extends StatefulWidget {
  const MergeScreen({super.key});

  @override
  State<MergeScreen> createState() => _MergeScreenState();
}

class _MergeScreenState extends State<MergeScreen> {
  final List<String> _files = [];
  final TextEditingController _outputCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _outputCtrl.dispose();
    super.dispose();
  }

  Future<void> _addFiles() async {
    print('DEBUG: _addFiles button pressed');
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      allowMultiple: true,
    );
    if (result != null) {
      setState(() {
        for (final f in result.files) {
          if (f.path != null && !_files.contains(f.path)) {
            _files.add(f.path!);
          }
        }
      });
      _suggestOutput();
    }
  }

  Future<void> _addFolder() async {
    final dir = await FilePicker.platform.getDirectoryPath();
    if (dir == null) return;
    final entries = Directory(dir).listSync();
    final pdfs = entries
        .whereType<File>()
        .where((f) => f.path.toLowerCase().endsWith('.pdf'))
        .map((f) => f.path)
        .toList()
      ..sort();
    if (pdfs.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No PDF files found in that folder.')),
        );
      }
      return;
    }
    setState(() {
      for (final path in pdfs) {
        if (!_files.contains(path)) _files.add(path);
      }
    });
    _suggestOutput();
  }

  void _suggestOutput() async {
    if (_outputCtrl.text.isNotEmpty) return;
    final docs = await getApplicationDocumentsDirectory();
    _outputCtrl.text = p.join(docs.path, 'merged_output.pdf');
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save merged PDF as',
      fileName: 'merged_output.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _merge() async {
    if (_files.length < 2) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Add at least 2 PDF files to merge.')),
      );
      return;
    }
    if (_outputCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Choose an output file path.')),
      );
      return;
    }
    setState(() => _loading = true);
    try {
      await PdfService.mergePdfs(List.from(_files), _outputCtrl.text);
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Merge PDFs',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                'Merged successfully: ${p.basename(_outputCtrl.text)}'),
            backgroundColor: AppTheme.success,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppTheme.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _fileSize(String path) {
    try {
      final bytes = File(path).lengthSync();
      if (bytes < 1024) return '${bytes}B';
      if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)}KB';
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)}MB';
    } catch (_) {
      return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Merge PDFs',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Merging PDFs...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FileDropZone(
                onFilesDropped: (paths) {
                  setState(() {
                    for (final path in paths) {
                      if (!_files.contains(path)) _files.add(path);
                    }
                  });
                  _suggestOutput();
                },
                label: 'Drop PDF files here',
                sublabel: 'or use the buttons below to add files',
                allowMultiple: true,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  CustomElevatedButton(
                    onPressed: _addFiles,
                    label: 'Add PDFs',
                    icon: Icons.add_rounded,
                  ),
                  const SizedBox(width: 12),
                  CustomOutlinedButton(
                    onPressed: _addFolder,
                    label: 'Add Folder',
                    icon: Icons.folder_open_rounded,
                  ),
                  const Spacer(),
                  if (_files.isNotEmpty)
                    CustomOutlinedButton(
                      onPressed: () => setState(() => _files.clear()),
                      label: 'Clear All',
                      icon: Icons.clear_all_rounded,
                    ),
                ],
              ),
              if (_files.isNotEmpty) ...[
                const SizedBox(height: 20),
                Text(
                  '${_files.length} file${_files.length == 1 ? '' : 's'} — drag to reorder',
                  style: const TextStyle(
                      color: AppTheme.textSecondary, fontSize: 13),
                ),
                const SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: AppTheme.cardBackground,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppTheme.cardBorder),
                  ),
                  child: ReorderableListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _files.length,
                    onReorder: (oldIndex, newIndex) {
                      setState(() {
                        if (newIndex > oldIndex) newIndex--;
                        final item = _files.removeAt(oldIndex);
                        _files.insert(newIndex, item);
                      });
                    },
                    itemBuilder: (context, index) {
                      final path = _files[index];
                      return ListTile(
                        key: ValueKey(path + index.toString()),
                        leading: const Icon(Icons.picture_as_pdf_rounded,
                            color: Color(0xFF4f7ef7), size: 20),
                        title: Text(
                          p.basename(path),
                          style: const TextStyle(
                              color: AppTheme.textPrimary, fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(
                          _fileSize(path),
                          style: const TextStyle(
                              color: AppTheme.textSecondary, fontSize: 11),
                        ),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '#${index + 1}',
                              style: const TextStyle(
                                  color: AppTheme.textSecondary, fontSize: 12),
                            ),
                            const SizedBox(width: 8),
                            IconButton(
                              icon: const Icon(Icons.close_rounded,
                                  size: 16, color: AppTheme.textSecondary),
                              onPressed: () =>
                                  setState(() => _files.removeAt(index)),
                              tooltip: 'Remove',
                            ),
                          ],
                        ),
                        dense: true,
                      );
                    },
                  ),
                ),
              ],
              const SizedBox(height: 24),
              const Text(
                'Output File',
                style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 14),
              ),
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
                  CustomOutlinedButton(
                    onPressed: _browseOutput,
                    label: 'Browse',
                  ),
                ],
              ),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: CustomElevatedButton(
                  onPressed: _files.length >= 2 ? _merge : () {},
                  label: _files.length >= 2
                      ? 'Merge ${_files.length} Files'
                      : 'Add at least 2 PDFs',
                  enabled: _files.length >= 2,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
