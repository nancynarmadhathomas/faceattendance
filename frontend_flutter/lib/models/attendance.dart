class AttendanceRecord {
  final String date;
  final String? checkIn;
  final String? checkOut;
  final String? workingHours;
  final String status;
  final String? lateReason;
  final String? name; // For admin view
  final String? employeeId; // For admin view
  final String? department; // For admin view

  AttendanceRecord({
    required this.date,
    this.checkIn,
    this.checkOut,
    this.workingHours,
    required this.status,
    this.lateReason,
    this.name,
    this.employeeId,
    this.department,
  });

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) {
    return AttendanceRecord(
      date: json['date'] ?? '',
      checkIn: json['check_in'],
      checkOut: json['check_out'],
      workingHours: json['working_hours']?.toString(),
      status: json['status'] ?? 'absent',
      lateReason: json['late_reason'],
      name: json['name'],
      employeeId: json['employee_id'],
      department: json['department'],
    );
  }
}
