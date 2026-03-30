import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:flutter_lucide/flutter_Icons.dart';
import '../theme.dart';
import '../services/api_service.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';
import '../models/employee.dart';
import '../models/attendance.dart';
import '../models/meeting.dart';
import '../models/leave.dart';

class EmployeeDashboard extends StatefulWidget {
  const EmployeeDashboard({super.key});

  @override
  State<EmployeeDashboard> createState() => _EmployeeDashboardState();
}

class _EmployeeDashboardState extends State<EmployeeDashboard> {
  String _activeSection = 'overview';
  bool _isLoading = true;
  
  Employee? _emp;
  AttendanceRecord? _today;
  List<AttendanceRecord> _history = [];
  List<Meeting> _meetings = [];
  List<LeaveRequest> _leaveReqs = [];
  Map<String, dynamic> _monthly = {};
  Map<String, dynamic> _leaveBal = {};
  List<Meeting> _upcoming = [];
  List<Map<String, dynamic>> _notifications = [];

  @override
  void initState() {
    super.initState();
    _fetchData();
  }

  Future<void> _fetchData() async {
    final res = await ApiService.getDashboardData();
    if (res['success'] == true) {
      setState(() {
        _emp = Employee.fromJson(res['employee']);
        if (res['today'] != null) _today = AttendanceRecord.fromJson(res['today']);
        _history = (res['history'] as List).map((e) => AttendanceRecord.fromJson(e)).toList();
        _meetings = (res['meetings'] as List).map((e) => Meeting.fromJson(e)).toList();
        _leaveReqs = (res['leave_reqs'] as List).map((e) => LeaveRequest.fromJson(e)).toList();
        _monthly = res['monthly'] ?? {};
        _leaveBal = res['leave_bal'] ?? {};
        _upcoming = (res['upcoming'] as List).map((e) => Meeting.fromJson(e)).toList();
        _notifications = List<Map<String, dynamic>>.from(res['notifications'] ?? []);
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
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: Row(
        children: [
          _buildSidebar(),
          Expanded(
            child: Column(
              children: [
                _buildTopbar(),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(32),
                    child: _buildActiveSection(),
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
    final themeProvider = Provider.of<ThemeProvider>(context);
    return Container(
      width: 240,
      color: themeProvider.isDark ? AppColors.sidebarBg : AppColors.lightSurface,
      decoration: BoxDecoration(
        border: Border(right: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder)),
      ),
      child: Column(
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 12, right: 12),
            child: Align(
              alignment: Alignment.topRight,
              child: IconButton(
                icon: Icon(themeProvider.isDark ? Icons.wb_sunny : Icons.brightness_3, size: 20),
                onPressed: () => themeProvider.toggleTheme(),
                color: themeProvider.isDark ? AppColors.primaryLight : AppColors.primary,
                tooltip: 'Toggle Theme',
              ),
            ),
          ),
          _buildSidebarProfile(),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                children: [
                  _buildNavItem('overview', Icons.dashboard, 'Overview'),
                  _buildNavItem('attendance', Icons.assignment, 'Attendance'),
                  _buildNavItem('meetings', Icons.calendar_today, 'Meetings', badge: _upcoming.length),
                  _buildNavItem('leaves', Icons.beach_access, 'Leave Request'),
                  _buildNavItem('profile', Icons.person, 'My Profile'),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: _buildNavItem('logout', Icons.logout, 'logout', color: AppColors.danger),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebarProfile() {
    final themeProvider = Provider.of<ThemeProvider>(context);
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 20),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder)),
      ),
      child: Column(
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.primary, width: 3),
              image: (_emp?.faceImage != null)
                ? DecorationImage(image: MemoryImage(base64Decode(_emp!.faceImage!)), fit: BoxFit.cover)
                : null,
            ),
            child: (_emp?.faceImage == null)
              ? Center(child: Text(_emp?.name[0].toUpperCase() ?? '', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: AppColors.primaryLight)))
              : null,
          ),
          const SizedBox(height: 12),
          Text(_emp?.name ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
          Text(_emp?.department ?? 'Employee', style: const TextStyle(color: AppColors.muted, fontSize: 12)),
          const SizedBox(height: 4),
          Text(_emp?.employeeId ?? '', style: const TextStyle(color: AppColors.primaryLight, fontFamily: 'monospace', fontSize: 11)),
          const SizedBox(height: 10),
          _buildStatusBadge(),
        ],
      ),
    );
  }

