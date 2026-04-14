import 'package:flutter/material.dart';
import 'package:desktop_drop/desktop_drop.dart';
import '../theme/app_theme.dart';

class FileDropZone extends StatefulWidget {
  final List<String> allowedExtensions;
  final void Function(List<String> paths) onFilesDropped;
  final String label;
  final String sublabel;
  final bool allowMultiple;

  const FileDropZone({
    super.key,
    required this.onFilesDropped,
    this.allowedExtensions = const ['pdf'],
    this.label = 'Drop files here',
    this.sublabel = 'or click Browse to select files',
    this.allowMultiple = true,
  });

  @override
  State<FileDropZone> createState() => _FileDropZoneState();
}

class _FileDropZoneState extends State<FileDropZone> {
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    return DropTarget(
      onDragEntered: (_) => setState(() => _isDragging = true),
      onDragExited: (_) => setState(() => _isDragging = false),
      onDragDone: (details) {
        setState(() => _isDragging = false);
        final paths = details.files
            .map((f) => f.path)
            .where((path) {
              if (widget.allowedExtensions.isEmpty) return true;
              final ext = path.split('.').last.toLowerCase();
              return widget.allowedExtensions.contains(ext);
            })
            .toList();
        if (paths.isNotEmpty) {
          widget.onFilesDropped(paths);
        }
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 24),
        decoration: BoxDecoration(
          color: _isDragging
              ? const Color(0xFF4f7ef7).withAlpha(20)
              : AppTheme.cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _isDragging
                ? AppTheme.primary
                : AppTheme.cardBorder,
            width: _isDragging ? 2 : 1,
          ),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              _isDragging
                  ? Icons.file_download_rounded
                  : Icons.upload_file_rounded,
              size: 40,
              color: _isDragging ? AppTheme.primary : AppTheme.textSecondary,
            ),
            const SizedBox(height: 12),
            Text(
              widget.label,
              style: TextStyle(
                color: _isDragging ? AppTheme.primary : AppTheme.textPrimary,
                fontSize: 15,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              widget.sublabel,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 13,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
