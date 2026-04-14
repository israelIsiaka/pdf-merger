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
      final c = AppColors.of(context);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? c.error : c.success,
    ));
  }

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'Protect PDF',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Encrypting PDF...',
        child: SingleChildScrollView(
          padding: EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _sectionLabel('Input PDF'),
              SizedBox(height: 8),
              _filePicker(_inputCtrl, 'Select input PDF...', _pickInput),
              SizedBox(height: 20),
              _sectionLabel('User Password'),
              SizedBox(height: 8),
              _passwordField(_userPassCtrl, 'Password to open the PDF',
                  _showUser, () => setState(() => _showUser = !_showUser)),
              SizedBox(height: 16),
              _sectionLabel('Owner Password'),
              SizedBox(height: 4),
              Text(
                'Controls editing/printing permissions. Leave blank to use user password.',
                style: TextStyle(color: c.textSecondary, fontSize: 12),
              ),
              SizedBox(height: 8),
              _passwordField(
                  _ownerPassCtrl,
                  'Owner password (optional)',
                  _showOwner,
                  () => setState(() => _showOwner = !_showOwner)),
              SizedBox(height: 20),
              _sectionLabel('Output File'),
              SizedBox(height: 8),
              _outputPicker(_outputCtrl, _browseOutput),
              SizedBox(height: 28),
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

  Widget _sectionLabel(String label) {
    final c = AppColors.of(context);
    return Text(label,
        style: TextStyle(
            color: c.textPrimary,
            fontWeight: FontWeight.w600,
            fontSize: 14));
  }

  Widget _filePicker(
      TextEditingController ctrl, String hint, VoidCallback onBrowse) {
    final c = AppColors.of(context);
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: ctrl,
            readOnly: true,
            style: TextStyle(color: c.textPrimary, fontSize: 13),
            decoration: InputDecoration(
              hintText: hint,
              prefixIcon: Icon(Icons.picture_as_pdf_rounded,
                  size: 18, color: c.textSecondary),
            ),
          ),
        ),
        SizedBox(width: 10),
        CustomOutlinedButton(onPressed: onBrowse, label: 'Browse'),
      ],
    );
  }

  Widget _passwordField(TextEditingController ctrl, String hint, bool show,
      VoidCallback toggle) {
    final c = AppColors.of(context);
    return TextField(
      controller: ctrl,
      obscureText: !show,
      style: TextStyle(color: c.textPrimary, fontSize: 13),
      decoration: InputDecoration(
        hintText: hint,
        prefixIcon: Icon(Icons.key_rounded,
            size: 18, color: c.textSecondary),
        suffixIcon: IconButton(
          icon: Icon(show ? Icons.visibility_off : Icons.visibility,
              size: 18, color: c.textSecondary),
          onPressed: toggle,
        ),
      ),
    );
  }

  Widget _outputPicker(TextEditingController ctrl, VoidCallback onBrowse) {
      final c = AppColors.of(context);
    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: ctrl,
            style: TextStyle(color: c.textPrimary, fontSize: 13),
            decoration: InputDecoration(
              hintText: 'Output file path...',
              prefixIcon: Icon(Icons.save_outlined,
                  size: 18, color: c.textSecondary),
            ),
          ),
        ),
        SizedBox(width: 10),
        OutlinedButton(onPressed: onBrowse, child: Text('Browse')),
      ],
    );
  }
}
