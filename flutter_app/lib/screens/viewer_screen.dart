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
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'View PDF',
      actions: [
        if (_filePath != null) ...[
          IconButton(
            icon: Icon(Icons.zoom_in_rounded),
            tooltip: 'Zoom In',
            onPressed: () => _viewerController.zoomUp(),
          ),
          IconButton(
            icon: Icon(Icons.zoom_out_rounded),
            tooltip: 'Zoom Out',
            onPressed: () => _viewerController.zoomDown(),
          ),
          IconButton(
            icon: Icon(Icons.fit_screen_rounded),
            tooltip: 'Fit Page',
            onPressed: () => _viewerController.setZoom(
                _viewerController.centerPosition, 1.0),
          ),
        ],
        IconButton(
          icon: Icon(Icons.folder_open_rounded),
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
      final c = AppColors.of(context);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.picture_as_pdf_rounded,
              size: 64, color: c.textSecondary),
          SizedBox(height: 16),
          Text('No PDF open',
              style: TextStyle(
                  color: c.textPrimary,
                  fontSize: 18,
                  fontWeight: FontWeight.w500)),
          SizedBox(height: 8),
          Text('Click Open PDF to load a document',
              style:
                  TextStyle(color: c.textSecondary, fontSize: 14)),
          SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _pickFile,
            icon: Icon(Icons.folder_open_rounded),
            label: Text('Open PDF'),
          ),
        ],
      ),
    );
  }

  Widget _buildViewer() {
      final c = AppColors.of(context);
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
        backgroundColor: c.background,
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
      final c = AppColors.of(context);
    return Center(
      child: Container(
        width: 360,
        padding: EdgeInsets.all(28),
        decoration: BoxDecoration(
          color: c.cardBackground,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: c.cardBorder),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.lock_rounded,
                size: 36, color: Color(0xFF22d3ee)),
            SizedBox(height: 14),
            Text('Password Protected',
                style: TextStyle(
                    color: c.textPrimary,
                    fontSize: 16,
                    fontWeight: FontWeight.w600)),
            SizedBox(height: 6),
            Text('Enter the password to open this PDF',
                style: TextStyle(
                    color: c.textSecondary, fontSize: 13)),
            SizedBox(height: 20),
            TextField(
              controller: _passCtrl,
              obscureText: !_showPassword,
              autofocus: true,
              style: TextStyle(
                  color: c.textPrimary, fontSize: 13),
              decoration: InputDecoration(
                hintText: 'Password',
                prefixIcon: Icon(Icons.key_rounded,
                    size: 18, color: c.textSecondary),
                suffixIcon: IconButton(
                  icon: Icon(
                      _showPassword
                          ? Icons.visibility_off
                          : Icons.visibility,
                      size: 18,
                      color: c.textSecondary),
                  onPressed: () =>
                      setState(() => _showPassword = !_showPassword),
                ),
              ),
              onSubmitted: (_) => _submitPassword(),
            ),
            SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submitPassword,
                child: Text('Open'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPageBar() {
      final c = AppColors.of(context);
    return Container(
      height: 44,
      decoration: BoxDecoration(
        color: c.cardBackground,
        border: Border(top: BorderSide(color: c.cardBorder)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: Icon(Icons.first_page_rounded,
                size: 20, color: c.textSecondary),
            onPressed: () =>
                _viewerController.goToPage(pageNumber: 1),
            tooltip: 'First page',
          ),
          IconButton(
            icon: Icon(Icons.chevron_left_rounded,
                size: 20, color: c.textSecondary),
            onPressed: () {
              final cur = _viewerController.pageNumber ?? 2;
              _viewerController.goToPage(pageNumber: cur - 1);
            },
            tooltip: 'Previous page',
          ),
          SizedBox(width: 8),
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
                style: TextStyle(
                    color: c.textSecondary, fontSize: 13),
              );
            },
          ),
          SizedBox(width: 8),
          IconButton(
            icon: Icon(Icons.chevron_right_rounded,
                size: 20, color: c.textSecondary),
            onPressed: () {
              final cur = _viewerController.pageNumber ?? 0;
              _viewerController.goToPage(pageNumber: cur + 1);
            },
            tooltip: 'Next page',
          ),
          IconButton(
            icon: Icon(Icons.last_page_rounded,
                size: 20, color: c.textSecondary),
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
