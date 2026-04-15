import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../models/contributor.dart';

class ContributorsScreen extends StatelessWidget {
  const ContributorsScreen({super.key});

  static const List<Contributor> _contributors = [
    Contributor(
      name: 'Israel Isiaka',
      role: 'Technical PM & Software Engineer',
      github: 'https://github.com/israelIsiaka',
      linkedIn: 'https://www.linkedin.com/in/isrealisiaka/',
      description:
          'A lifelong learner with a background in computer science.',
    ),
    Contributor(
      name: 'Precious Osokogu',
      role: 'Creative Designer & Contributor',
      linkedIn: 'https://www.linkedin.com/in/preciousosokogu',
      twitter: 'https://x.com/Ajizglow',
      website: 'https://zurifycreativehub.com/',
      description:
          'Creative director and designer at Zurify Creative Hub. Brings design thinking and creative vision to the project.',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return AppScaffold(
      title: 'Contributors',
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Color(0xFF8b5cf6).withAlpha(30),
                    Color(0xFF4f7ef7).withAlpha(15),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                    color: Color(0xFF8b5cf6).withAlpha(50)),
              ),
              child: Column(
                children: [
                  Icon(Icons.people_alt_rounded,
                      size: 40, color: Color(0xFF8b5cf6)),
                  SizedBox(height: 12),
                  Text(
                    'Built with care',
                    style: TextStyle(
                      color: c.textPrimary,
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 6),
                  Text(
                    'PDF Merger is an open-source project. '
                    'Every contribution matters.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: c.textSecondary,
                      fontSize: 13,
                      height: 1.5,
                    ),
                  ),
                  SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: () => _launch(
                        'https://github.com/israelIsiaka/pdf-merger'),
                    icon: Icon(Icons.code_rounded, size: 16),
                    label: Text('View on GitHub'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Color(0xFF8b5cf6),
                      side: BorderSide(
                          color: Color(0xFF8b5cf6), width: 1),
                    ),
                  ),
                ],
              ),
            ),

            SizedBox(height: 28),
            Text('Team',
                style: TextStyle(
                    color: c.textPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 16)),
            SizedBox(height: 12),

            ..._contributors.map((contrib) => Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: _ContributorCard(contributor: contrib),
                )),

            SizedBox(height: 28),
            Divider(),
            SizedBox(height: 20),

            // Want to contribute
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: c.cardBackground,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: c.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.volunteer_activism_rounded,
                          size: 18, color: Color(0xFF22c55e)),
                      SizedBox(width: 8),
                      Text(
                        'Want to contribute?',
                        style: TextStyle(
                          color: c.textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    'PDF Merger welcomes contributions of all kinds — '
                    'bug fixes, new features, translations, or documentation improvements.',
                    style: TextStyle(
                        color: c.textSecondary,
                        fontSize: 13,
                        height: 1.5),
                  ),
                  SizedBox(height: 12),
                  TextButton.icon(
                    onPressed: () => _launch(
                        'https://github.com/israelIsiaka/pdf-merger/issues'),
                    icon: Icon(Icons.open_in_new_rounded, size: 14),
                    label: Text('Open an issue or pull request'),
                    style: TextButton.styleFrom(
                        foregroundColor: Color(0xFF22c55e)),
                  ),
                ],
              ),
            ),

            SizedBox(height: 20),

            // Support the project
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Color(0xFFf59e0b).withAlpha(25),
                    Color(0xFFef4444).withAlpha(15),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Color(0xFFf59e0b).withAlpha(60)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.favorite_rounded,
                          size: 18, color: Color(0xFFf59e0b)),
                      SizedBox(width: 8),
                      Text(
                        'Support the project',
                        style: TextStyle(
                          color: c.textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  Text(
                    'PDF Merger is free and always will be. If it saves you time '
                    'or you would like to request a feature, consider supporting '
                    'the project — any amount means a lot.',
                    style: TextStyle(
                        color: c.textSecondary, fontSize: 13, height: 1.5),
                  ),
                  SizedBox(height: 16),
                  Row(
                    children: [
                      _SupportButton(
                        icon: Icons.coffee_rounded,
                        label: 'Buy Me a Coffee',
                        url: 'https://buymeacoffee.com/placeholder',
                        color: Color(0xFFf59e0b),
                      ),
                      SizedBox(width: 10),
                      _SupportButton(
                        icon: Icons.favorite_border_rounded,
                        label: 'GitHub Sponsors',
                        url: 'https://github.com/sponsors/placeholder',
                        color: Color(0xFFec4899),
                      ),
                      SizedBox(width: 10),
                      _SupportButton(
                        icon: Icons.attach_money_rounded,
                        label: 'PayPal',
                        url: 'https://paypal.me/placeholder',
                        color: Color(0xFF4f7ef7),
                      ),
                    ],
                  ),
                ],
              ),
            ),

            SizedBox(height: 20),

            // License
            Container(
              width: double.infinity,
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: c.cardBackground,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: c.cardBorder),
              ),
              child: Row(
                children: [
                  Icon(Icons.gavel_rounded,
                      size: 16, color: c.textSecondary),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Released under the MIT License. Free for personal and commercial use.',
                      style: TextStyle(
                          color: c.textSecondary,
                          fontSize: 12,
                          height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> _launch(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }
}

class _ContributorCard extends StatelessWidget {
  final Contributor contributor;
  const _ContributorCard({required this.contributor});

  @override
  Widget build(BuildContext context) {
    final c = AppColors.of(context);
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: c.cardBackground,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: c.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // Avatar initials
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF8b5cf6), Color(0xFF4f7ef7)],
                  ),
                  borderRadius: BorderRadius.circular(22),
                ),
                child: Center(
                  child: Text(
                    contributor.name
                        .split(' ')
                        .map((w) => w.isNotEmpty ? w[0] : '')
                        .take(2)
                        .join(),
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      contributor.name,
                      style: TextStyle(
                        color: c.textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 14,
                      ),
                    ),
                    SizedBox(height: 2),
                    Text(
                      contributor.role,
                      style: TextStyle(
                          color: Color(0xFF8b5cf6), fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (contributor.description != null) ...[
            SizedBox(height: 10),
            Text(
              contributor.description!,
              style: TextStyle(
                  color: c.textSecondary,
                  fontSize: 13,
                  height: 1.5),
            ),
          ],
          SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (contributor.github != null)
                _LinkButton(
                  icon: Icons.code_rounded,
                  label: 'GitHub',
                  url: contributor.github!,
                  color: const Color(0xFF4f7ef7),
                ),
              if (contributor.linkedIn != null)
                _LinkButton(
                  icon: Icons.work_outline_rounded,
                  label: 'LinkedIn',
                  url: contributor.linkedIn!,
                  color: const Color(0xFF22d3ee),
                ),
              if (contributor.twitter != null)
                _LinkButton(
                  icon: Icons.alternate_email_rounded,
                  label: 'Twitter / X',
                  url: contributor.twitter!,
                  color: const Color(0xFF64748b),
                ),
              if (contributor.website != null)
                _LinkButton(
                  icon: Icons.language_rounded,
                  label: 'Website',
                  url: contributor.website!,
                  color: const Color(0xFF22c55e),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _LinkButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String url;
  final Color color;

  const _LinkButton({
    required this.icon,
    required this.label,
    required this.url,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () async {
        final uri = Uri.parse(url);
        if (await canLaunchUrl(uri)) await launchUrl(uri);
      },
      icon: Icon(icon, size: 14),
      label: Text(label, style: TextStyle(fontSize: 12)),
      style: OutlinedButton.styleFrom(
        foregroundColor: color,
        side: BorderSide(color: color.withAlpha(80)),
        padding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}

class _SupportButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final String url;
  final Color color;

  const _SupportButton({
    required this.icon,
    required this.label,
    required this.url,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () async {
        final uri = Uri.parse(url);
        if (await canLaunchUrl(uri)) await launchUrl(uri);
      },
      icon: Icon(icon, size: 15),
      label: Text(label, style: const TextStyle(fontSize: 12)),
      style: OutlinedButton.styleFrom(
        foregroundColor: color,
        side: BorderSide(color: color.withAlpha(100)),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        minimumSize: Size.zero,
        tapTargetSize: MaterialTapTargetSize.shrinkWrap,
      ),
    );
  }
}
