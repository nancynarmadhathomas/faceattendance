class Employee {
  final String employeeId;
  final String name;
  final String? email;
  final String? department;
  final String? role;
  final String? createdAt;
  final String? faceImage;

  Employee({
    required this.employeeId,
    required this.name,
    this.email,
    this.department,
    this.role,
    this.createdAt,
    this.faceImage,
  });

  factory Employee.fromJson(Map<String, dynamic> json) {
    return Employee(
      employeeId: json['employee_id'] ?? '',
      name: json['name'] ?? '',
      email: json['email'],
      department: json['department'],
      role: json['role'] ?? 'employee',
      createdAt: json['created_at'],
      faceImage: json['face_image'],
    );
  }

  Map<String, dynamic> toJson() => {
    'employee_id': employeeId,
    'name': name,
    'email': email,
    'department': department,
    'role': role,
    'created_at': createdAt,
    'face_image': faceImage,
  };
}
