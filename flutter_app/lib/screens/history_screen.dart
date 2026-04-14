import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<HistoryEntry> _entries = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final entries = await HistoryService.getEntries();
    if (mounted) setState(() {
      _entries = entries;
      _loading = false;
    });
  }

  Future<void> _clear() async {
      final c = AppColors.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: c.cardBackground,
        title: Text('Clear History',
            style: TextStyle(color: c.textPrimary)),
        content: Text('Remove all history entries?',
            style: TextStyle(color: c.textSecondary)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text('Cancel')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text('Clear',
                  style: TextStyle(color: c.error))),
        ],
      ),
    );
    if (confirmed == true) {
      await HistoryService.clearHistory();
      _load();
    }
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-'
        '${dt.day.toString().padLeft(2, '0')}  '
        '${dt.hour.toString().padLeft(2, '0')}:'
        '${dt.minute.toString().padLeft(2, '0')}';
  }

  bool _fileExists(String path) {
    try {
      return File(path).existsSync();
    } catch (_) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'History',
      actions: [
        if (_entries.isNotEmpty)
          IconButton(
            icon: Icon(Icons.delete_sweep_rounded,
                color: c.textSecondary),
            tooltip: 'Clear all',
            onPressed: _clear,
          ),
        IconButton(
          icon: Icon(Icons.refresh_rounded,
              color: c.textSecondary),
          tooltip: 'Refresh',
          onPressed: _load,
        ),
      ],
      body: _loading
          ? Center(child: CircularProgressIndicator())
          : _entries.isEmpty
              ? _buildEmpty()
              : ListView.separated(
                  padding: EdgeInsets.all(20),
                  itemCount: _entries.length,
                  separatorBuilder: (_, __) =>
                      SizedBox(height: 8),
                  itemBuilder: (context, index) =>
                      _buildCard(_entries[index]),
                ),
    );
  }

  Widget _buildEmpty() {
      final c = AppColors.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.history_rounded,
              size: 56, color: c.textSecondary.withAlpha(80)),
          SizedBox(height: 16),
          Text('No history yet',
              style: TextStyle(color: c.textSecondary, fontSize: 16)),
          SizedBox(height: 6),
          Text('Processed files will appear here',
              style: TextStyle(color: c.textSecondary, fontSize: 13)),
        ],
      ),
    );
  }

  Widget _buildCard(HistoryEntry entry) {
      final c = AppColors.of(context);
    final exists = _fileExists(entry.outputPath);
    return Container(
      padding: EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: c.cardBackground,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: c.cardBorder),
      ),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: c.primary.withAlpha(25),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.picture_as_pdf_rounded,
                size: 18, color: c.primary),
          ),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(entry.operation,
                    style: TextStyle(
                        color: c.textPrimary,
                        fontSize: 13,
                        fontWeight: FontWeight.w600)),
                SizedBox(height: 2),
                Text(
                  p.basename(entry.outputPath),
                  style: TextStyle(
                      color: exists
                          ? c.textSecondary
                          : c.error.withAlpha(180),
                      fontSize: 12),
                  overflow: TextOverflow.ellipsis,
                ),
                SizedBox(height: 2),
                Text(_formatDate(entry.timestamp),
                    style: TextStyle(
                        color: c.textSecondary, fontSize: 11)),
              ],
            ),
          ),
          if (!exists)
            Tooltip(
              message: 'File no longer exists',
              child: Icon(Icons.warning_amber_rounded,
                  size: 16, color: c.warning),
            ),
        ],
      ),
    );
  }
}
