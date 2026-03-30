class LeaveRequest {
  final int id;
  final String employeeId;
  final String? employeeName;
  final String leaveType;
  final String fromDate;
  final String toDate;
  final String? reason;
  final String status;
  final String? department;

  LeaveRequest({
    required this.id,
    required this.employeeId,
    this.employeeName,
    required this.leaveType,
    required this.fromDate,
    required this.toDate,
    this.reason,
    required this.status,
    this.department,
  });

  factory LeaveRequest.fromJson(Map<String, dynamic> json) {
    return LeaveRequest(
      id: json['id'] ?? 0,
      employeeId: json['employee_id'] ?? '',
      employeeName: json['employee_name'],
      leaveType: json['leave_type'] ?? '',
      fromDate: json['from_date'] ?? '',
      toDate: json['to_date'] ?? '',
      reason: json['reason'],
      status: json['status'] ?? 'Pending',
      department: json['department'],
    );
  }
}
