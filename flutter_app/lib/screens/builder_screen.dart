import "dart:math";

import "package:flutter/material.dart";

import "../config.dart";
import "../models/resume.dart";
import "../services/api_service.dart";

class BuilderScreen extends StatefulWidget {
  final ApiService api;
  final String username;
  final VoidCallback onToggleTheme;
  final bool isDark;
  const BuilderScreen({
    super.key,
    required this.api,
    required this.username,
    required this.onToggleTheme,
    required this.isDark,
  });

  @override
  State<BuilderScreen> createState() => _BuilderScreenState();
}

class _BuilderScreenState extends State<BuilderScreen> {
  final _nameCtrl = TextEditingController();
  final _titleCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _addressCtrl = TextEditingController();
  final _summaryCtrl = TextEditingController();
  final _linkedinCtrl = TextEditingController();
  final _githubCtrl = TextEditingController();
  final _websiteCtrl = TextEditingController();
  final _skillsCtrl = TextEditingController();
  final _expCtrl = TextEditingController();
  final _eduCtrl = TextEditingController();
  final _projCtrl = TextEditingController();
  final _certCtrl = TextEditingController();
  final _langCtrl = TextEditingController();
  final _jobDescCtrl = TextEditingController();

  List<Map<String, dynamic>> _resumeRows = [];
  List<Map<String, dynamic>> _publicLinks = [];
  List<Map<String, dynamic>> _jobs = [];
  List<Map<String, dynamic>> _scoreHistory = [];
  int? _selectedId;
  bool _loading = true;
  bool _busy = false;
  String _status = "Ready";
  String _atsSummary = "";
  String _publicStatus = "";
  String _jobsStatus = "";
  int _expiresDays = 7;
  String _templateName = "modern";
  String _pageSize = "letter";
  int _tab = 0;
  final _jobCompanyCtrl = TextEditingController();
  final _jobRoleCtrl = TextEditingController();
  final _jobNotesCtrl = TextEditingController();
  final _jobFollowUpCtrl = TextEditingController();
  String _jobStatus = "saved";

  final List<String> _templates = const [
    "modern",
    "corporate",
    "classic",
    "compact",
    "executive",
    "snack_gray",
    "vision_blue",
    "harsh_minimal",
    "javid_split",
    "teal_modern",
    "astra_clean",
    "metro_sidebar",
    "executive_slate",
    "creative_split",
    "mono_compact",
    "classic_clarity",
    "impact_panel",
    "contemporary_photo",
  ];

