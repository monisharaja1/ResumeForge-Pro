# ResumeForge Flutter Starter

This is a migration starter frontend for your existing Flask backend (`app.py`).

## What is included
- Login screen (uses `/login` form-style auth)
- Resume list + basic builder screen
- Save resume to backend (`/api/resumes`)
- Fetch resumes (`/api/resumes`)
- Load one resume (`/api/resumes/{id}`)

## Prerequisites
- Flutter SDK (stable)
- Running backend:
  - `python app.py`
  - Default backend URL: `http://127.0.0.1:5000`

## Run
1. Open terminal inside `flutter_app`
2. Install packages:
   - `flutter pub get`
3. Run:
   - `flutter run -d chrome`

## Update backend URL
Edit `lib/config.dart`:
- `ApiConfig.baseUrl`

## Next steps
- Add full section editors (experience, education, projects)
- Add PDF export flow (`/api/export-pdf`)
- Add ATS/AI tools from current web UI
