import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/progress_overlay.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class WatermarkScreen extends StatefulWidget {
  const WatermarkScreen({super.key});

  @override
  State<WatermarkScreen> createState() => _WatermarkScreenState();
}

class _WatermarkScreenState extends State<WatermarkScreen> {
  final _inputCtrl = TextEditingController();
  final _outputCtrl = TextEditingController();
  final _textCtrl = TextEditingController(text: 'CONFIDENTIAL');
  final _colorCtrl = TextEditingController(text: '#808080');

  double _opacity = 0.3;
  double _rotation = -45;
  String _position = 'center';
  String _frequency = 'all';
  bool _loading = false;

  static const _positions = [
    'center', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'grid'
  ];
  static const _frequencies = ['all', 'first', 'last'];

  @override
  void dispose() {
    _inputCtrl.dispose();
    _outputCtrl.dispose();
    _textCtrl.dispose();
    _colorCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
        type: FileType.custom, allowedExtensions: ['pdf']);
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      setState(() => _inputCtrl.text = path);
      final docs = await getApplicationDocumentsDirectory();
      _outputCtrl.text =
          p.join(docs.path, '${p.basenameWithoutExtension(path)}_watermarked.pdf');
    }
  }

  Future<void> _browseOutput() async {
    final r = await FilePicker.platform.saveFile(
        dialogTitle: 'Save watermarked PDF',
        fileName: 'watermarked.pdf',
        type: FileType.custom,
        allowedExtensions: ['pdf']);
    if (r != null) setState(() => _outputCtrl.text = r);
  }

  Future<void> _apply() async {
    if (_inputCtrl.text.isEmpty) { _snack('Select an input PDF.', error: true); return; }
    if (_textCtrl.text.isEmpty) { _snack('Enter watermark text.', error: true); return; }
    if (_outputCtrl.text.isEmpty) { _snack('Choose an output path.', error: true); return; }
    setState(() => _loading = true);
    try {
      await PdfService.addWatermark(
        _inputCtrl.text,
        _outputCtrl.text,
        _textCtrl.text,
        opacity: _opacity,
        rotation: _rotation,
        color: _colorCtrl.text.isEmpty ? '#808080' : _colorCtrl.text,
        position: _position,
        frequency: _frequency,
      );
      await HistoryService.addEntry(HistoryEntry(
          operation: 'Watermark PDF',
          outputPath: _outputCtrl.text,
          timestamp: DateTime.now()));
      _snack('Watermark applied successfully.', error: false);
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

  Color get _previewColor {
    try {
      final hex = _colorCtrl.text.replaceAll('#', '');
      if (hex.length == 6) {
        return Color(int.parse('FF$hex', radix: 16));
      }
    } catch (_) {}
    return Colors.grey;
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Add Watermark',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Applying watermark...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _label('Input PDF'),
              const SizedBox(height: 8),
              _filePicker(_inputCtrl, 'Select PDF...', _pickInput),
              const SizedBox(height: 20),
              _label('Watermark Text'),
              const SizedBox(height: 8),
              TextField(
                controller: _textCtrl,
                style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
                decoration: const InputDecoration(hintText: 'e.g. CONFIDENTIAL'),
              ),
              const SizedBox(height: 20),
              Row(children: [
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('Opacity: ${_opacity.toStringAsFixed(2)}'),
                    Slider(
                      value: _opacity,
                      min: 0.05,
                      max: 0.95,
                      divisions: 18,
                      label: _opacity.toStringAsFixed(2),
                      onChanged: (v) => setState(() => _opacity = v),
                    ),
                  ],
                )),
                const SizedBox(width: 20),
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('Rotation: ${_rotation.toStringAsFixed(0)}°'),
                    Slider(
                      value: _rotation,
                      min: -90,
                      max: 90,
                      divisions: 36,
                      label: '${_rotation.toStringAsFixed(0)}°',
                      onChanged: (v) => setState(() => _rotation = v),
                    ),
                  ],
                )),
              ]),
              const SizedBox(height: 16),
              Row(children: [
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('Color (hex)'),
                    const SizedBox(height: 8),
                    Row(children: [
                      Expanded(
                        child: TextField(
                          controller: _colorCtrl,
                          style: const TextStyle(
                              color: AppTheme.textPrimary, fontSize: 13),
                          decoration: const InputDecoration(hintText: '#808080'),
                          onChanged: (_) => setState(() {}),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Container(
                        width: 36, height: 36,
                        decoration: BoxDecoration(
                          color: _previewColor,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: AppTheme.cardBorder),
                        ),
                      ),
                    ]),
                  ],
                )),
                const SizedBox(width: 20),
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _label('Position'),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                      initialValue: _position,
                      dropdownColor: AppTheme.cardBackground,
                      style: const TextStyle(
                          color: AppTheme.textPrimary, fontSize: 13),
                      decoration: const InputDecoration(),
                      items: _positions.map((pos) => DropdownMenuItem(
                          value: pos,
                          child: Text(pos))).toList(),
                      onChanged: (v) => setState(() => _position = v!),
                    ),
                  ],
                )),
              ]),
              const SizedBox(height: 20),
              _label('Apply to pages'),
              const SizedBox(height: 8),
              Row(children: _frequencies.map((f) => Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(f[0].toUpperCase() + f.substring(1)),
                  selected: _frequency == f,
                  onSelected: (_) => setState(() => _frequency = f),
                  selectedColor: AppTheme.primary.withAlpha(60),
                  labelStyle: TextStyle(
                    color: _frequency == f
                        ? AppTheme.primary
                        : AppTheme.textSecondary,
                    fontSize: 13,
                  ),
                  backgroundColor: AppTheme.cardBackground,
                  side: BorderSide(
                    color: _frequency == f
                        ? AppTheme.primary
                        : AppTheme.cardBorder,
                  ),
                ),
              )).toList()),
              const SizedBox(height: 20),
              _label('Output File'),
              const SizedBox(height: 8),
              _outputPicker(_outputCtrl, _browseOutput),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: _apply,
                  icon: const Icon(Icons.water_drop_outlined),
                  label: const Text('Apply Watermark'),
                  style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF06b6d4)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _label(String t) => Text(t,
      style: const TextStyle(
          color: AppTheme.textPrimary,
          fontWeight: FontWeight.w600,
          fontSize: 14));

  Widget _filePicker(
      TextEditingController ctrl, String hint, VoidCallback onBrowse) {
    return Row(children: [
      Expanded(
        child: TextField(
          controller: ctrl,
          readOnly: true,
          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
          decoration: InputDecoration(
            hintText: hint,
            prefixIcon: const Icon(Icons.picture_as_pdf_rounded,
                size: 18, color: AppTheme.textSecondary),
          ),
        ),
      ),
      const SizedBox(width: 10),
      OutlinedButton(onPressed: onBrowse, child: const Text('Browse')),
    ]);
  }

  Widget _outputPicker(TextEditingController ctrl, VoidCallback onBrowse) {
    return Row(children: [
      Expanded(
        child: TextField(
          controller: ctrl,
          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
          decoration: const InputDecoration(
            hintText: 'Output file path...',
            prefixIcon: Icon(Icons.save_outlined,
                size: 18, color: AppTheme.textSecondary),
          ),
        ),
      ),
      const SizedBox(width: 10),
      OutlinedButton(onPressed: onBrowse, child: const Text('Browse')),
    ]);
  }
}