  Widget _buildStatusBadge() {
    String state = _today?.status ?? 'absent';
    Color color = state == 'present' ? AppColors.success : (state == 'late' ? AppColors.warning : AppColors.danger);
    String label = state == 'present' ? 'Present' : (state == 'late' ? 'Late' : 'Not checked in');

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 8, height: 8, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
          const SizedBox(width: 5),
          Text(label, style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildNavItem(String id, IconData icon, String label, {int? badge, Color? color}) {
    bool active = _activeSection == id;
    
    return GestureDetector(
      onTap: () {
        if (id == 'logout') {
          ApiService.checkOut(); // Logic from original
          Navigator.pushReplacementNamed(context, '/');
        } else {
          setState(() => _activeSection = id);
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: active ? AppColors.primary.withOpacity(0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: active ? AppColors.primaryLight : (color ?? AppColors.muted)),
            const SizedBox(width: 12),
            Text(label, style: TextStyle(fontSize: 14, fontWeight: active ? FontWeight.w600 : FontWeight.w500, color: active ? AppColors.primaryLight : (color ?? AppColors.muted))),
            if (badge != null && badge > 0) ...[
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(999)),
                child: Text('$badge', style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTopbar() {
    final themeProvider = Provider.of<ThemeProvider>(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 16),
      decoration: BoxDecoration(
        color: themeProvider.isDark ? AppColors.sidebarBg : AppColors.lightSurface,
        border: Border(bottom: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Good day, ${_emp?.name.split(' ')[0] ?? ''}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              Text(_emp?.department ?? 'Employee', style: TextStyle(color: themeProvider.isDark ? AppColors.muted : AppColors.lightMuted, fontSize: 12)),
            ],
          ),
          Column(
            children: [
              StreamBuilder(
                stream: Stream.periodic(const Duration(seconds: 1)),
                builder: (context, snapshot) {
                  final now = DateTime.now();
                  return Column(
                    children: [
                      Text(DateFormat('EEE, MMM d, yyyy').format(now), style: TextStyle(color: themeProvider.isDark ? AppColors.muted : AppColors.lightMuted, fontSize: 12)),
                      Text(DateFormat('hh:mm:ss a').format(now), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, fontFamily: 'monospace')),
                    ],
                  );
                },
              ),
            ],
          ),
          Row(
            children: [
              if (_today == null)
                _buildClockBtn('Clock In', AppColors.success, _doCheckin)
              else if (_today!.checkOut == null)
                _buildClockBtn('Clock Out', AppColors.danger, _doCheckout)
              else
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(color: (themeProvider.isDark ? AppColors.muted : AppColors.lightMuted).withOpacity(0.1), borderRadius: BorderRadius.circular(999)),
                  child: Text('Clocked out · ${_today!.checkOut}', style: TextStyle(color: themeProvider.isDark ? AppColors.muted : AppColors.lightMuted, fontSize: 12)),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildClockBtn(String label, Color color, VoidCallback onTap) {
    return ElevatedButton.icon(
      onPressed: onTap,
      icon: Icon(label == 'Clock In' ? Icons.schedule : Icons.logout, size: 14),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        backgroundColor: color.withOpacity(0.12),
        foregroundColor: color,
        side: BorderSide(color: color.withOpacity(0.25)),
      ),
    );
  }

  Future<void> _doCheckin() async {
    final res = await ApiService.checkIn();
    if (res['success'] == true) {
      if (res['late'] == true) {
        _showLateModal();
      } else {
        _fetchData();
      }
    }
  }

  Future<void> _doCheckout() async {
    final res = await ApiService.checkOut();
    if (res['success'] == true) _fetchData();
  }

  void _showLateModal() {
    String? reason;
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.surface,
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.schedule, size: 48, color: AppColors.warning),
            const SizedBox(height: 16),
            const Text('You\'re Running Late', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const Text('Office hours start at 9:30 AM. Please select a reason.', textAlign: TextAlign.center, style: TextStyle(color: AppColors.muted, fontSize: 14)),
            const SizedBox(height: 20),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(labelText: 'Reason for Late Arrival'),
              items: ['Traffic', 'Health Issue', 'Personal Work', 'Transport Delay', 'Emergency', 'Other']
                  .map((e) => DropdownMenuItem(value: e, child: Text(e))).toList(),
              onChanged: (v) => reason = v,
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () async {
                  if (reason != null) {
                    await ApiService.submitLateReason(reason!);
                    Navigator.pop(context);
                    _fetchData();
                  }
                },
                child: const Text('Confirm & Clock In'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActiveSection() {
    switch (_activeSection) {
      case 'overview': return _buildOverview();
      case 'attendance': return _buildAttendanceTable(_history, 'Full Attendance History');
      case 'meetings': return _buildMeetingsGrid();
      case 'leaves': return _buildLeavesSection();
      case 'profile': return _buildProfileSection();
      default: return Container();
    }
  }

  Widget _buildOverview() {
    return Column(
      children: [
        _buildSummaryBar(),
        const SizedBox(height: 20),
        _buildStatsRow(),
        const SizedBox(height: 20),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(flex: 2, child: _buildAttendanceTable(_history.take(7).toList(), 'Recent Attendance')),
            const SizedBox(width: 20),
            Expanded(flex: 1, child: _buildUpcomingMeetingsCard()),
          ],
        ),
      ],
    );
  }

  Widget _buildSummaryBar() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _buildSummaryItem('Today Status', _today?.status.toUpperCase() ?? 'ABSENT', AppColors.accent),
            _buildSummaryItem('Check-In Time', _today?.checkIn ?? '--:--', Colors.white),
            _buildSummaryItem('Working Hours', '${_today?.workingHours ?? 0}h', Colors.white),
            _buildSummaryItem('Shift Timing', '9:30 AM – 6:30 PM', Colors.white, isMono: true),
          ],
        ),
      ),
    ).paddingBottom(20);
  }

  Widget _buildSummaryItem(String label, String val, Color color, {bool isMono = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 11, letterSpacing: 1)),
        const SizedBox(height: 4),
        Text(val, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 15, fontFamily: isMono ? 'monospace' : null)),
      ],
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        _buildStatTile('Present (Month)', _monthly['present']?.toString() ?? '0', Icons.person_round_check, AppColors.success),
        const SizedBox(width: 16),
        _buildStatTile('Late (Month)', _monthly['late']?.toString() ?? '0', Icons.alert_triangle, AppColors.warning),
        const SizedBox(width: 16),
        _buildStatTile('Leaves Taken', _leaveReqs.where((l) => l.status == 'Approved').length.toString(), Icons.beach_access, AppColors.primaryLight),
        const SizedBox(width: 16),
        _buildStatTile('Attendance %', '${_monthly['pct'] ?? 0}%', Icons.bar_chart_2, const Color(0xFF8B5CF6)),
      ],
    );
  }

  Widget _buildStatTile(String label, String val, IconData icon, Color color) {
    final themeProvider = Provider.of<ThemeProvider>(context);
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: themeProvider.isDark ? AppColors.cardBg : AppColors.lightSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border(left: BorderSide(color: color, width: 3), right: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder), top: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder), bottom: BorderSide(color: themeProvider.isDark ? AppColors.border : AppColors.lightBorder)),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(width: 16),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: themeProvider.isDark ? AppColors.muted : AppColors.lightMuted, fontSize: 11, letterSpacing: 0.5)),
                Text(val, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAttendanceTable(List<AttendanceRecord> data, String title) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(22),
              child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            ),
            const Divider(height: 1),
            Table(
              columnWidths: const {
                0: FlexColumnWidth(2),
                1: FlexColumnWidth(2),
                2: FlexColumnWidth(2),
                3: FlexColumnWidth(1.5),
                4: FlexColumnWidth(2),
              },
              children: [
                TableRow(
                  decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                  children: ['Date', 'Check In', 'Check Out', 'Hours', 'Status'].map((h) => Padding(padding: const EdgeInsets.all(14), child: Text(h.toUpperCase(), style: const TextStyle(color: AppColors.muted, fontSize: 11, fontWeight: FontWeight.bold)))).toList(),
                ),
                ...data.map((r) => TableRow(
                  decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: AppColors.border))),
                  children: [
                    _tablePadding(Text(r.date, style: const TextStyle(fontSize: 13))),
                    _tablePadding(Text(r.checkIn ?? '--:--', style: const TextStyle(color: AppColors.success, fontFamily: 'monospace', fontSize: 13))),
                    _tablePadding(Text(r.checkOut ?? '--:--', style: const TextStyle(color: AppColors.muted, fontFamily: 'monospace', fontSize: 13))),
                    _tablePadding(Text('${r.workingHours ?? '--'}h', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13))),
                    _tablePadding(_buildPill(r.status)),
                  ],
                )),
              ],
            ),
            if (data.isEmpty) const Padding(padding: EdgeInsets.all(32), child: Center(child: Text('No records yet', style: TextStyle(color: AppColors.muted)))),
          ],
        ),
      ),
    );
  }

  Widget _tablePadding(Widget child) => Padding(padding: const EdgeInsets.all(14), child: child);

  Widget _buildPill(String status) {
    Color c = status == 'present' ? AppColors.success : (status == 'late' ? AppColors.warning : AppColors.danger);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(color: c.withOpacity(0.15), borderRadius: BorderRadius.circular(999)),
      child: Text(status.toUpperCase(), textAlign: TextAlign.center, style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildUpcomingMeetingsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Upcoming Meetings', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 20),
            if (_upcoming.isEmpty)
              const Center(child: Padding(padding: EdgeInsets.all(20), child: Text('No upcoming meetings', style: TextStyle(color: AppColors.muted))))
            else
              ..._upcoming.map((m) => _buildMeetingItem(m)),
          ],
        ),
      ),
    );
  }

  Widget _buildMeetingItem(Meeting m) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(width: 8, height: 8, margin: const EdgeInsets.only(top: 6), decoration: const BoxDecoration(color: AppColors.primary, shape: BoxShape.circle, boxShadow: [BoxShadow(color: AppColors.primary, blurRadius: 4)])),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${m.date} · ${m.time}', style: const TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.bold, fontSize: 12)),
                const SizedBox(height: 2),
                Text(m.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                if (m.description != null) Text(m.description!, style: const TextStyle(color: AppColors.muted, fontSize: 12), maxLines: 2, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMeetingsGrid() {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(maxCrossAxisExtent: 340, mainAxisSpacing: 14, crossAxisSpacing: 14, childAspectRatio: 1.8),
      itemCount: _meetings.length,
      itemBuilder: (context, i) {
        final m = _meetings[i];
        return Card(
          color: AppColors.cardBg,
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(m.date, style: const TextStyle(color: AppColors.muted, fontSize: 11)),
                Text(m.time, style: const TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 8),
                Text(m.title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const Spacer(),
                const Divider(height: 20),
                Row(
                  children: [
                    const Icon(Icons.person, size: 12, color: AppColors.primaryLight),
                    const SizedBox(width: 4),
                    Text(m.employeeId != null ? 'Assigned to you' : 'All employees', style: const TextStyle(color: AppColors.primaryLight, fontSize: 11)),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildLeavesSection() {
    final leaveTypeController = TextEditingController();
    final fromController = TextEditingController();
    final toController = TextEditingController();
    final reasonController = TextEditingController();

    return Column(
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Submit Leave Request', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Expanded(child: _buildInput('Leave Type', leaveTypeController, isSelect: true, options: ['Casual Leave', 'Sick Leave', 'Half Day', 'Permission', 'WFH'])),
                    const SizedBox(width: 16),
                    Expanded(child: _buildInput('Reason', reasonController)),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(child: _buildInput('From Date', fromController, isDate: true)),
                    const SizedBox(width: 16),
                    Expanded(child: _buildInput('To Date', toController, isDate: true)),
                  ],
                ),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () async {
                    await ApiService.submitLeave({
                      'leave_type': leaveTypeController.text,
                      'from_date': fromController.text,
                      'to_date': toController.text,
                      'reason': reasonController.text,
                    });
                    _fetchData();
                  },
                  child: const Text('Submit Request'),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        _buildAttendanceTable(_history, 'My Leave Requests'), // Reuse table for now
      ],
    );
  }

  Widget _buildInput(String label, TextEditingController controller, {bool isSelect = false, List<String>? options, bool isDate = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label.toUpperCase(), style: const TextStyle(color: AppColors.muted, fontSize: 11, fontWeight: FontWeight.bold)),
        const SizedBox(height: 6),
        isSelect 
          ? DropdownButtonFormField<String>(
              decoration: const InputDecoration(contentPadding: EdgeInsets.symmetric(horizontal: 14)),
              items: options?.map((e) => DropdownMenuItem(value: e, child: Text(e, style: const TextStyle(fontSize: 14)))).toList(),
              onChanged: (v) => controller.text = v ?? '',
            )
          : TextField(
              controller: controller,
              readOnly: isDate,
              onTap: isDate ? () async {
                final d = await showDatePicker(context: context, initialDate: DateTime.now(), firstDate: DateTime.now(), lastDate: DateTime(2027));
                if (d != null) controller.text = DateFormat('yyyy-MM-dd').format(d);
              } : null,
              decoration: InputDecoration(hintText: label),
            ),
      ],
    );
  }

  Widget _buildProfileSection() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 1,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                children: [
                   Container(
                    width: 120, height: 120,
                    decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: AppColors.primary, width: 3),
                      image: (_emp?.faceImage != null) ? DecorationImage(image: MemoryImage(base64Decode(_emp!.faceImage!)), fit: BoxFit.cover) : null,
                    ),
                    child: (_emp?.faceImage == null) ? Center(child: Text(_emp?.name[0].toUpperCase() ?? '', style: const TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: AppColors.primaryLight))) : null,
                  ),
                  const SizedBox(height: 16),
                  Text(_emp?.name ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 20)),
                  Text(_emp?.department ?? 'N/A', style: const TextStyle(color: AppColors.muted)),
                  const SizedBox(height: 12),
                  _buildPill(_today?.status ?? 'absent'),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 20),
        Expanded(
          flex: 2,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Profile Information', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  const SizedBox(height: 20),
                  _profileRow('Employee ID', _emp?.employeeId ?? ''),
                  _profileRow('Full Name', _emp?.name ?? ''),
                  _profileRow('Email', _emp?.email ?? '—'),
                  _profileRow('Department', _emp?.department ?? '—'),
                  _profileRow('Role', (_emp?.role ?? 'employee').toUpperCase()),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _profileRow(String label, String val) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 14)),
          Text(val, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        ],
      ),
    );
  }
}

extension PaddingBottom on Widget {
  Widget paddingBottom(double val) => Padding(padding: EdgeInsets.only(bottom: val), child: this);
}
