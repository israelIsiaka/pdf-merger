class HistoryEntry {
  final String operation;
  final String outputPath;
  final DateTime timestamp;

  HistoryEntry({
    required this.operation,
    required this.outputPath,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
        'operation': operation,
        'outputPath': outputPath,
        'timestamp': timestamp.toIso8601String(),
      };

  factory HistoryEntry.fromJson(Map<String, dynamic> j) => HistoryEntry(
        operation: j['operation'] as String,
        outputPath: j['outputPath'] as String,
        timestamp: DateTime.parse(j['timestamp'] as String),
      );
}