  @override
  void initState() {
    super.initState();
    _nameCtrl.text = widget.username;
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    setState(() => _loading = true);
    try {
      await Future.wait([_loadRows(), _loadPublicLinks(), _loadJobs(), _loadScoreHistory()]);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<String> _splitLines(String raw) {
    return raw
        .split("\n")
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
  }

  List<String> _splitRow(String line, int n) {
    final parts = (line.contains("|") ? line.split("|") : line.split(","))
        .map((e) => e.trim())
        .toList();
    while (parts.length < n) {
      parts.add("");
    }
    return parts.take(n).toList();
  }

  List<Map<String, String>> _parseRows(String raw, List<String> keys) {
    return _splitLines(raw).map((line) {
      final vals = _splitRow(line, keys.length);
      return {for (int i = 0; i < keys.length; i++) keys[i]: vals[i]};
    }).toList();
  }

  String _rowsToText(List<Map<String, String>> rows, List<String> keys) {
    return rows.map((r) => keys.map((k) => r[k] ?? "").join(", ")).join("\n");
  }

  ResumeModel _currentModel() {
    return ResumeModel(
      id: _selectedId,
      fullName: _nameCtrl.text.trim(),
      profileTitle: _titleCtrl.text.trim(),
      email: _emailCtrl.text.trim(),
      phone: _phoneCtrl.text.trim(),
      address: _addressCtrl.text.trim(),
      summary: _summaryCtrl.text.trim(),
      linkedin: _linkedinCtrl.text.trim(),
      github: _githubCtrl.text.trim(),
      website: _websiteCtrl.text.trim(),
      experiences: _parseRows(
        _expCtrl.text,
        const ["job_title", "company", "start_date", "end_date", "description"],
      ),
      educations: _parseRows(
        _eduCtrl.text,
        const ["degree", "institution", "start_date", "end_date", "description"],
      ),
      projects: _parseRows(
        _projCtrl.text,
        const ["name", "role", "technologies", "start_date", "end_date", "description", "link"],
      ),
      certifications: _parseRows(
        _certCtrl.text,
        const ["name", "issuer", "date", "link"],
      ),
      languages: _parseRows(
        _langCtrl.text,
        const ["name", "proficiency"],
      ),
      skills: _splitLines(_skillsCtrl.text),
    );
  }

  Future<void> _loadRows() async {
    try {
      _resumeRows = await widget.api.fetchResumeList();
    } catch (e) {
      _status = e.toString();
    }
    if (mounted) setState(() {});
  }

  Future<void> _loadPublicLinks() async {
    try {
      _publicLinks = await widget.api.fetchPublicLinks();
    } catch (_) {
      _publicLinks = [];
    }
    if (mounted) setState(() {});
  }

  Future<void> _loadJobs() async {
    try {
      _jobs = await widget.api.fetchJobs();
    } catch (e) {
      _jobsStatus = e.toString();
    }
    if (mounted) setState(() {});
  }

  Future<void> _loadScoreHistory() async {
    try {
      _scoreHistory = await widget.api.fetchScoreHistory();
    } catch (_) {
      _scoreHistory = [];
    }
    if (mounted) setState(() {});
  }

  Future<void> _loadResume(int id) async {
    setState(() {
      _busy = true;
      _status = "Loading resume...";
    });
    try {
      final r = await widget.api.fetchResume(id);
      _selectedId = r.id;
      _nameCtrl.text = r.fullName;
      _titleCtrl.text = r.profileTitle;
      _emailCtrl.text = r.email;
      _phoneCtrl.text = r.phone;
      _addressCtrl.text = r.address;
      _summaryCtrl.text = r.summary;
      _linkedinCtrl.text = r.linkedin;
      _githubCtrl.text = r.github;
      _websiteCtrl.text = r.website;
      _skillsCtrl.text = r.skills.join("\n");
      _expCtrl.text = _rowsToText(
        r.experiences,
        const ["job_title", "company", "start_date", "end_date", "description"],
      );
      _eduCtrl.text = _rowsToText(
        r.educations,
        const ["degree", "institution", "start_date", "end_date", "description"],
      );
      _projCtrl.text = _rowsToText(
        r.projects,
        const ["name", "role", "technologies", "start_date", "end_date", "description", "link"],
      );
      _certCtrl.text = _rowsToText(
        r.certifications,
        const ["name", "issuer", "date", "link"],
      );
      _langCtrl.text = _rowsToText(
        r.languages,
        const ["name", "proficiency"],
      );
      _status = "Loaded";
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _newResume() {
    _selectedId = null;
    _nameCtrl.text = widget.username;
    _titleCtrl.clear();
    _emailCtrl.clear();
    _phoneCtrl.clear();
    _addressCtrl.clear();
    _summaryCtrl.clear();
    _linkedinCtrl.clear();
    _githubCtrl.clear();
    _websiteCtrl.clear();
    _skillsCtrl.clear();
    _expCtrl.clear();
    _eduCtrl.clear();
    _projCtrl.clear();
    _certCtrl.clear();
    _langCtrl.clear();
    _atsSummary = "";
    _publicStatus = "";
    setState(() => _status = "New resume");
  }

  Future<void> _saveResume() async {
    setState(() {
      _busy = true;
      _status = "Saving...";
    });
    try {
      final id = await widget.api.saveResume(_currentModel());
      _selectedId = id;
      await _loadRows();
      _status = "Saved (ID: $id)";
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Saved resume #$id")),
        );
      }
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _deleteResume() async {
    if (_selectedId == null) return;
    final ok = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text("Delete Resume"),
            content: const Text("This will permanently delete selected resume."),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text("Cancel")),
              FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text("Delete")),
            ],
          ),
        ) ??
        false;
    if (!ok) return;

