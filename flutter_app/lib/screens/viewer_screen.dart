import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:pdfrx/pdfrx.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';

class ViewerScreen extends StatefulWidget {
  const ViewerScreen({super.key});

  @override
  State<ViewerScreen> createState() => _ViewerScreenState();
}

class _ViewerScreenState extends State<ViewerScreen> {
  String? _filePath;
  final TextEditingController _passCtrl = TextEditingController();
  bool _showPassword = false;
  bool _needsPassword = false;
  String? _enteredPassword;
  final PdfViewerController _viewerController = PdfViewerController();

  @override
  void dispose() {
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result?.files.single.path != null) {
      setState(() {
        _filePath = result!.files.single.path!;
        _needsPassword = false;
        _enteredPassword = null;
        _passCtrl.clear();
      });
    }
  }

  void _submitPassword() {
    setState(() {
      _enteredPassword = _passCtrl.text;
      _needsPassword = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'View PDF',
      actions: [
        if (_filePath != null) ...[
          IconButton(
            icon: const Icon(Icons.zoom_in_rounded),
            tooltip: 'Zoom In',
            onPressed: () => _viewerController.zoomUp(),
          ),
          IconButton(
            icon: const Icon(Icons.zoom_out_rounded),
            tooltip: 'Zoom Out',
            onPressed: () => _viewerController.zoomDown(),
          ),
          IconButton(
            icon: const Icon(Icons.fit_screen_rounded),
            tooltip: 'Fit Page',
            onPressed: () => _viewerController.setZoom(
                _viewerController.centerPosition, 1.0),
          ),
        ],
        IconButton(
          icon: const Icon(Icons.folder_open_rounded),
          tooltip: 'Open PDF',
          onPressed: _pickFile,
        ),
      ],
      body: _filePath == null
          ? _emptyState()
          : _needsPassword
              ? _passwordPrompt()
              : Column(
                  children: [
                    Expanded(child: _buildViewer()),
                    _buildPageBar(),
                  ],
                ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.picture_as_pdf_rounded,
              size: 64, color: AppTheme.textSecondary),
          const SizedBox(height: 16),
          const Text('No PDF open',
              style: TextStyle(
                  color: AppTheme.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.w500)),
          const SizedBox(height: 8),
          const Text('Click Open PDF to load a document',
              style:
                  TextStyle(color: AppTheme.textSecondary, fontSize: 14)),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _pickFile,
            icon: const Icon(Icons.folder_open_rounded),
            label: const Text('Open PDF'),
          ),
        ],
      ),
    );
  }

  Widget _buildViewer() {
    // Build a passwordProvider that returns the entered password once,
    // then prompts the user if the password was wrong or not yet entered.
    PdfPasswordProvider? provider;
    if (_enteredPassword != null) {
      provider = createSimplePasswordProvider(_enteredPassword);
    } else {
      provider = () async {
        // No password provided yet — show password dialog on UI thread
        if (mounted) {
          setState(() => _needsPassword = true);
        }
        return null;
      };
    }

    return PdfViewer.file(
      _filePath!,
      passwordProvider: provider,
      controller: _viewerController,
      params: PdfViewerParams(
        backgroundColor: AppTheme.background,
        onDocumentChanged: (doc) {
          if (doc == null && mounted) {
            // Document failed / needs password
            setState(() => _needsPassword = true);
          }
        },
      ),
    );
  }

  Widget _passwordPrompt() {
    return Center(
      child: Container(
        width: 360,
        padding: const EdgeInsets.all(28),
        decoration: BoxDecoration(
          color: AppTheme.cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.cardBorder),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.lock_rounded,
                size: 36, color: Color(0xFF22d3ee)),
            const SizedBox(height: 14),
            const Text('Password Protected',
                style: TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            const SizedBox(height: 6),
            const Text('Enter the password to open this PDF',
                style: TextStyle(
                    color: AppTheme.textSecondary, fontSize: 13)),
            const SizedBox(height: 20),
            TextField(
              controller: _passCtrl,
              obscureText: !_showPassword,
              autofocus: true,
              style: const TextStyle(
                  color: AppTheme.textPrimary, fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Password',
                prefixIcon: const Icon(Icons.key_rounded,
                    size: 18, color: AppTheme.textSecondary),
                suffixIcon: IconButton(
                  icon: Icon(
                      _showPassword
                          ? Icons.visibility_off
                          : Icons.visibility,
                      size: 18,
                      color: AppTheme.textSecondary),
                  onPressed: () =>
                      setState(() => _showPassword = !_showPassword),
                ),
              ),
              onSubmitted: (_) => _submitPassword(),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submitPassword,
                child: const Text('Open'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPageBar() {
    return Container(
      height: 44,
      decoration: const BoxDecoration(
        color: AppTheme.cardBackground,
        border: Border(top: BorderSide(color: AppTheme.cardBorder)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.first_page_rounded,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () =>
                _viewerController.goToPage(pageNumber: 1),
            tooltip: 'First page',
          ),
          IconButton(
            icon: const Icon(Icons.chevron_left_rounded,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () {
              final cur = _viewerController.pageNumber ?? 2;
              _viewerController.goToPage(pageNumber: cur - 1);
            },
            tooltip: 'Previous page',
          ),
          const SizedBox(width: 8),
          ValueListenableBuilder<Matrix4>(
            valueListenable: _viewerController,
            builder: (context, _, _) {
              final current = _viewerController.pageNumber ?? 1;
              int total = 1;
              _viewerController.useDocument((doc) {
                total = doc.pages.length;
              });
              return Text(
                'Page $current of $total',
                style: const TextStyle(
                    color: AppTheme.textSecondary, fontSize: 13),
              );
            },
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.chevron_right_rounded,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () {
              final cur = _viewerController.pageNumber ?? 0;
              _viewerController.goToPage(pageNumber: cur + 1);
            },
            tooltip: 'Next page',
          ),
          IconButton(
            icon: const Icon(Icons.last_page_rounded,
                size: 20, color: AppTheme.textSecondary),
            onPressed: () {
              _viewerController.useDocument((doc) {
                _viewerController.goToPage(
                    pageNumber: doc.pages.length);
              });
            },
            tooltip: 'Last page',
          ),
        ],
      ),
    );
  }
}
