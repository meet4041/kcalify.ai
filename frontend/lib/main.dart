import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart'; // flutter pub add image_picker
import 'package:http/http.dart' as http;         // flutter pub add http
import 'package:http_parser/http_parser.dart';   // flutter pub add http_parser

void main() {
  runApp(const KcalifyApp());
}

class KcalifyApp extends StatelessWidget {
  const KcalifyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Kcalify.ai',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        scaffoldBackgroundColor: Colors.grey[50],
      ),
      home: const ScannerScreen(),
    );
  }
}

class ScannerScreen extends StatefulWidget {
  const ScannerScreen({super.key});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  Uint8List? _webImage; // Stores image data for Web/Mobile
  bool _isLoading = false;
  String _errorMessage = "";
  Map<String, dynamic>? _nutritionData; // Stores the JSON from Python

  // 1. Pick Image
  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      final bytes = await image.readAsBytes();
      setState(() {
        _webImage = bytes;
        _nutritionData = null; // Reset previous results
        _errorMessage = "";
      });
    }
  }

  // 2. Send to Backend
  Future<void> _analyzeFood() async {
    if (_webImage == null) return;

    setState(() {
      _isLoading = true;
      _errorMessage = "";
    });

    try {
      // ⚠️ IMPORTANT: 
      // Use '[http://127.0.0.1:8000](http://127.0.0.1:8000)' for Chrome/iOS Simulator
      // Use '[http://10.0.2.2:8000](http://10.0.2.2:8000)' for Android Emulator
      var uri = Uri.parse('http://127.0.0.1:8000/predict/calories?user_id=test_user_123');
      
      var request = http.MultipartRequest('POST', uri);
      
      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          _webImage!,
          filename: 'food_upload.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
      );

      var response = await request.send();

      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        setState(() {
          _nutritionData = jsonDecode(respStr);
        });
      } else {
        setState(() {
          _errorMessage = "Server Error: ${response.statusCode}";
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = "Connection Failed. Is backend running?\nError: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Kcalify AI Scanner", style: TextStyle(fontWeight: FontWeight.bold)),
        centerTitle: true,
        backgroundColor: Colors.white,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Image Preview Area
            Container(
              height: 300,
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                boxShadow: [
                  BoxShadow(color: Colors.black.withOpacity(0.1), blurRadius: 10, spreadRadius: 2)
                ],
              ),
              child: _webImage != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(20),
                      child: Image.memory(_webImage!, fit: BoxFit.cover),
                    )
                  : Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.add_a_photo_rounded, size: 60, color: Colors.grey[300]),
                        const SizedBox(height: 10),
                        Text("Upload a food photo", style: TextStyle(color: Colors.grey[500])),
                      ],
                    ),
            ),
            
            const SizedBox(height: 25),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _pickImage,
                    icon: const Icon(Icons.image),
                    label: const Text("Select Image"),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.black,
                      elevation: 0,
                      side: const BorderSide(color: Colors.grey),
                    ),
                  ),
                ),
                const SizedBox(width: 15),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: (_webImage == null || _isLoading) ? null : _analyzeFood,
                    icon: _isLoading 
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : const Icon(Icons.bolt),
                    label: Text(_isLoading ? "Analyzing..." : "Analyze"),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      backgroundColor: Colors.green[700],
                      foregroundColor: Colors.white,
                      elevation: 2,
                    ),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 30),

            // Error Message
            if (_errorMessage.isNotEmpty)
              Container(
                padding: const EdgeInsets.all(15),
                decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(10)),
                child: Text(_errorMessage, style: const TextStyle(color: Colors.red)),
              ),

            // Nutrition Result Card
            if (_nutritionData != null)
              _buildNutritionCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildNutritionCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.green.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(color: Colors.green.withOpacity(0.1), blurRadius: 20, offset: const Offset(0, 10))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Text(
            _nutritionData!['food_name'],
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.black87),
          ),
          const SizedBox(height: 5),
          Text(
            "${_nutritionData!['calories']} kcal",
            style: TextStyle(fontSize: 40, fontWeight: FontWeight.w900, color: Colors.green[700]),
          ),
          const SizedBox(height: 20),
          const Divider(),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _macroInfo("Protein", _nutritionData!['protein'], Colors.blue[600]!),
              _macroInfo("Carbs", _nutritionData!['carbs'], Colors.orange[600]!),
              _macroInfo("Fats", _nutritionData!['fat'], Colors.red[600]!),
            ],
          ),
        ],
      ),
    );
  }

  Widget _macroInfo(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: TextStyle(color: Colors.grey[600], fontSize: 14, fontWeight: FontWeight.w500)),
        const SizedBox(height: 5),
        Text(
          value,
          style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}