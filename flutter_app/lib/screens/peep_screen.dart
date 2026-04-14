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

class PeepScreen extends StatefulWidget {
  const PeepScreen({super.key});

  @override
  State<PeepScreen> createState() => _PeepScreenState();
}

class _PeepScreenState extends State<PeepScreen> {
  final TextEditingController _inputCtrl = TextEditingController();
  final TextEditingController _passCtrl = TextEditingController();
  final TextEditingController _outputCtrl = TextEditingController();
  bool _showPass = false;
  bool _loading = false;

  @override
  void dispose() {
    _inputCtrl.dispose();
    _passCtrl.dispose();
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
      final docs = await getApplicationDocumentsDirectory();
      final base = p.basenameWithoutExtension(path);
      _outputCtrl.text = p.join(docs.path, '${base}_unlocked.pdf');
    }
  }

  Future<void> _browseOutput() async {
    final result = await FilePicker.platform.saveFile(
      dialogTitle: 'Save decrypted PDF as',
      fileName: 'unlocked.pdf',
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result != null) setState(() => _outputCtrl.text = result);
  }

  Future<void> _decrypt() async {
    if (_inputCtrl.text.isEmpty) {
      _snack('Select an input PDF.', error: true);
      return;
    }
    if (_passCtrl.text.isEmpty) {
      _snack('Enter the PDF password.', error: true);
      return;
    }
    if (_outputCtrl.text.isEmpty) {
      _snack('Choose an output path.', error: true);
      return;
    }
    setState(() => _loading = true);
    try {
      await PdfService.decryptPdf(
          _inputCtrl.text, _outputCtrl.text, _passCtrl.text);
      await HistoryService.addEntry(HistoryEntry(
        operation: 'Peep PDF (Decrypt)',
        outputPath: _outputCtrl.text,
        timestamp: DateTime.now(),
      ));
      _snack('Password removed successfully.', error: false);
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
      title: 'Peep PDF — Remove Password',
      body: ProgressOverlay(
        visible: _loading,
        message: 'Removing password...',
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Color(0xFFa78bfa).withAlpha(18),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                      color: Color(0xFFa78bfa).withAlpha(50)),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline_rounded,
                        color: Color(0xFFa78bfa), size: 18),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'You must know the current password to unlock a protected PDF.',
                        style: TextStyle(
                            color: Color(0xFFa78bfa), fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(height: 24),
              Text('Input PDF',
                  style: TextStyle(
                      color: c.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputCtrl,
                      readOnly: true,
                      style: TextStyle(
                          color: c.textPrimary, fontSize: 13),
                      decoration: InputDecoration(
                        hintText: 'Select password-protected PDF...',
                        prefixIcon: Icon(Icons.picture_as_pdf_rounded,
                            size: 18, color: c.textSecondary),
                      ),
                    ),
                  ),
                  SizedBox(width: 10),
                  CustomOutlinedButton(
                      onPressed: _pickInput, label: 'Browse'),
                ],
              ),
              SizedBox(height: 20),
              Text('Current Password',
                  style: TextStyle(
                      color: c.textPrimary,
                      fontWeight: FontWeight.w600,
                      fontSize: 14)),
              SizedBox(height: 8),
              TextField(
                controller: _passCtrl,
                obscureText: !_showPass,
                style: TextStyle(
                    color: c.textPrimary, fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Enter the current password',
                  prefixIcon: Icon(Icons.lock_open_rounded,
                      size: 18, color: c.textSecondary),
                  suffixIcon: IconButton(
                    icon: Icon(
                        _showPass
                            ? Icons.visibility_off
                            : Icons.visibility,
                        size: 18,
                        color: c.textSecondary),
                    onPressed: () =>
                        setState(() => _showPass = !_showPass),
                  ),
                ),
              ),
              SizedBox(height: 20),
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
                        hintText: 'Output file path...',
                        prefixIcon: Icon(Icons.save_outlined,
                            size: 18, color: c.textSecondary),
                      ),
                    ),
                  ),
                  SizedBox(width: 10),
                  CustomOutlinedButton(
                      onPressed: _browseOutput, label: 'Browse'),
                ],
              ),
              SizedBox(height: 28),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: CustomElevatedButton(
                  onPressed: _decrypt,
                  label: 'Remove Password',
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
