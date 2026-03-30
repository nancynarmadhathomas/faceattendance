class Meeting {
  final int id;
  final String title;
  final String? description;
  final String date;
  final String time;
  final String? employeeId;

  Meeting({
    required this.id,
    required this.title,
    this.description,
    required this.date,
    required this.time,
    this.employeeId,
  });

  factory Meeting.fromJson(Map<String, dynamic> json) {
    return Meeting(
      id: json['id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'],
      date: json['meeting_date'] ?? '',
      time: json['meeting_time'] ?? '',
      employeeId: json['employee_id'],
    );
  }
}
