class Contributor {
  final String name;
  final String role;
  final String? linkedIn;
  final String? github;
  final String? twitter;
  final String? website;
  final String? description;

  const Contributor({
    required this.name,
    required this.role,
    this.linkedIn,
    this.github,
    this.twitter,
    this.website,
    this.description,
  });
}
