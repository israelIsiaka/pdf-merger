import 'dart:io';
import 'dart:typed_data';
import 'dart:ui';
import 'package:path/path.dart' as p;
import 'package:syncfusion_flutter_pdf/pdf.dart';
import 'package:pdfrx/pdfrx.dart' as rx;

class PdfService {
  // ---------------------------------------------------------------------------
  // Merge
  // ---------------------------------------------------------------------------
  static Future<void> mergePdfs(
      List<String> inputPaths, String outputPath) async {
    final result = PdfDocument();
    for (final path in inputPaths) {
      final bytes = await File(path).readAsBytes();
      final src = PdfDocument(inputBytes: bytes);
      for (int i = 0; i < src.pages.count; i++) {
        final srcPage = src.pages[i];
        final section = result.sections!.add();
        section.pageSettings.size = srcPage.size;
        section.pageSettings.margins.all = 0;
        final destPage = section.pages.add();
        final template = srcPage.createTemplate();
        destPage.graphics.drawPdfTemplate(template, Offset.zero);
      }
      src.dispose();
    }
    final outBytes = result.saveSync();
    result.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // Protect
  // ---------------------------------------------------------------------------
  static Future<void> protectPdf(
    String inputPath,
    String outputPath,
    String userPassword,
    String ownerPassword,
  ) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);
    doc.security.userPassword = userPassword;
    doc.security.ownerPassword = ownerPassword;
    doc.security.algorithm = PdfEncryptionAlgorithm.aesx256Bit;
    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // Decrypt / Peep
  // ---------------------------------------------------------------------------
  static Future<void> decryptPdf(
    String inputPath,
    String outputPath,
    String password,
  ) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes, password: password);
    doc.security.userPassword = '';
    doc.security.ownerPassword = '';
    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // Compress
  // ---------------------------------------------------------------------------
  static Future<void> compressPdf(
    String inputPath,
    String outputPath, {
    PdfCompressionLevel level = PdfCompressionLevel.best,
  }) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);
    doc.compressionLevel = level;
    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // Render a page as preview image (used by watermark / annotate screens)
  // ---------------------------------------------------------------------------
  static Future<Uint8List?> renderPreview(String pdfPath,
      {double targetWidth = 400, int pageIndex = 0}) async {
    try {
      final doc = await rx.PdfDocument.openFile(pdfPath);
      if (doc.pages.isEmpty) {
        doc.dispose();
        return null;
      }
      final idx = pageIndex.clamp(0, doc.pages.length - 1);
      final page = doc.pages[idx];
      final scale = targetWidth / page.width;
      final image = await page.render(
        fullWidth: page.width * scale,
        fullHeight: page.height * scale,
        backgroundColor: const Color(0xFFFFFFFF),
      );
      if (image == null) {
        doc.dispose();
        return null;
      }
      final bytes =
          await _renderImageToBytes(image, (page.width * scale).toInt(),
              (page.height * scale).toInt());
      doc.dispose();
      return bytes;
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Get page count via pdfrx (no password needed for preview)
  // ---------------------------------------------------------------------------
  static Future<int> getPreviewPageCount(String pdfPath) async {
    try {
      final doc = await rx.PdfDocument.openFile(pdfPath);
      final count = doc.pages.length;
      doc.dispose();
      return count;
    } catch (_) {
      return 1;
    }
  }

  // ---------------------------------------------------------------------------
  // Watermark
  // ---------------------------------------------------------------------------
  static Future<void> addWatermark(
    String inputPath,
    String outputPath,
    String text, {
    double opacity = 0.3,
    double rotation = -45,
    String color = '#808080',
    String position = 'center',
    String frequency = 'all',
  }) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);

    final pdfColor = _hexToColor(color);
    final brush = PdfSolidBrush(pdfColor);
    final font = PdfStandardFont(PdfFontFamily.helvetica, 48,
        style: PdfFontStyle.bold);

    final pageCount = doc.pages.count;
    final pageIndices = _resolveFrequency(frequency, pageCount);

    for (final idx in pageIndices) {
      final page = doc.pages[idx];
      final graphics = page.graphics;
      graphics.save();
      graphics.setTransparency(opacity);

      final textSize = font.measureString(text);
      final pw = page.size.width;
      final ph = page.size.height;

      if (position == 'grid') {
        for (double x = -pw; x < pw * 2; x += textSize.width + 80) {
          for (double y = -ph; y < ph * 2; y += textSize.height + 80) {
            graphics.translateTransform(x + pw / 2, y + ph / 2);
            graphics.rotateTransform(rotation);
            graphics.drawString(text, font,
                brush: brush,
                bounds: Rect.fromLTWH(-textSize.width / 2,
                    -textSize.height / 2, textSize.width, textSize.height));
            graphics.rotateTransform(-rotation);
            graphics.translateTransform(-(x + pw / 2), -(y + ph / 2));
          }
        }
      } else {
        final ox = _resolvePositionX(position, pw, ph, textSize);
        final oy = _resolvePositionY(position, pw, ph, textSize);
        graphics.translateTransform(ox, oy);
        graphics.rotateTransform(rotation);
        graphics.drawString(text, font,
            brush: brush,
            bounds: Rect.fromLTWH(-textSize.width / 2, -textSize.height / 2,
                textSize.width, textSize.height));
      }

      graphics.restore();
    }

    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  static double _resolvePositionX(
      String position, double pw, double ph, Size textSize) {
    switch (position) {
      case 'top-left':
        return textSize.width / 2 + 40;
      case 'top-right':
        return pw - textSize.width / 2 - 40;
      case 'bottom-left':
        return textSize.width / 2 + 40;
      case 'bottom-right':
        return pw - textSize.width / 2 - 40;
      default:
        return pw / 2;
    }
  }

  static double _resolvePositionY(
      String position, double pw, double ph, Size textSize) {
    switch (position) {
      case 'top-left':
      case 'top-right':
        return textSize.height / 2 + 40;
      case 'bottom-left':
      case 'bottom-right':
        return ph - textSize.height / 2 - 40;
      default:
        return ph / 2;
    }
  }

  // ---------------------------------------------------------------------------
  // Image watermark
  // ---------------------------------------------------------------------------
  static Future<void> addImageWatermark(
    String inputPath,
    String outputPath,
    Uint8List imageBytes, {
    double opacity = 0.3,
    double rotation = -45,
    String position = 'center',
    String frequency = 'all',
    double scale = 0.3,
  }) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);
    final bitmap = PdfBitmap(imageBytes);
    final pageCount = doc.pages.count;
    final pageIndices = _resolveFrequency(frequency, pageCount);

    for (final idx in pageIndices) {
      final page = doc.pages[idx];
      final graphics = page.graphics;
      final pw = page.size.width;
      final ph = page.size.height;
      final imgW = bitmap.width * scale;
      final imgH = bitmap.height * scale;

      final ox = _resolvePositionX(position, pw, ph, Size(imgW, imgH));
      final oy = _resolvePositionY(position, pw, ph, Size(imgW, imgH));

      graphics.save();
      graphics.setTransparency(opacity);
      if (position == 'grid') {
        for (double x = -pw; x < pw * 2; x += imgW + 60) {
          for (double y = -ph; y < ph * 2; y += imgH + 60) {
            graphics.translateTransform(x + pw / 2, y + ph / 2);
            graphics.rotateTransform(rotation);
            graphics.drawImage(
                bitmap, Rect.fromLTWH(-imgW / 2, -imgH / 2, imgW, imgH));
            graphics.rotateTransform(-rotation);
            graphics.translateTransform(-(x + pw / 2), -(y + ph / 2));
          }
        }
      } else {
        graphics.translateTransform(ox, oy);
        graphics.rotateTransform(rotation);
        graphics.drawImage(
            bitmap, Rect.fromLTWH(-imgW / 2, -imgH / 2, imgW, imgH));
      }
      graphics.restore();
    }

    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  static List<int> _resolveFrequency(String frequency, int pageCount) {
    switch (frequency) {
      case 'first':
        return pageCount > 0 ? [0] : [];
      case 'last':
        return pageCount > 0 ? [pageCount - 1] : [];
      default:
        return List.generate(pageCount, (i) => i);
    }
  }

  // ---------------------------------------------------------------------------
  // Split
  // ---------------------------------------------------------------------------
  static Future<List<String>> splitPdf(
    String inputPath,
    String outputDir,
    String ranges,
  ) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);
    final totalPages = doc.pages.count;
    final parsedRanges = _parseRanges(ranges, totalPages);
    final outputPaths = <String>[];
    final baseName = p.basenameWithoutExtension(inputPath);

    for (int r = 0; r < parsedRanges.length; r++) {
      final range = parsedRanges[r];
      final newDoc = PdfDocument();
      for (final pageIdx in range) {
        if (pageIdx < totalPages) {
          final srcPage = doc.pages[pageIdx];
          final section = newDoc.sections!.add();
          section.pageSettings.size = srcPage.size;
          section.pageSettings.margins.all = 0;
          final newPage = section.pages.add();
          final template = srcPage.createTemplate();
          newPage.graphics.drawPdfTemplate(template, Offset.zero);
        }
      }

      final outFileName =
          '${baseName}_part${r + 1}_pages${range.first + 1}-${range.last + 1}.pdf';
      final outPath = p.join(outputDir, outFileName);
      final outBytes = newDoc.saveSync();
      newDoc.dispose();
      await File(outPath).writeAsBytes(outBytes);
      outputPaths.add(outPath);
    }

    doc.dispose();
    return outputPaths;
  }

  static List<List<int>> _parseRanges(String rangesStr, int totalPages) {
    final result = <List<int>>[];
    final parts = rangesStr.split(',');
    for (final part in parts) {
      final trimmed = part.trim();
      if (trimmed.isEmpty) continue;
      if (trimmed.contains('-')) {
        final bounds = trimmed.split('-');
        if (bounds.length == 2) {
          final start = (int.tryParse(bounds[0].trim()) ?? 1) - 1;
          final end = (int.tryParse(bounds[1].trim()) ?? totalPages) - 1;
          if (start <= end && start >= 0 && end < totalPages) {
            result.add(List.generate(end - start + 1, (i) => start + i));
          }
        }
      } else {
        final page = (int.tryParse(trimmed) ?? 1) - 1;
        if (page >= 0 && page < totalPages) {
          result.add([page]);
        }
      }
    }
    return result.isEmpty ? [List.generate(totalPages, (i) => i)] : result;
  }

  // ---------------------------------------------------------------------------
  // PDF to Images (uses pdfrx for rendering)
  // ---------------------------------------------------------------------------
  static Future<List<String>> pdfToImages(
    String inputPath,
    String outputDir,
    int dpi,
  ) async {
    final doc = await rx.PdfDocument.openFile(inputPath);
    final outputPaths = <String>[];
    final baseName = p.basenameWithoutExtension(inputPath);
    final scale = dpi / 72.0;

    for (int i = 0; i < doc.pages.length; i++) {
      final page = doc.pages[i];
      final width = page.width * scale;
      final height = page.height * scale;
      final image = await page.render(
        fullWidth: width,
        fullHeight: height,
        backgroundColor: const Color(0xFFFFFFFF),
      );
      if (image == null) continue;

      final pngBytes =
          await _renderImageToBytes(image, width.toInt(), height.toInt());
      final outPath = p.join(outputDir, '${baseName}_page${i + 1}.png');
      await File(outPath).writeAsBytes(pngBytes);
      outputPaths.add(outPath);
    }

    doc.dispose();
    return outputPaths;
  }

  static Future<Uint8List> _renderImageToBytes(
      rx.PdfImage image, int width, int height) async {
    final pixels = image.pixels;
    final codec = await ImageDescriptor.raw(
      await ImmutableBuffer.fromUint8List(pixels),
      width: width,
      height: height,
      pixelFormat: PixelFormat.rgba8888,
    ).instantiateCodec();
    final frame = await codec.getNextFrame();
    final byteData =
        await frame.image.toByteData(format: ImageByteFormat.png);
    return byteData!.buffer.asUint8List();
  }

  // ---------------------------------------------------------------------------
  // Images to PDF
  // ---------------------------------------------------------------------------
  static Future<void> imagesToPdf(
      List<String> imagePaths, String outputPath) async {
    final doc = PdfDocument();

    for (final imgPath in imagePaths) {
      final imgBytes = await File(imgPath).readAsBytes();
      final bitmap = PdfBitmap(imgBytes);
      final imgWidth = bitmap.width.toDouble();
      final imgHeight = bitmap.height.toDouble();
      const a4Width = 595.0;
      const a4Height = 842.0;
      final scaleX = a4Width / imgWidth;
      final scaleY = a4Height / imgHeight;
      final scale = scaleX < scaleY ? scaleX : scaleY;
      final drawWidth = imgWidth * scale;
      final drawHeight = imgHeight * scale;
      final section = doc.sections!.add();
      section.pageSettings.size = Size(drawWidth, drawHeight);
      section.pageSettings.margins.all = 0;
      final page = section.pages.add();
      page.graphics
          .drawImage(bitmap, Rect.fromLTWH(0, 0, drawWidth, drawHeight));
    }

    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // Annotate / Sign
  // ---------------------------------------------------------------------------
  static Future<void> annotate(
    String inputPath,
    String outputPath,
    List<Map<String, dynamic>> textItems,
    Uint8List? sigBytes,
    double sigX,
    double sigY,
    int fontSize,
    String color,
    String frequency,
  ) async {
    final bytes = await File(inputPath).readAsBytes();
    final doc = PdfDocument(inputBytes: bytes);
    final pageCount = doc.pages.count;
    final pageIndices = _resolveFrequency(frequency, pageCount);
    final pdfColor = _hexToColor(color);
    final font = PdfStandardFont(PdfFontFamily.helvetica, fontSize.toDouble());
    final brush = PdfSolidBrush(pdfColor);

    for (final idx in pageIndices) {
      final page = doc.pages[idx];
      final pw = page.size.width;
      final ph = page.size.height;
      final graphics = page.graphics;

      for (final item in textItems) {
        final text = (item['text'] as String?) ?? '';
        final fx = (item['x'] as num?)?.toDouble() ?? 0.5;
        final fy = (item['y'] as num?)?.toDouble() ?? 0.5;
        if (text.isEmpty) continue;
        final textSize = font.measureString(text);
        final x = fx * pw - textSize.width / 2;
        final y = fy * ph - textSize.height / 2;
        graphics.drawString(text, font,
            brush: brush,
            bounds: Rect.fromLTWH(x, y, textSize.width, textSize.height));
      }

      if (sigBytes != null) {
        final sigBitmap = PdfBitmap(sigBytes);
        const sigW = 150.0;
        const sigH = 60.0;
        final sx = sigX * pw - sigW / 2;
        final sy = sigY * ph - sigH / 2;
        graphics.drawImage(sigBitmap, Rect.fromLTWH(sx, sy, sigW, sigH));
      }
    }

    final outBytes = doc.saveSync();
    doc.dispose();
    await File(outputPath).writeAsBytes(outBytes);
  }

  // ---------------------------------------------------------------------------
  // PDF to Word (LibreOffice)
  // ---------------------------------------------------------------------------
  static Future<void> pdfToWord(String inputPath, String outputPath) async {
    final outDir = p.dirname(outputPath);
    final ProcessResult result;
    try {
      result = await Process.run(
        _libreOfficeExecutable(),
        ['--headless', '--convert-to', 'docx', '--outdir', outDir, inputPath],
      );
    } on ProcessException {
      throw Exception(
          'LibreOffice not found. Install LibreOffice to use this feature.');
    }
    if (result.exitCode != 0) {
      throw Exception(
          'LibreOffice not found or conversion failed. '
          'Install LibreOffice to use this feature.\n${result.stderr}');
    }
    final expectedOut =
        p.join(outDir, '${p.basenameWithoutExtension(inputPath)}.docx');
    if (expectedOut != outputPath && await File(expectedOut).exists()) {
      await File(expectedOut).rename(outputPath);
    }
  }

  // ---------------------------------------------------------------------------
  // Word to PDF (LibreOffice)
  // ---------------------------------------------------------------------------
  static Future<void> wordToPdf(String inputPath, String outputPath) async {
    final outDir = p.dirname(outputPath);
    final ProcessResult result;
    try {
      result = await Process.run(
        _libreOfficeExecutable(),
        ['--headless', '--convert-to', 'pdf', '--outdir', outDir, inputPath],
      );
    } on ProcessException {
      throw Exception(
          'LibreOffice not found. Install LibreOffice to use this feature.');
    }
    if (result.exitCode != 0) {
      throw Exception(
          'LibreOffice not found or conversion failed. '
          'Install LibreOffice to use this feature.\n${result.stderr}');
    }
    final expectedOut =
        p.join(outDir, '${p.basenameWithoutExtension(inputPath)}.pdf');
    if (expectedOut != outputPath && await File(expectedOut).exists()) {
      await File(expectedOut).rename(outputPath);
    }
  }

  // ---------------------------------------------------------------------------
  // Get page count
  // ---------------------------------------------------------------------------
  static Future<int> getPageCount(String pdfPath,
      {String password = ''}) async {
    final bytes = await File(pdfPath).readAsBytes();
    final doc = password.isEmpty
        ? PdfDocument(inputBytes: bytes)
        : PdfDocument(inputBytes: bytes, password: password);
    final count = doc.pages.count;
    doc.dispose();
    return count;
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  static PdfColor _hexToColor(String hex) {
    final cleaned = hex.replaceAll('#', '');
    if (cleaned.length == 6) {
      final r = int.parse(cleaned.substring(0, 2), radix: 16);
      final g = int.parse(cleaned.substring(2, 4), radix: 16);
      final b = int.parse(cleaned.substring(4, 6), radix: 16);
      return PdfColor(r, g, b);
    }
    return PdfColor(128, 128, 128);
  }

  static String _libreOfficeExecutable() {
    if (Platform.isMacOS) {
      // Bundled inside the app (Contents/Resources/LibreOffice.app), if present.
      final contentsDir =
          p.dirname(p.dirname(Platform.resolvedExecutable));
      final bundledApp =
          p.join(contentsDir, 'Resources', 'LibreOffice.app');
      final bundledPath =
          p.join(bundledApp, 'Contents', 'MacOS', 'soffice');
      if (File(bundledPath).existsSync()) {
        _clearQuarantine(bundledApp);
        return bundledPath;
      }
      const macPath =
          '/Applications/LibreOffice.app/Contents/MacOS/soffice';
      if (File(macPath).existsSync()) return macPath;
      return 'libreoffice';
    }

    // Windows/Linux: bundled next to the app as <exeDir>/libreoffice/program/.
    final exeDir = p.dirname(Platform.resolvedExecutable);
    if (Platform.isWindows) {
      final bundled = p.join(exeDir, 'libreoffice', 'program', 'soffice.exe');
      if (File(bundled).existsSync()) return bundled;
      return 'soffice.exe';
    }
    final bundled = p.join(exeDir, 'libreoffice', 'program', 'soffice');
    if (File(bundled).existsSync()) return bundled;
    return 'libreoffice';
  }

  // Downloaded/zipped apps carry com.apple.quarantine, which Gatekeeper
  // enforces even when a bundled binary is launched via Process.run rather
  // than double-clicked. Strip it once so the bundled LibreOffice doesn't
  // hit its own Gatekeeper prompt the first time it's used.
  static bool _quarantineCleared = false;
  static void _clearQuarantine(String appPath) {
    if (_quarantineCleared) return;
    _quarantineCleared = true;
    try {
      Process.runSync('xattr', ['-dr', 'com.apple.quarantine', appPath]);
    } catch (_) {
      // Best-effort; if this fails the user still gets a normal Gatekeeper prompt.
    }
  }
}
