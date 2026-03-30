import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static const String baseUrl = 'http://localhost:5000';

  static Map<String, String> get _headers => {
    'Content-Type': 'application/json',
  };

  static Future<Map<String, dynamic>> login(String person, String pass) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/admin/login'),
        headers: _headers,
        body: jsonEncode({'personname': person, 'password': pass}),
      );
      return jsonDecode(res.body);
    } catch (e) { return {'success': false, 'message': 'Auth Error'}; }
  }

  static Future<Map<String, dynamic>> verifyFace(String b64) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/api/verify'),
        headers: _headers,
        body: jsonEncode({'image': b64}),
      );
      return jsonDecode(res.body);
    } catch (e) { return {'success': false, 'message': 'Verify Error'}; }
  }

  static Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    try {
      final res = await http.post(
        Uri.parse('$baseUrl/api/register'),
        headers: _headers,
        body: jsonEncode(data),
      );
      return jsonDecode(res.body);
    } catch (e) { return {'success': false, 'message': 'Reg Error'}; }
  }

  static Future<Map<String, dynamic>> getDashboardData() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/dashboard-data'), headers: _headers);
      return jsonDecode(res.body);
    } catch (e) { return {'success': false}; }
  }

  static Future<Map<String, dynamic>> getAdminDashboardData() async {
    try {
      final res = await http.get(Uri.parse('$baseUrl/api/admin-dashboard-data'), headers: _headers);
      return jsonDecode(res.body);
    } catch (e) { return {'success': false}; }
  }

  static Future<Map<String, dynamic>> checkIn() async {
    try {
      final res = await http.post(Uri.parse('$baseUrl/api/checkin'), headers: _headers);
      return jsonDecode(res.body);
    } catch (e) { return {'success': false}; }
  }

  static Future<Map<String, dynamic>> checkOut() async {
    try {
      final res = await http.post(Uri.parse('$baseUrl/api/checkout'), headers: _headers);
      return jsonDecode(res.body);
    } catch (e) { return {'success': false}; }
  }

  static Future<void> submitLateReason(String reason) async {
    await http.post(Uri.parse('$baseUrl/api/late-reason'), headers: _headers, body: jsonEncode({'reason': reason}));
  }

  static Future<Map<String, dynamic>> submitLeave(Map<String, dynamic> data) async {
    final res = await http.post(Uri.parse('$baseUrl/api/leave-request'), headers: _headers, body: jsonEncode(data));
    return jsonDecode(res.body);
  }

  static Future<void> approveLeave(int id) async {
    await http.post(Uri.parse('$baseUrl/api/admin/leave/$id/approve'), headers: _headers);
  }

  static Future<void> rejectLeave(int id) async {
    await http.post(Uri.parse('$baseUrl/api/admin/leave/$id/reject'), headers: _headers);
  }

  static Future<void> createMeeting(Map<String, dynamic> data) async {
    await http.post(Uri.parse('$baseUrl/api/admin/meeting'), headers: _headers, body: jsonEncode(data));
  }

  static Future<void> deleteMeeting(int id) async {
    await http.delete(Uri.parse('$baseUrl/api/admin/meeting/$id'), headers: _headers);
  }

  static Future<void> deleteEmployee(String id) async {
    await http.delete(Uri.parse('$baseUrl/api/admin/employee/$id'), headers: _headers);
  }
}
