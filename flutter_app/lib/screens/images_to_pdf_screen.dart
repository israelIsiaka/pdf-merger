import 'dart:io';
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

class ImagesToPdfScreen extends StatefulWidget {
  const ImagesToPdfScreen({super.key});

  @override
  State<ImagesToPdfScreen> createState() => _ImagesToPdfScreenState();
}

class _ImagesToPdfScreenState extends State<ImagesToPdfScreen> {
  final List<String> _images = [];
  final TextEditingController _outputCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _outputCtrl.dispose();
    super.dispose();
  }

  Future<void> _addImages() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff'],
      allowMultiple: true,
    );
    if (result != null) {
      setState(() {
        for (final f in result.files) {
          if (f.path != null && !_images.contains(f.path)) {
            _images.add(f.path!);
          }
        }
      });
      _suggestOutput();
    }
  }

  void _suggestOutput() async {
    if (_outputCtrl.text.isNotEmpty) return;
    final docs = await getApplicationDocumentsDirectory();
    _outputCtrl.text = p.join(docs.path, 'images_output.pdf');
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save PDF as',
      fileName: 'images_output.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _convert() async {
      final c = AppColors.of(context);
    if (_images.isEmpty || _outputCtrl.text.isEmpty) return;
    setState(() => _loading = true);
    try {
      await PdfService.imagesToPdf(List.from(_images), _outputCtrl.text);
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Images to PDF (${_images.length} images)',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Created: ${p.basename(_outputCtrl.text)}'),
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
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'Images to PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Building PDF...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              FileDropZone(
                onFilesDropped: (paths) {
                  final imgs = paths.where((path) {
                    final ext = path.toLowerCase();
                    return ext.endsWith('.jpg') ||
                        ext.endsWith('.jpeg') ||
                        ext.endsWith('.png') ||
                        ext.endsWith('.bmp') ||
                        ext.endsWith('.gif') ||
                        ext.endsWith('.tiff');
                  });
                  if (imgs.isNotEmpty) {
                    setState(() {
                      for (final img in imgs) {
                        if (!_images.contains(img)) _images.add(img);
                      }
                    });
                    _suggestOutput();
                  }
                },
                label: 'Drop images here',
                sublabel: 'JPG, PNG, BMP, GIF, TIFF supported',
                allowMultiple: true,
              ),
              SizedBox(height: 16),
              Row(
                children: [
                  ElevatedButton.icon(
                    onPressed: _addImages,
                    icon: Icon(Icons.add_photo_alternate_rounded, size: 18),
                    label: Text('Add Images'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: Color(0xFFec4899)),
                  ),
                  Spacer(),
                  if (_images.isNotEmpty)
                    TextButton.icon(
                      onPressed: () => setState(() => _images.clear()),
                      icon: Icon(Icons.clear_all_rounded, size: 16),
                      label: Text('Clear All'),
                      style: TextButton.styleFrom(
                          foregroundColor: c.textSecondary),
                    ),
                ],
              ),
              if (_images.isNotEmpty) ...[
                SizedBox(height: 20),
                Text(
                  '${_images.length} image${_images.length == 1 ? '' : 's'} — drag to reorder',
                  style: TextStyle(
                      color: c.textSecondary, fontSize: 13),
                ),
                SizedBox(height: 8),
                Container(
                  decoration: BoxDecoration(
                    color: c.cardBackground,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: c.cardBorder),
                  ),
                  child: ReorderableListView.builder(
                    shrinkWrap: true,
                    physics: NeverScrollableScrollPhysics(),
                    itemCount: _images.length,
                    onReorder: (oldIndex, newIndex) {
                      setState(() {
                        if (newIndex > oldIndex) newIndex--;
                        final item = _images.removeAt(oldIndex);
                        _images.insert(newIndex, item);
                      });
                    },
                    itemBuilder: (context, index) {
                      final path = _images[index];
                      return ListTile(
                        key: ValueKey(path + index.toString()),
                        leading: Icon(Icons.image_rounded,
                            color: Color(0xFFec4899), size: 20),
                        title: Text(
                          p.basename(path),
                          style: TextStyle(
                              color: c.textPrimary, fontSize: 13),
                          overflow: TextOverflow.ellipsis,
                        ),
                        subtitle: Text(_fileSize(path),
                            style: TextStyle(
                                color: c.textSecondary, fontSize: 11)),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('#${index + 1}',
                                style: TextStyle(
                                    color: c.textSecondary,
                                    fontSize: 12)),
                            SizedBox(width: 8),
                            IconButton(
                              icon: Icon(Icons.close_rounded,
                                  size: 16, color: c.textSecondary),
                              onPressed: () =>
                                  setState(() => _images.removeAt(index)),
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
              SizedBox(height: 24),
              Text('Output File',
                  style: TextStyle(
                      color: c.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              SizedBox(height: 8),
              Row(
                children: [
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
                      onPressed: _browseOutput, child: Text('Browse')),
                ],
              ),
              SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed:
                      _images.isNotEmpty && _outputCtrl.text.isNotEmpty
                          ? _convert
                          : null,
                  icon: Icon(Icons.picture_as_pdf_rounded),
                  label: Text(_images.isEmpty
                      ? 'Add images first'
                      : 'Combine ${_images.length} Images'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Color(0xFFec4899),
                    disabledBackgroundColor: c.cardBorder,
                    disabledForegroundColor: c.textSecondary,
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
