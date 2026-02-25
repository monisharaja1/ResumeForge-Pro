import "dart:convert";
import "dart:typed_data";

import "package:http/http.dart" as http;

import "../config.dart";
import "../models/resume.dart";

class ApiService {
  final http.Client _client = http.Client();

  Uri _uri(String path) => Uri.parse("${ApiConfig.baseUrl}$path");

  Future<bool> login({
    required String username,
    required String password,
  }) async {
    final res = await _client.post(
      _uri("/login"),
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: {"username": username, "password": password},
    );
    return res.statusCode == 200 || res.statusCode == 302;
  }

  Future<List<Map<String, dynamic>>> fetchResumeList() async {
    final res = await _client.get(_uri("/api/resumes"));
    if (res.statusCode != 200) {
      throw Exception("Failed to fetch resumes: ${res.body}");
    }
    final body = jsonDecode(res.body) as List<dynamic>;
    return body.map((e) => (e as Map<String, dynamic>)).toList();
  }

  Future<ResumeModel> fetchResume(int id) async {
    final res = await _client.get(_uri("/api/resumes/$id"));
    if (res.statusCode != 200) {
      throw Exception("Failed to fetch resume: ${res.body}");
    }
    return ResumeModel.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  Future<int> saveResume(ResumeModel model) async {
    final res = await _client.post(
      _uri("/api/resumes"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(model.toJson()),
    );
    if (res.statusCode != 200) {
      throw Exception("Save failed: ${res.body}");
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data["id"] as num).toInt();
  }

  Future<void> deleteResume(int id) async {
    final res = await _client.delete(_uri("/api/resumes/$id"));
    if (res.statusCode != 200) {
      throw Exception("Delete failed: ${res.body}");
    }
  }

  Future<Map<String, dynamic>> atsScore({
    required ResumeModel model,
    required String jobDescription,
  }) async {
    final payload = model.toJson()
      ..["job_description"] = jobDescription.trim();
    final res = await _client.post(
      _uri("/api/ats-score"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      throw Exception("ATS failed: ${res.body}");
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Uint8List> exportPdf({
    required ResumeModel model,
    String templateName = "modern",
    String pageSize = "letter",
  }) async {
    final payload = model.toJson()
      ..["template_name"] = templateName
      ..["page_size"] = pageSize;
    final res = await _client.post(
      _uri("/api/export-pdf"),
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/pdf",
      },
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      throw Exception("PDF export failed: ${res.body}");
    }
    return res.bodyBytes;
  }

  Future<String> exportWord({
    required ResumeModel model,
  }) async {
    final res = await _client.post(
      _uri("/api/export-word"),
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/rtf",
      },
      body: jsonEncode(model.toJson()),
    );
    if (res.statusCode != 200) {
      throw Exception("Word export failed: ${res.body}");
    }
    return utf8.decode(res.bodyBytes, allowMalformed: true);
  }

  Future<Map<String, dynamic>> createPublicLink({
    required ResumeModel model,
    int expiresDays = 7,
  }) async {
    final res = await _client.post(
      _uri("/api/public-resume"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "resume": model.toJson(),
        "expires_days": expiresDays,
      }),
    );
    if (res.statusCode != 200) {
      throw Exception("Public link failed: ${res.body}");
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> fetchPublicLinks() async {
    final res = await _client.get(_uri("/api/public-resume"));
    if (res.statusCode != 200) {
      throw Exception("Failed to fetch public links: ${res.body}");
    }
    final body = jsonDecode(res.body) as List<dynamic>;
    return body.map((e) => (e as Map<String, dynamic>)).toList();
  }

  Future<void> revokePublicLink(String token) async {
    final res = await _client.delete(_uri("/api/public-resume/$token"));
    if (res.statusCode != 200) {
      throw Exception("Revoke link failed: ${res.body}");
    }
  }

  Future<List<Map<String, dynamic>>> fetchScoreHistory() async {
    final res = await _client.get(_uri("/api/score-history"));
    if (res.statusCode != 200) {
      throw Exception("Score history failed: ${res.body}");
    }
    final body = jsonDecode(res.body) as List<dynamic>;
    return body.map((e) => (e as Map<String, dynamic>)).toList();
  }

  Future<List<Map<String, dynamic>>> fetchJobs() async {
    final res = await _client.get(_uri("/api/job-tracker"));
    if (res.statusCode != 200) {
      throw Exception("Fetch jobs failed: ${res.body}");
    }
    final body = jsonDecode(res.body) as List<dynamic>;
    return body.map((e) => (e as Map<String, dynamic>)).toList();
  }

  Future<int> createJob(Map<String, dynamic> payload) async {
    final res = await _client.post(
      _uri("/api/job-tracker"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      throw Exception("Create job failed: ${res.body}");
    }
    final data = jsonDecode(res.body) as Map<String, dynamic>;
    return (data["id"] as num).toInt();
  }

  Future<void> updateJob(int id, Map<String, dynamic> payload) async {
    final res = await _client.patch(
      _uri("/api/job-tracker/$id"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(payload),
    );
    if (res.statusCode != 200) {
      throw Exception("Update job failed: ${res.body}");
    }
  }

  Future<void> deleteJob(int id) async {
    final res = await _client.delete(_uri("/api/job-tracker/$id"));
    if (res.statusCode != 200) {
      throw Exception("Delete job failed: ${res.body}");
    }
  }
}
