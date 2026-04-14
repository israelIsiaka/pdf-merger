import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/progress_overlay.dart';
import '../widgets/custom_button.dart';
import '../services/pdf_service.dart';
import '../services/history_service.dart';
import '../models/history_entry.dart';

class ProtectScreen extends StatefulWidget {
  const ProtectScreen({super.key});

  @override
  State<ProtectScreen> createState() => _ProtectScreenState();
}

class _ProtectScreenState extends State<ProtectScreen> {
  final TextEditingController _inputCtrl = TextEditingController();
  final TextEditingController _userPassCtrl = TextEditingController();
  final TextEditingController _ownerPassCtrl = TextEditingController();
  final TextEditingController _outputCtrl = TextEditingController();
  bool _showUser = false;
  bool _showOwner = false;
  bool _loading = false;

  @override
  void dispose() {
    _inputCtrl.dispose();
    _userPassCtrl.dispose();
    _ownerPassCtrl.dispose();
    _outputCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickInput() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result?.files.single.path != null) {
      final path = result!.files.single.path!;
      setState(() => _inputCtrl.text = path);
      _suggestOutput(path);
    }
  }

  void _suggestOutput(String inputPath) async {
    final dir = await getApplicationDocumentsDirectory();
    final base = p.basenameWithoutExtension(inputPath);
    _outputCtrl.text = p.join(dir.path, '${base}_protected.pdf');
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save protected PDF as',
      fileName: 'protected.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _protect() async {
    if (_inputCtrl.text.isEmpty) {
      _snack('Select an input PDF.', error: true);
      return;
    }
    if (_userPassCtrl.text.isEmpty) {
      _snack('Enter a user password.', error: true);
      return;
    }
    if (_outputCtrl.text.isEmpty) {
      _snack('Choose an output path.', error: true);
      return;
    }
    setState(() => _loading = true);
    try {
      await PdfService.protectPdf(
        _inputCtrl.text,
        _outputCtrl.text,
        _userPassCtrl.text,
        _ownerPassCtrl.text.isEmpty ? _userPassCtrl.text : _ownerPassCtrl.text,
      );
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Protect PDF',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      _snack('PDF protected successfully.', error: false);
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
      backgroundColor: error ? AppTheme.error : AppTheme.success,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'Protect PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Encrypting PDF...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _sectionLabel('Input PDF'),
              const SizedBox(height: 8),
              _filePicker(_inputCtrl, 'Select input PDF...', _pickInput),
              const SizedBox(height: 20),
              _sectionLabel('User Password'),
              const SizedBox(height: 8),
              _passwordField(_userPassCtrl, 'Password to open the PDF',
                  _showUser, () => setState(() => _showUser = !_showUser)),
              const SizedBox(height: 16),
              _sectionLabel('Owner Password'),
              const SizedBox(height: 4),
              const Text(
                'Controls editing/printing permissions. Leave blank to use user password.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 12),
              ),
              const SizedBox(height: 8),
              _passwordField(
                  _ownerPassCtrl,
                  'Owner password (optional)',
                  _showOwner,
                  () => setState(() => _showOwner = !_showOwner)),
              const SizedBox(height: 20),
              _sectionLabel('Output File'),
              const SizedBox(height: 8),
              _outputPicker(_outputCtrl, _browseOutput),
              const SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: CustomElevatedButton(
                  onPressed: _protect,
                  label: 'Protect PDF',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _sectionLabel(String label) => Text(label,
      style: const TextStyle(
          color: AppTheme.textPrimary,
          fontWeight: FontWeight.w600,
          fontSize: 14));

  Widget _filePicker(
      TextEditingController ctrl, String hint, VoidCallback onBrowse) {
    return Row(
      children: [
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
        CustomOutlinedButton(onPressed: onBrowse, label: 'Browse'),
      ],
    );
  }

  Widget _passwordField(TextEditingController ctrl, String hint, bool show,
      VoidCallback toggle) {
    return TextField(
      controller: ctrl,
      obscureText: !show,
      style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: const Icon(Icons.key_rounded,
            size: 18, color: AppTheme.textSecondary),
        suffixIcon: IconButton(
          icon: Icon(show ? Icons.visibility_off : Icons.visibility,
              size: 18, color: AppTheme.textSecondary),
          onPressed: toggle,
        ),
      ),
    );
  }

  Widget _outputPicker(TextEditingController ctrl, VoidCallback onBrowse) {
    return Row(
      children: [
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
      ],
    );
  }
}