    setState(() {
      _busy = true;
      _status = "Deleting...";
    });
    try {
      await widget.api.deleteResume(_selectedId!);
      _newResume();
      await _loadRows();
      _status = "Deleted";
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _runAts() async {
    setState(() {
      _busy = true;
      _status = "Running ATS...";
    });
    try {
      final data = await widget.api.atsScore(
        model: _currentModel(),
        jobDescription: _jobDescCtrl.text.trim(),
      );
      final score = data["score"] ?? 0;
      final matched = ((data["matched_keywords"] as List?) ?? []).join(", ");
      final missing = ((data["missing_keywords"] as List?) ?? []).join(", ");
      final section = (data["section_scores"] as Map<String, dynamic>? ?? {});
      _atsSummary =
          "Score: $score/100\n"
          "Summary ${section["summary"] ?? 0}% | Skills ${section["skills"] ?? 0}% | "
          "Experience ${section["experience"] ?? 0}% | Projects ${section["projects"] ?? 0}%\n"
          "Matched: ${matched.isEmpty ? "-" : matched}\n"
          "Missing: ${missing.isEmpty ? "-" : missing}";
      await _loadScoreHistory();
      _status = "ATS ready";
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _exportPdf() async {
    setState(() {
      _busy = true;
      _status = "Exporting PDF...";
    });
    try {
      final bytes = await widget.api.exportPdf(
        model: _currentModel(),
        templateName: _templateName,
        pageSize: _pageSize,
      );
      _status = "PDF generated (${bytes.lengthInBytes} bytes)";
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("PDF ready (${bytes.lengthInBytes} bytes)")),
        );
      }
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _exportWord() async {
    setState(() {
      _busy = true;
      _status = "Exporting Word...";
    });
    try {
      final content = await widget.api.exportWord(model: _currentModel());
      _status = "Word generated (${content.length} chars)";
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Word export ready (${content.length} chars)")),
        );
      }
    } catch (e) {
      _status = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _createPublicLink() async {
    setState(() {
      _busy = true;
      _publicStatus = "Creating public link...";
    });
    try {
      final data = await widget.api.createPublicLink(
        model: _currentModel(),
        expiresDays: _expiresDays,
      );
      _publicStatus = data["url"]?.toString() ?? "Created";
      await _loadPublicLinks();
    } catch (e) {
      _publicStatus = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _revokePublicLink(String token) async {
    setState(() {
      _busy = true;
      _publicStatus = "Revoking link...";
    });
    try {
      await widget.api.revokePublicLink(token);
      _publicStatus = "Link revoked";
      await _loadPublicLinks();
    } catch (e) {
      _publicStatus = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _createJob() async {
    setState(() {
      _busy = true;
      _jobsStatus = "Saving job...";
    });
    try {
      await widget.api.createJob({
        "company": _jobCompanyCtrl.text.trim(),
        "role": _jobRoleCtrl.text.trim(),
        "status": _jobStatus,
        "notes": _jobNotesCtrl.text.trim(),
        "jd_text": _jobDescCtrl.text.trim(),
        "follow_up_date": _jobFollowUpCtrl.text.trim(),
        "reminder_enabled": _jobFollowUpCtrl.text.trim().isNotEmpty,
      });
      _jobCompanyCtrl.clear();
      _jobRoleCtrl.clear();
      _jobNotesCtrl.clear();
      _jobFollowUpCtrl.clear();
      _jobStatus = "saved";
      _jobsStatus = "Job saved";
      await _loadJobs();
    } catch (e) {
      _jobsStatus = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _deleteJob(int id) async {
    setState(() {
      _busy = true;
      _jobsStatus = "Deleting job...";
    });
    try {
      await widget.api.deleteJob(id);
      _jobsStatus = "Job deleted";
      await _loadJobs();
    } catch (e) {
      _jobsStatus = e.toString();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _buildLeftPane() {
    return Column(
      children: [
        const ListTile(
          title: Text(
            "Resumes",
            style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700),
          ),
        ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10),
          child: Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _busy ? null : _newResume,
                  child: const Text("New"),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton(
                  onPressed: _busy ? null : _loadRows,
                  child: const Text("Refresh"),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Expanded(
          child: ListView.builder(
            itemCount: _resumeRows.length,
            itemBuilder: (_, i) {
              final row = _resumeRows[i];
              final id = (row["id"] as num?)?.toInt() ?? -1;
              final title = (row["title"] ?? row["full_name"] ?? "Untitled").toString();
              final selected = id == _selectedId;
              return ListTile(
                selected: selected,
                title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
                subtitle: Text("ID: $id"),
                onTap: _busy ? null : () => _loadResume(id),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildText({
    required TextEditingController ctrl,
    required String label,
    int min = 1,
    int max = 1,
  }) {
    return TextField(
      controller: ctrl,
      minLines: min,
      maxLines: max,
      decoration: InputDecoration(labelText: label, border: const OutlineInputBorder()),
    );
  }

  Widget _buildEditorTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            SizedBox(width: 320, child: _buildText(ctrl: _nameCtrl, label: "Full Name")),
            SizedBox(width: 320, child: _buildText(ctrl: _titleCtrl, label: "Profile Title")),
            SizedBox(width: 320, child: _buildText(ctrl: _emailCtrl, label: "Email")),
            SizedBox(width: 320, child: _buildText(ctrl: _phoneCtrl, label: "Phone")),
            SizedBox(width: 320, child: _buildText(ctrl: _addressCtrl, label: "Address")),
            SizedBox(width: 320, child: _buildText(ctrl: _linkedinCtrl, label: "LinkedIn")),
            SizedBox(width: 320, child: _buildText(ctrl: _githubCtrl, label: "GitHub")),
            SizedBox(width: 320, child: _buildText(ctrl: _websiteCtrl, label: "Website")),
          ],
        ),
        const SizedBox(height: 12),
        _buildText(ctrl: _summaryCtrl, label: "Summary", min: 4, max: 8),
        const SizedBox(height: 12),
        _buildText(ctrl: _skillsCtrl, label: "Skills (one per line)", min: 4, max: 8),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _expCtrl,
          label: "Experience (Job, Company, Start, End, Description)",
          min: 4,
          max: 10,
        ),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _eduCtrl,
          label: "Education (Degree, Institution, Start, End, Description)",
          min: 3,
          max: 8,
        ),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _projCtrl,
          label: "Projects (Name, Role, Tech, Start, End, Description, Link)",
          min: 3,
          max: 8,
        ),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _certCtrl,
          label: "Certifications (Name, Issuer, Date, Link)",
          min: 2,
          max: 6,
        ),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _langCtrl,
          label: "Languages (Name, Proficiency)",
          min: 2,
          max: 6,
        ),
      ],
    );
  }

  Widget _buildToolsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _templateName,
                decoration: const InputDecoration(
                  labelText: "PDF Template",
                  border: OutlineInputBorder(),
                ),
                items: _templates.map((t) => DropdownMenuItem(value: t, child: Text(t))).toList(),
                onChanged: _busy
                    ? null
                    : (v) {
                        if (v == null) return;
                        setState(() => _templateName = v);
                      },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _pageSize,
                decoration: const InputDecoration(
                  labelText: "Page Size",
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: "letter", child: Text("Letter")),
                  DropdownMenuItem(value: "a4", child: Text("A4")),
                ],
                onChanged: _busy
                    ? null
                    : (v) {
                        if (v == null) return;
                        setState(() => _pageSize = v);
                      },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        _buildText(
          ctrl: _jobDescCtrl,
          label: "Job Description (for ATS)",
          min: 6,
          max: 12,
        ),
        const SizedBox(height: 12),
        if (_atsSummary.isNotEmpty)
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: Theme.of(context).colorScheme.outlineVariant),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(_atsSummary),
          ),
        const SizedBox(height: 14),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            OutlinedButton.icon(
              onPressed: _busy ? null : _runAts,
              icon: const Icon(Icons.analytics_outlined),
              label: const Text("ATS Score"),
            ),
            OutlinedButton.icon(
              onPressed: _busy ? null : _exportPdf,
              icon: const Icon(Icons.picture_as_pdf_outlined),
              label: const Text("Export PDF"),
            ),
            OutlinedButton.icon(
              onPressed: _busy ? null : _exportWord,
              icon: const Icon(Icons.description_outlined),
              label: const Text("Export Word"),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPublicLinksTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: DropdownButtonFormField<int>(
                value: _expiresDays,
                decoration: const InputDecoration(
                  labelText: "Expiry (days)",
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 1, child: Text("1 day")),
                  DropdownMenuItem(value: 7, child: Text("7 days")),
                  DropdownMenuItem(value: 14, child: Text("14 days")),
                  DropdownMenuItem(value: 30, child: Text("30 days")),
                ],
                onChanged: _busy
                    ? null
                    : (v) {
                        if (v == null) return;
                        setState(() => _expiresDays = v);
                      },
              ),
            ),
            const SizedBox(width: 10),
            ElevatedButton(
              onPressed: _busy ? null : _createPublicLink,
              child: const Text("Create Link"),
            ),
            const SizedBox(width: 10),
            OutlinedButton(
              onPressed: _busy ? null : _loadPublicLinks,
              child: const Text("Refresh"),
            ),
          ],
        ),
        if (_publicStatus.isNotEmpty) ...[
          const SizedBox(height: 10),
          SelectableText(_publicStatus),
        ],
        const SizedBox(height: 14),
        Text("Generated Links (${_publicLinks.length})",
            style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ..._publicLinks.map((row) {
          final title = (row["title"] ?? "Public Resume").toString();
          final token = (row["token"] ?? "").toString();
          final url = token.isEmpty ? "" : "${ApiConfig.baseUrl}/public/$token";
          final expires = (row["expires_at"] ?? "-").toString();
          final created = (row["created"] ?? "-").toString();
          final revoked = (row["revoked"] == 1);
          return Card(
            child: ListTile(
              title: Text(title),
              subtitle: SelectableText(
                "Expires: $expires\nCreated: $created\n${url.isEmpty ? token : url}",
              ),
              trailing: revoked
                  ? const Text("Revoked")
                  : IconButton(
                      onPressed: _busy ? null : () => _revokePublicLink(token),
                      icon: const Icon(Icons.block),
                      tooltip: "Revoke",
                    ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildJobsTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            SizedBox(width: 260, child: _buildText(ctrl: _jobCompanyCtrl, label: "Company")),
            SizedBox(width: 260, child: _buildText(ctrl: _jobRoleCtrl, label: "Role")),
            SizedBox(
              width: 220,
              child: DropdownButtonFormField<String>(
                value: _jobStatus,
                decoration: const InputDecoration(
                  labelText: "Status",
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: "saved", child: Text("Saved")),
                  DropdownMenuItem(value: "applied", child: Text("Applied")),
                  DropdownMenuItem(value: "interview", child: Text("Interview")),
                  DropdownMenuItem(value: "offer", child: Text("Offer")),
                  DropdownMenuItem(value: "rejected", child: Text("Rejected")),
                ],
                onChanged: _busy
                    ? null
                    : (v) {
                        if (v == null) return;
                        setState(() => _jobStatus = v);
                      },
              ),
            ),
            SizedBox(
              width: 220,
              child: _buildText(
                ctrl: _jobFollowUpCtrl,
                label: "Follow-up Date (YYYY-MM-DD)",
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        _buildText(ctrl: _jobNotesCtrl, label: "Notes", min: 2, max: 5),
        const SizedBox(height: 10),
        Wrap(
          spacing: 10,
          children: [
            ElevatedButton.icon(
              onPressed: _busy ? null : _createJob,
              icon: const Icon(Icons.add),
              label: const Text("Add Job"),
            ),
            OutlinedButton.icon(
              onPressed: _busy ? null : _loadJobs,
              icon: const Icon(Icons.refresh),
              label: const Text("Refresh"),
            ),
          ],
        ),
        if (_jobsStatus.isNotEmpty) ...[
          const SizedBox(height: 10),
          Text(_jobsStatus),
        ],
        const SizedBox(height: 14),
        Text("Tracked Jobs (${_jobs.length})",
            style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ..._jobs.map((row) {
          final id = (row["id"] as num?)?.toInt() ?? -1;
          final company = (row["company"] ?? "-").toString();
          final role = (row["role"] ?? "-").toString();
          final status = (row["status"] ?? "saved").toString();
          final follow = (row["follow_up_date"] ?? "").toString();
          return Card(
            child: ListTile(
              title: Text("$company - $role"),
              subtitle: Text("Status: $status${follow.isNotEmpty ? "\nFollow-up: $follow" : ""}"),
              trailing: IconButton(
                onPressed: _busy ? null : () => _deleteJob(id),
                icon: const Icon(Icons.delete_outline),
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildHistoryTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            const Text("ATS Score History", style: TextStyle(fontWeight: FontWeight.w700)),
            const Spacer(),
            OutlinedButton.icon(
              onPressed: _busy ? null : _loadScoreHistory,
              icon: const Icon(Icons.refresh),
              label: const Text("Refresh"),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (_scoreHistory.isEmpty)
          const Card(
            child: ListTile(
              title: Text("No history yet"),
              subtitle: Text("Run ATS score to build history."),
            ),
          ),
        ..._scoreHistory.map((row) {
          final score = (row["score"] ?? 0).toString();
          final source = (row["source"] ?? "-").toString();
          final created = (row["created"] ?? "-").toString();
          final title = (row["resume_title"] ?? "Untitled").toString();
          return Card(
            child: ListTile(
              leading: CircleAvatar(child: Text(score)),
              title: Text(title),
              subtitle: Text("Source: $source\n$created"),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildMainPane() {
    final tabs = [
      _buildEditorTab(),
      _buildToolsTab(),
      _buildPublicLinksTab(),
      _buildJobsTab(),
      _buildHistoryTab(),
    ];
    return Column(
      children: [
        Material(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("Editor"),
                  selected: _tab == 0,
                  onSelected: (_) => setState(() => _tab = 0),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("Tools"),
                  selected: _tab == 1,
                  onSelected: (_) => setState(() => _tab = 1),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("Public Links"),
                  selected: _tab == 2,
                  onSelected: (_) => setState(() => _tab = 2),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("Jobs"),
                  selected: _tab == 3,
                  onSelected: (_) => setState(() => _tab = 3),
                ),
                const SizedBox(width: 8),
                ChoiceChip(
                  label: const Text("History"),
                  selected: _tab == 4,
                  onSelected: (_) => setState(() => _tab = 4),
                ),
                const SizedBox(width: 20),
                TextButton.icon(
                  onPressed: _busy ? null : _saveResume,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text("Save"),
                ),
                const SizedBox(width: 8),
                TextButton.icon(
                  onPressed: (_busy || _selectedId == null) ? null : _deleteResume,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text("Delete"),
                ),
                const SizedBox(width: 8),
              ],
            ),
          ),
        ),
        Expanded(child: tabs[min(max(_tab, 0), tabs.length - 1)]),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("ResumeForge Flutter - ${widget.username}"),
        actions: [
          IconButton(
            onPressed: widget.onToggleTheme,
            icon: Icon(widget.isDark ? Icons.light_mode : Icons.dark_mode),
            tooltip: "Toggle theme",
          ),
          if (_busy)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: Center(child: SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))),
            ),
          Padding(
            padding: const EdgeInsets.only(right: 14),
            child: Center(
              child: Text(
                _status,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : LayoutBuilder(
              builder: (context, constraints) {
                final compact = constraints.maxWidth < 980;
                if (compact) {
                  return Column(
                    children: [
                      SizedBox(
                        height: 210,
                        child: _buildLeftPane(),
                      ),
                      const Divider(height: 1),
                      Expanded(child: _buildMainPane()),
                    ],
                  );
                }
                return Row(
                  children: [
                    SizedBox(width: 300, child: _buildLeftPane()),
                    const VerticalDivider(width: 1),
                    Expanded(child: _buildMainPane()),
                  ],
                );
              },
            ),
    );
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _titleCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _addressCtrl.dispose();
    _summaryCtrl.dispose();
    _linkedinCtrl.dispose();
    _githubCtrl.dispose();
    _websiteCtrl.dispose();
    _skillsCtrl.dispose();
    _expCtrl.dispose();
    _eduCtrl.dispose();
    _projCtrl.dispose();
    _certCtrl.dispose();
    _langCtrl.dispose();
    _jobDescCtrl.dispose();
    _jobCompanyCtrl.dispose();
    _jobRoleCtrl.dispose();
    _jobNotesCtrl.dispose();
    _jobFollowUpCtrl.dispose();
    super.dispose();
  }
}
