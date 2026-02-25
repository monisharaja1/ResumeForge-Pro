class ResumeModel {
  final int? id;
  final String fullName;
  final String profileTitle;
  final String email;
  final String phone;
  final String address;
  final String summary;
  final String linkedin;
  final String github;
  final String website;
  final List<Map<String, String>> experiences;
  final List<Map<String, String>> educations;
  final List<Map<String, String>> projects;
  final List<Map<String, String>> certifications;
  final List<Map<String, String>> languages;
  final List<String> skills;

  const ResumeModel({
    this.id,
    required this.fullName,
    required this.profileTitle,
    required this.email,
    required this.phone,
    required this.address,
    required this.summary,
    required this.linkedin,
    required this.github,
    required this.website,
    required this.experiences,
    required this.educations,
    required this.projects,
    required this.certifications,
    required this.languages,
    required this.skills,
  });

  factory ResumeModel.empty() {
    return const ResumeModel(
      id: null,
      fullName: "",
      profileTitle: "",
      email: "",
      phone: "",
      address: "",
      summary: "",
      linkedin: "",
      github: "",
      website: "",
      experiences: <Map<String, String>>[],
      educations: <Map<String, String>>[],
      projects: <Map<String, String>>[],
      certifications: <Map<String, String>>[],
      languages: <Map<String, String>>[],
      skills: <String>[],
    );
  }

  factory ResumeModel.fromJson(Map<String, dynamic> json) {
    List<Map<String, String>> _rows(String key, List<String> fields) {
      final src = (json[key] as List?) ?? const [];
      return src.map((e) {
        final m = (e as Map).map((k, v) => MapEntry("$k", "${v ?? ""}"));
        return {
          for (final f in fields) f: (m[f] ?? "").trim(),
        };
      }).toList();
    }

    return ResumeModel(
      id: (json["id"] as num?)?.toInt(),
      fullName: (json["full_name"] ?? "").toString(),
      profileTitle: (json["profile_title"] ?? "").toString(),
      email: (json["email"] ?? "").toString(),
      phone: (json["phone"] ?? "").toString(),
      address: (json["address"] ?? "").toString(),
      summary: (json["summary"] ?? "").toString(),
      linkedin: (json["linkedin"] ?? "").toString(),
      github: (json["github"] ?? "").toString(),
      website: (json["website"] ?? "").toString(),
      experiences: _rows(
        "experiences",
        const ["job_title", "company", "start_date", "end_date", "description"],
      ),
      educations: _rows(
        "educations",
        const ["degree", "institution", "start_date", "end_date", "description"],
      ),
      projects: _rows(
        "projects",
        const ["name", "role", "technologies", "start_date", "end_date", "description", "link"],
      ),
      certifications: _rows(
        "certifications",
        const ["name", "issuer", "date", "link"],
      ),
      languages: _rows(
        "languages",
        const ["name", "proficiency"],
      ),
      skills: ((json["skills"] as List?) ?? const []).map((e) => e.toString()).toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      "id": id,
      "title": fullName.isNotEmpty ? fullName : "Untitled",
      "full_name": fullName,
      "profile_title": profileTitle,
      "email": email,
      "phone": phone,
      "address": address,
      "summary": summary,
      "linkedin": linkedin,
      "github": github,
      "website": website,
      "skills": skills,
      "experiences": experiences,
      "educations": educations,
      "projects": projects,
      "certifications": certifications,
      "languages": languages,
      "achievements": const <Map<String, dynamic>>[],
      "references": const <Map<String, dynamic>>[],
      "custom_sections": const <Map<String, dynamic>>[],
    };
  }
}
