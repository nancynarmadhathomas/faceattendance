import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_lucide/flutter_Icons.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';
import '../theme.dart';
import '../services/api_service.dart';
import '../models/employee.dart';
import '../models/attendance.dart';
import '../models/meeting.dart';
import '../models/leave.dart';

class AdminDashboard extends StatefulWidget {
  const AdminDashboard({super.key});

  @override
  State<AdminDashboard> createState() => _AdminDashboardState();
}

class _AdminDashboardState extends State<AdminDashboard> {
  String _activeTab = 'attendance';
  bool _isLoading = true;

  Map<String, dynamic> _stats = {};
  List<Employee> _employees = [];
  List<AttendanceRecord> _attendToday = [];
  List<AttendanceRecord> _recentAtt = [];
  List<Meeting> _meetings = [];
  List<LeaveRequest> _leaveReqs = [];

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    final res = await ApiService.getAdminDashboardData();
    if (res['success'] == true) {
      setState(() {
        _stats = res['stats'] ?? {};
        _employees = (res['employees'] as List).map((e) => Employee.fromJson(e)).toList();
        _attendToday = (res['attend_today'] as List).map((e) => AttendanceRecord.fromJson(e)).toList();
        _recentAtt = (res['recent_att'] as List).map((e) => AttendanceRecord.fromJson(e)).toList();
        _meetings = (res['meetings'] as List).map((e) => Meeting.fromJson(e)).toList();
        _leaveReqs = (res['leave_reqs'] as List).map((e) => LeaveRequest.fromJson(e)).toList();
        _isLoading = false;
      });
    } else {
      if (mounted) Navigator.pushReplacementNamed(context, '/');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    
    // ignore: unused_local_variable
    final themeProvider = Provider.of<ThemeProvider>(context, listen: false);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Row(
        children: [
          _buildSidebar(),
          Expanded(
            child: Column(
              children: [
                _buildNavbar(),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildStatCards(),
                        const SizedBox(height: 28),
                        _buildActiveTab(),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: 260,
      color: isDark ? AppColors.sidebarBg : AppColors.lightSurface,
      decoration: BoxDecoration(
        border: Border(right: BorderSide(color: isDark ? AppColors.border : AppColors.lightBorder)),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: isDark ? AppColors.border : AppColors.lightBorder)),
            ),
            child: Row(
              children: [
                const Icon(Icons.verified, color: AppColors.primaryLight, size: 24),
                const SizedBox(width: 12),
                const Text('Admin Panel', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Column(
              children: [
                _buildNavBtn('attendance', Icons.assignment, 'Attendance'),
                _buildNavBtn('employees', Icons.persons, 'Employees'),
                _buildNavBtn('meetings', Icons.calendar_today, 'Meetings'),
                _buildNavBtn('leaves', Icons.description, 'Leaves',
                    badge: _leaveReqs.where((l) => l.status == 'Pending').length),
              ],
            ),
          ),
          const Spacer(),
          Padding(
            padding: const EdgeInsets.all(12),
            child: _buildNavBtn('logout', Icons.logout, 'logout', color: AppColors.danger),
          ),
        ],
      ),
    );
  }

  Widget _buildNavBtn(String id, IconData icon, String label, {int? badge, Color? color}) {
    bool active = _activeTab == id;
    return GestureDetector(
      onTap: () {
        if (id == 'logout') {
          Navigator.pushReplacementNamed(context, '/');
        } else {
          setState(() => _activeTab = id);
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        margin: const EdgeInsets.only(bottom: 4),
        decoration: BoxDecoration(
          color: active ? AppColors.primaryGlow : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: active ? AppColors.primaryLight : (color ?? AppColors.muted)),
            const SizedBox(width: 12),
            Text(label,
                style: TextStyle(
                    fontSize: 14,
                    fontWeight: active ? FontWeight.bold : FontWeight.w500,
                    color: active ? AppColors.primaryLight : (color ?? AppColors.muted))),
            if (badge != null && badge > 0) ...[
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: AppColors.warning, borderRadius: BorderRadius.circular(999)),
                child: Text('$badge',
                    style: const TextStyle(color: Colors.black, fontSize: 11, fontWeight: FontWeight.bold)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildNavbar() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 0),
      height: 60,
      decoration: BoxDecoration(
        color: isDark ? AppColors.sidebarBg : AppColors.lightSurface,
        border: Border(bottom: BorderSide(color: isDark ? AppColors.border : AppColors.lightBorder)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          RichText(
            text: TextSpan(
              text: 'Face',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Theme.of(context).textTheme.bodyLarge?.color),
              children: [
                const TextSpan(text: 'Attend', style: TextStyle(color: AppColors.primaryLight)),
                TextSpan(text: ' · Admin', style: TextStyle(fontWeight: FontWeight.normal, color: isDark ? AppColors.muted : AppColors.lightMuted)),
              ],
            ),
          ),
          ElevatedButton.icon(
            onPressed: _showMeetingModal,
            icon: const Icon(Icons.plus, size: 14),
            label: const Text('New Meeting'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCards() {
    return Row(
      children: [
        _buildStatCard('Total Employees', _stats['total']?.toString() ?? '0', Icons.persons, AppColors.primary),
        const SizedBox(width: 16),
        _buildStatCard('Present Today', _stats['present']?.toString() ?? '0', Icons.person_round_check, AppColors.success),
        const SizedBox(width: 16),
        _buildStatCard('Absent Today', _stats['absent']?.toString() ?? '0', Icons.person_round_x, AppColors.danger),
        const SizedBox(width: 16),
        _buildStatCard('Late Today', _stats['late']?.toString() ?? '0', Icons.alert_triangle, AppColors.warning),
      ],
    );
  }

  Widget _buildStatCard(String label, String val, IconData icon, Color color) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        decoration: BoxDecoration(
          color: isDark ? AppColors.cardBg : AppColors.lightSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: isDark ? AppColors.border : AppColors.lightBorder),
          boxShadow: [
            BoxShadow(color: color.withOpacity(0.05), blurRadius: 10, spreadRadius: 0),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 14, color: AppColors.muted),
                const SizedBox(width: 4),
                Text(label,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.muted, letterSpacing: 0.5, fontWeight: FontWeight.w500)),
              ],
            ),
            const SizedBox(height: 4),
            Text(val,
                style: TextStyle(
                    fontSize: 32, fontWeight: FontWeight.bold, color: color == AppColors.primary ? (isDark ? Colors.white : AppColors.primary) : color)),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveTab() {
    switch (_activeTab) {
      case 'attendance':
        return _buildAttendanceTab();
      case 'employees':
        return _buildEmployeesTab();
      case 'meetings':
        return _buildMeetingsTab();
      case 'leaves':
        return _buildLeavesTab();
      default:
        return Container();
    }
  }

  Widget _buildAttendanceTab() {
    return Column(
      children: [
        _buildTabHeader(Icons.assignment, 'Today\'s Attendance'),
        _buildAttendanceTable(_attendToday),
        const SizedBox(height: 40),
        _buildTabHeader(Icons.history, 'Recent Attendance (Last 10)'),
        _buildAttendanceTable(_recentAtt),
      ],
    );
  }

  Widget _buildTabHeader(IconData icon, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Icon(icon, size: 16, color: Theme.of(context).textTheme.bodyLarge?.color),
          const SizedBox(width: 6),
          Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
          const Spacer(),
          SizedBox(
            width: 220,
            child: TextField(
              decoration: const InputDecoration(
                hintText: 'Search...',
                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              ),
              style: const TextStyle(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAttendanceTable(List<AttendanceRecord> records) {
    return Card(
      child: Table(
        columnWidths: const {
          0: FlexColumnWidth(2.5),
          1: FlexColumnWidth(1.5),
          2: FlexColumnWidth(1.5),
          3: FlexColumnWidth(1),
          4: FlexColumnWidth(1.5),
        },
        children: [
          TableRow(
            decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
            children: ['Employee', 'Check In', 'Check Out', 'Hours', 'Status']
                .map((h) => Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(h.toUpperCase(),
                        style: const TextStyle(
                            color: AppColors.muted, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5))))
                .toList(),
          ),
          ...records.map((r) => TableRow(
                decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                children: [
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(r.name ?? 'Unknown', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        Text(r.employeeId ?? '', style: const TextStyle(color: AppColors.muted, fontSize: 11)),
                      ],
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(r.checkIn ?? '--:--',
                        style: const TextStyle(color: AppColors.success, fontFamily: 'monospace', fontSize: 13)),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(r.checkOut ?? '--:--',
                        style: const TextStyle(color: AppColors.muted, fontFamily: 'monospace', fontSize: 13)),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text('${r.workingHours ?? '--'}h',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: _buildBadge(r.status),
                  ),
                ],
              )),
          if (records.isEmpty)
            TableRow(children: [
              Container(),
              Container(),
              const Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(child: Text('No records found', style: TextStyle(color: AppColors.muted)))),
              Container(),
              Container(),
            ]),
        ],
      ),
    );
  }

  Widget _buildBadge(String status) {
    Color c = status == 'present' ? AppColors.success : (status == 'late' ? AppColors.warning : AppColors.danger);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(999)),
      child: Text(status.toUpperCase(),
          textAlign: TextAlign.center, style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildEmployeesTab() {
    return Column(
      children: [
        _buildTabHeader(Icons.persons, 'All Employees (${_employees.length})'),
        Card(
          child: Table(
            columnWidths: const {
              0: FlexColumnWidth(1),
              1: FlexColumnWidth(2),
              2: FlexColumnWidth(2),
              3: FlexColumnWidth(1.5),
              4: FlexColumnWidth(1.5),
              5: FlexColumnWidth(1),
            },
            children: [
              TableRow(
                decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                children: ['ID', 'Name', 'Email', 'Department', 'Joined', 'Actions']
                    .map((h) => Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(h.toUpperCase(),
                            style: const TextStyle(
                                color: AppColors.muted, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5))))
                    .toList(),
              ),
              ..._employees.map((e) => TableRow(
                    decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(e.employeeId,
                            style: const TextStyle(color: AppColors.primaryLight, fontFamily: 'monospace', fontSize: 13)),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(e.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(e.email ?? '—', style: const TextStyle(color: AppColors.muted, fontSize: 13)),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(e.department ?? '—', style: const TextStyle(fontSize: 13)),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(e.createdAt?.split('T')[0] ?? '—',
                            style: const TextStyle(color: AppColors.muted, fontSize: 12)),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: IconButton(
                          icon: const Icon(Icons.delete, size: 16, color: AppColors.danger),
                          onPressed: () async {
                            if (await _confirm('Delete employee ${e.employeeId}?')) {
                              await ApiService.deleteEmployee(e.employeeId);
                              _fetchData();
                            }
                          },
                        ),
                      ),
                    ],
                  )),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMeetingsTab() {
    return Column(
      children: [
        _buildTabHeader(Icons.calendar_today, 'Scheduled Meetings'),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
              maxCrossAxisExtent: 340, mainAxisSpacing: 16, crossAxisSpacing: 16, childAspectRatio: 1.8),
          itemCount: _meetings.length,
          itemBuilder: (context, i) {
            final m = _meetings[i];
            return Card(
              color: AppColors.surface,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(color: AppColors.success.withOpacity(0.15), borderRadius: BorderRadius.circular(999)),
                          child: Text('${m.date} · ${m.time}', style: const TextStyle(color: AppColors.success, fontSize: 10, fontWeight: FontWeight.bold)),
                        ),
                        IconButton(
                          icon: const Icon(Icons.x, size: 14, color: AppColors.danger),
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                          onPressed: () async {
                            if (await _confirm('Delete this meeting?')) {
                              await ApiService.deleteMeeting(m.id);
                              _fetchData();
                            }
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(m.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                    if (m.description != null)
                      Text(m.description!,
                          style: const TextStyle(color: AppColors.muted, fontSize: 12),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis),
                    const Spacer(),
                    Row(
                      children: [
                        const Icon(Icons.person, size: 12, color: AppColors.primaryLight),
                        const SizedBox(width: 4),
                        Text(m.employeeId ?? 'All Employees',
                            style: const TextStyle(color: AppColors.primaryLight, fontSize: 11)),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        ),
      ],
    );
  }

  Widget _buildLeavesTab() {
    return Column(
      children: [
        _buildTabHeader(Icons.description, 'Leave Requests (${_leaveReqs.length})'),
        Card(
          child: Table(
            columnWidths: const {
              0: FlexColumnWidth(2),
              1: FlexColumnWidth(1.5),
              2: FlexColumnWidth(1.5),
              3: FlexColumnWidth(1.2),
              4: FlexColumnWidth(1.2),
              5: FlexColumnWidth(1.5),
              6: FlexColumnWidth(1.2),
              7: FlexColumnWidth(2),
            },
            children: [
              TableRow(
                decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                children: ['Employee', 'Dept', 'Type', 'From', 'To', 'Reason', 'Status', 'Actions']
                    .map((h) => Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(h.toUpperCase(),
                            style: const TextStyle(
                                color: AppColors.muted, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 0.5))))
                    .toList(),
              ),
              ..._leaveReqs.map((l) => TableRow(
                    decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(l.employeeName ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                            Text(l.employeeId, style: const TextStyle(color: AppColors.muted, fontSize: 10)),
                          ],
                        ),
                      ),
                      _td(l.department ?? '—'),
                      _td(l.leaveType),
                      _td(l.fromDate),
                      _td(l.toDate),
                      _td(l.reason ?? '—', isMuted: true),
                      Padding(padding: const EdgeInsets.all(12), child: _buildPill(l.status.toLowerCase())),
                      Padding(
                        padding: const EdgeInsets.all(12),
                        child: l.status == 'Pending'
                            ? Row(
                                children: [
                                  IconButton(
                                      icon: const Icon(Icons.check, color: AppColors.success, size: 16),
                                      onPressed: () async {
                                        await ApiService.approveLeave(l.id);
                                        _fetchData();
                                      }),
                                  IconButton(
                                      icon: const Icon(Icons.x, color: AppColors.danger, size: 16),
                                      onPressed: () async {
                                        await ApiService.rejectLeave(l.id);
                                        _fetchData();
                                      }),
                                ],
                              )
                            : const Text('—', style: TextStyle(color: AppColors.muted)),
                      ),
                    ],
                  )),
            ],
          ),
        ),
      ],
    );
  }

  Widget _td(String text, {bool isMuted = false}) => Padding(
      padding: const EdgeInsets.all(12),
      child: Text(text,
          style: TextStyle(fontSize: 12, color: isMuted ? AppColors.muted : null, fontWeight: isMuted ? null : FontWeight.w500)));

  Widget _buildPill(String status) {
    Color c = status == 'approved' ? AppColors.success : (status == 'rejected' ? AppColors.danger : AppColors.warning);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(999)),
      child: Text(status.toUpperCase(),
          textAlign: TextAlign.center, style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Future<bool> _confirm(String msg) async {
    return await showDialog(
            context: context,
            builder: (context) => AlertDialog(
                  backgroundColor: Theme.of(context).cardTheme.color,
                  title: const Text('Confirm Action'),
                  content: Text(msg),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                    ElevatedButton(onPressed: () => Navigator.pop(context, true), child: const Text('Confirm')),
                  ],
                )) ??
        false;
  }

  void _showMeetingModal() {
    final titleC = TextEditingController();
    final dateC = TextEditingController();
    final timeC = TextEditingController();
    final descC = TextEditingController();
    String? assignedId;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Schedule Meeting'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
             _buildField('Title *', titleC),
             _buildField('Date *', dateC, isDate: true),
             _buildField('Time *', timeC, isTime: true),
             _buildField('Description', descC),
             const SizedBox(height: 10),
             DropdownButtonFormField<String>(
               decoration: const InputDecoration(labelText: 'Assign To'),
               items: [const DropdownMenuItem(value: '', child: Text('All Employees')), ..._employees.map((e) => DropdownMenuItem(value: e.employeeId, child: Text(e.name)))],
               onChanged: (v) => assignedId = v,
             ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(onPressed: () async {
            await ApiService.createMeeting({'title': titleC.text, 'date': dateC.text, 'time': timeC.text, 'description': descC.text, 'employee_id': assignedId});
            Navigator.pop(context);
            _fetchData();
          }, child: const Text('Save Meeting')),
        ],
      ),
    );
  }

  Widget _buildField(String label, TextEditingController c, {bool isDate = false, bool isTime = false}) {
     return Padding(
       padding: const EdgeInsets.only(bottom: 12),
       child: TextField(
         controller: c,
         readOnly: isDate || isTime,
         onTap: isDate ? () async {
           final d = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime.now(), lastDate: DateTime(2026));
           if (d!=null) c.text = DateFormat('yyyy-MM-dd').format(d);
         } : (isTime ? () async {
           final t = await showTimePicker(context: context, initialTime: TimeOfDay.now());
           if (t!=null) c.text = t.format(context);
         } : null),
         decoration: InputDecoration(labelText: label),
       ),
     );
  }
}
