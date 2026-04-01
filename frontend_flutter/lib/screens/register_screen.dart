import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter_lucide/flutter_lucide.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';
import '../theme.dart';
import '../services/api_service.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> with SingleTickerProviderStateMixin {
  int _step = 1;
  String _role = 'employee';
  
  final _idController = TextEditingController();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _deptController = TextEditingController();
  final _passController = TextEditingController();

  CameraController? _controller;
  bool _isInit = false;
  bool _isRegistering = false;
  String? _message;
  String? _messageType;
  late AnimationController _scanController;

  @override
  void initState() {
    super.initState();
    _scanController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat();
  }

  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;
    
    _controller = CameraController(
      cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.front,
        orElse: () => cameras.first,
      ),
      ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await _controller!.initialize();
      setState(() => _isInit = true);
    } catch (e) {
      _showToast('Camera access denied.', 'danger');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    _scanController.dispose();
    super.dispose();
  }

  void _showToast(String msg, String type) {
    setState(() {
      _message = msg;
      _messageType = type;
    });
  }

  void _goStep2() {
    if (_idController.text.trim().isEmpty || 
        _nameController.text.trim().isEmpty || 
        _passController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required fields (ID, Name, Password)')),
      );
      return;
    }
    setState(() => _step = 2);
    _initCamera();
  }

  void _goStep1() {
    _controller?.dispose();
    setState(() {
      _step = 1;
      _isInit = false;
    });
  }

  Future<void> _submitRegister() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isRegistering = true;
      _showToast('⏳ Registering...', 'info');
    });

    try {
      final XFile image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      final b64 = base64Encode(bytes);

      final payload = {
        'employee_id': _idController.text.trim(),
        'name': _nameController.text.trim(),
        'email': _emailController.text.trim(),
        'department': _deptController.text.trim(),
        'password': _passController.text,
        'role': _role,
        'image': b64,
      };

      final res = await ApiService.register(payload);

      if (res['success'] == true) {
        _showToast('✅ Registration Successful! Please login with your face.', 'success');
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) Navigator.pushReplacementNamed(context, '/');
        });
      } else {
        _showToast('❌ ${res['message'] ?? 'Registration failed.'}', 'danger');
        setState(() => _isRegistering = false);
      }
    } catch (e) {
      _showToast('Server error. Please try again.', 'danger');
      setState(() => _isRegistering = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: RichText(
          text: TextSpan(
            text: 'Face',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Theme.of(context).textTheme.bodyLarge?.color ?? Colors.white),
            children: const [
              TextSpan(text: 'Attend', style: TextStyle(color: AppColors.primaryLight)),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('← Back to Login', style: TextStyle(color: AppColors.muted)),
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Employee Registration', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    const Text('Complete both steps to register your account.', style: TextStyle(color: AppColors.muted, fontSize: 14)),
                    const SizedBox(height: 24),
                    _buildStepsIndicator(),
                    const SizedBox(height: 32),
                    if (_step == 1) _buildStep1() else _buildStep2(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepsIndicator() {
    return Row(
      children: [
        _buildStepIndicator(1, 'Details', _step >= 1),
        const SizedBox(width: 0),
        _buildStepIndicator(2, 'Face Capture', _step == 2),
      ],
    );
  }

  Widget _buildStepIndicator(int n, String label, bool active) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          border: Border(
            bottom: BorderSide(
              color: active ? (_step > n ? AppColors.success : AppColors.primary) : AppColors.border,
              width: 2,
            ),
          ),
        ),
        child: Text(
          '$n · $label',
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: active ? (_step > n ? AppColors.success : AppColors.primaryLight) : AppColors.muted,
          ),
        ),
      ),
    );
  }

  Widget _buildStep1() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('ROLE *', style: TextStyle(fontSize: 12, color: AppColors.muted, letterSpacing: 0.5)),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(child: _buildRoleCard('employee', '👤', 'Employee', 'Standard access')),
            const SizedBox(width: 12),
            Expanded(child: _buildRoleCard('admin', '🛡️', 'Admin', 'Full access')),
          ],
        ),
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: _buildField('EMPLOYEE ID *', _idController, hint: 'e.g. EMP-001'),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildField('FULL NAME *', _nameController, hint: 'John Doe'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildField('EMAIL', _emailController, hint: 'john@company.com', type: TextInputType.emailAddress),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildField('DEPARTMENT', _deptController, hint: 'Engineering'),
            ),
          ],
        ),
        const SizedBox(height: 16),
        _buildField('PASSWORD *', _passController, hint: 'Min 6 characters', obscure: true),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: _goStep2,
            child: const Text('Next: Capture Face →'),
          ),
        ),
      ],
    );
  }

  Widget _buildRoleCard(String role, String icon, String title, String sub) {
    bool selected = _role == role;
    Color activeColor = role == 'admin' ? const Color(0xFF8B5CF6) : AppColors.primary;
    
    return GestureDetector(
      onTap: () => setState(() => _role = role),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: selected 
            ? (role == 'admin' ? activeColor.withOpacity(0.15) : AppColors.primaryGlow) 
            : Theme.of(context).inputDecorationTheme.fillColor,
          border: Border.all(color: selected ? activeColor : Theme.of(context).dividerColor, width: 2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 22)),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  Text(sub, style: const TextStyle(color: AppColors.muted, fontSize: 11)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, {String? hint, bool obscure = false, TextInputType? type}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: AppColors.muted, letterSpacing: 0.5)),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          obscureText: obscure,
          keyboardType: type,
          style: const TextStyle(fontSize: 14),
          decoration: InputDecoration(hintText: hint),
        ),
      ],
    );
  }

  Widget _buildStep2() {
    return Column(
      children: [
        Center(
          child: Column(
            children: [
              Container(
                width: 280,
                height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(color: AppColors.primary, width: 3),
                  boxShadow: const [
                    BoxShadow(color: AppColors.primaryGlow, blurRadius: 20, spreadRadius: 5),
                  ],
                ),
                clipBehavior: Clip.antiAlias,
                child: Stack(
                  children: [
                    if (_isInit)
                      SizedBox.expand(child: CameraPreview(_controller!))
                    else
                      const Center(child: CircularProgressIndicator()),
                    AnimatedBuilder(
                      animation: _scanController,
                      builder: (context, child) {
                        return Positioned(
                          top: 280 * _scanController.value,
                          left: 0,
                          right: 0,
                          child: Container(
                            height: 3,
                            decoration: const BoxDecoration(
                              gradient: LinearGradient(
                                colors: [Colors.transparent, AppColors.primaryLight, Colors.transparent],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              const Text(
                '"Centre your face and ensure good lighting"',
                style: TextStyle(color: AppColors.muted, fontStyle: FontStyle.italic, fontSize: 13),
              ),
            ],
          ),
        ),
        if (_message != null) _buildToast(),
        const SizedBox(height: 24),
        Row(
          children: [
            ElevatedButton(
              onPressed: _isRegistering ? null : _goStep1,
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).inputDecorationTheme.fillColor,
                foregroundColor: Theme.of(context).textTheme.bodyMedium?.color,
              ),
              child: const Text('← Back'),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton(
                onPressed: _isRegistering ? null : _submitRegister,
                child: Text(_isRegistering ? '⏳ Registering...' : '📷 Capture & Register'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildToast() {
    Color color = _messageType == 'success' ? AppColors.success : (_messageType == 'danger' ? AppColors.danger : AppColors.primaryLight);
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 18),
      margin: const EdgeInsets.only(top: 16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(_message!, style: TextStyle(color: color, fontWeight: FontWeight.w500, fontSize: 13)),
    );
  }
}
