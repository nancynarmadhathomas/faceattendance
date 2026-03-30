import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:flutter_lucide/flutter_Icons.dart';
import 'package:provider/provider.dart';
import '../providers/theme_provider.dart';
import '../theme.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> with SingleTickerProviderStateMixin {
  CameraController? _controller;
  bool _isInit = false;
  bool _isVerifying = false;
  String? _message;
  String? _messageType;
  bool _showRegisterPrompt = false;
  late AnimationController _scanController;

  @override
  void initState() {
    super.initState();
    _initCamera();
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
      _showToast('Camera access denied. Enable permissions.', 'danger');
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

  Future<void> _captureAndVerify() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isVerifying = true;
      _showRegisterPrompt = false;
      _showToast('Analyzing face...', 'info');
    });

    try {
      final XFile image = await _controller!.takePicture();
      final bytes = await image.readAsBytes();
      final b64 = base64Encode(bytes);

      final res = await ApiService.verifyFace(b64);

      if (res['success'] == true) {
        _showToast('✅ Welcome, ${res['name']}! Redirecting...', 'success');
        Future.delayed(const Duration(seconds: 1), () {
          if (mounted) Navigator.pushReplacementNamed(context, '/dashboard');
        });
      } else {
        _showToast('❌ ${res['message'] ?? 'Face not recognized.'}', 'danger');
        if (res['message']?.toString().toLowerCase().contains('not registered') ?? false) {
          setState(() => _showRegisterPrompt = true);
        }
        setState(() => _isVerifying = false);
      }
    } catch (e) {
      _showToast('Server error. Please try again.', 'danger');
      setState(() => _isVerifying = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bool isMobile = MediaQuery.of(context).size.width < 900;
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      body: Row(
        children: [
          if (!isMobile)
            Expanded(
              flex: 1,
              child: Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: themeProvider.isDark 
                      ? [const Color(0xFF0B0F1A), const Color(0xFF1A1550)] 
                      : [const Color(0xFF6366F1), const Color(0xFF4F46E5)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('👁️', style: TextStyle(fontSize: 60)),
                      const SizedBox(height: 16),
                      const Text(
                        'Face Attendance',
                        style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Secure, fast biometric attendance tracking. Look at the camera and you\'re in.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: AppColors.muted, height: 1.6),
                      ).paddingHorizontal(40),
                      const SizedBox(height: 24),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildStatItem('<1s', 'Login Time', AppColors.primaryLight),
                          const SizedBox(width: 32),
                          _buildStatItem('99%', 'Accuracy', AppColors.success),
                          const SizedBox(width: 32),
                          _buildStatItem('No Touch', 'Required', AppColors.warning),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          Expanded(
            flex: isMobile ? 1 : 0,
            child: Container(
              width: isMobile ? null : 480,
              color: Theme.of(context).cardTheme.color,
              padding: const EdgeInsets.symmetric(horizontal: 40),
              child: Center(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Good day! 👋',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Look at the camera to sign in.',
                        style: TextStyle(color: AppColors.muted, fontSize: 14),
                      ),
                      const SizedBox(height: 28),
                      // Camera UI
                      Center(
                        child: Column(
                          children: [
                            Container(
                              width: 280,
                              height: 280,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(color: AppColors.primary, width: 3),
                                boxShadow: [
                                  BoxShadow(
                                    color: AppColors.primaryGlow,
                                    blurRadius: 20,
                                    spreadRadius: 5,
                                  ),
                                ],
                              ),
                              clipBehavior: Clip.antiAlias,
                              child: Stack(
                                children: [
                                  if (_isInit)
                                    SizedBox.expand(child: CameraPreview(_controller!))
                                  else
                                    const Center(child: CircularProgressIndicator()),
                                  // Scan line
                                  AnimatedBuilder(
                                    animation: _scanController,
                                    builder: (context, child) {
                                      return Positioned(
                                        top: 280 * _scanController.value,
                                        left: 0,
                                        right: 0,
                                        child: Container(
                                          height: 3,
                                          decoration: BoxDecoration(
                                            gradient: LinearGradient(
                                              colors: [
                                                Colors.transparent,
                                                AppColors.primaryLight,
                                                Colors.transparent
                                              ],
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
                              '"Align your face inside the circle"',
                              style: TextStyle(color: AppColors.muted, fontStyle: FontStyle.italic, fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                      if (_message != null) _buildToast(),
                      if (_showRegisterPrompt) _buildRegisterPrompt(),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _isVerifying ? null : _captureAndVerify,
                          child: Text(_isVerifying ? '🔄 Verifying...' : '📷 Verify Face'),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Center(
                        child: Column(
                          children: [
                            GestureDetector(
                              onTap: () => Navigator.pushNamed(context, '/register'),
                              child: RichText(
                                text: const TextSpan(
                                  text: 'New employee? ',
                                  style: TextStyle(color: AppColors.muted, fontSize: 14),
                                  children: [
                                    TextSpan(
                                      text: 'Register here',
                                      style: TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            GestureDetector(
                              onTap: _showAdminLoginModal,
                              child: const Text(
                                'Admin? Admin Login',
                                style: TextStyle(color: AppColors.primaryLight, fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ).paddingTop(isMobile ? 40 : 0),
          ),
        ],
      ),
    );
  }

  Widget _buildStatItem(String val, String label, Color color) {
    return Column(
      children: [
        Text(val, style: TextStyle(color: color, fontSize: 24, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
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
      child: Text(_message!, style: TextStyle(color: color, fontWeight: FontWeight.w500, fontSize: 14)),
    );
  }

  Widget _buildRegisterPrompt() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.only(top: 16),
      decoration: BoxDecoration(
        color: AppColors.danger.withOpacity(0.08),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.danger.withOpacity(0.25)),
      ),
      child: Column(
        children: [
          const Text('😕 Your face is not registered yet.', style: TextStyle(color: Color(0xFFF87171), fontSize: 14)),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: () => Navigator.pushNamed(context, '/register'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              textStyle: const TextStyle(fontSize: 12),
            ),
            child: const Text('📝 Register Now'),
          ),
        ],
      ),
    );
  }

  void _showAdminLoginModal() {
    final personController = TextEditingController(text: 'admin');
    final passController = TextEditingController(text: 'admin123');
    String? error;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setModalState) => AlertDialog(
          backgroundColor: Theme.of(context).cardTheme.color,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
          content: Container(
            width: 440,
            constraints: const BoxConstraints(maxWidth: 440),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('🔐 Admin Login', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 20),
                const Text('personNAME', style: TextStyle(fontSize: 12, color: AppColors.muted, letterSpacing: 0.5)),
                const SizedBox(height: 6),
                TextField(controller: personController, decoration: const InputDecoration(hintText: 'admin')),
                const SizedBox(height: 16),
                const Text('PASSWORD', style: TextStyle(fontSize: 12, color: AppColors.muted, letterSpacing: 0.5)),
                const SizedBox(height: 6),
                TextField(controller: passController, obscureText: true, decoration: const InputDecoration(hintText: '••••••••')),
                if (error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
                  ),
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () async {
                          final res = await ApiService.login(personController.text, passController.text);
                          if (res['success'] == true) {
                            Navigator.pushReplacementNamed(context, '/admin');
                          } else {
                            setModalState(() => error = res['message'] ?? 'Invalid credentials');
                          }
                        },
                        child: const Text('Login'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        style: TextButton.styleFrom(
                          backgroundColor: AppColors.surface2,
                          foregroundColor: AppColors.text,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: const Text('Cancel'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

extension PaddingExtension on Widget {
  Widget paddingHorizontal(double val) => Padding(padding: EdgeInsets.symmetric(horizontal: val), child: this);
  Widget paddingVertical(double val) => Padding(padding: EdgeInsets.symmetric(vertical: val), child: this);
  Widget paddingTop(double val) => Padding(padding: EdgeInsets.only(top: val), child: this);
}
