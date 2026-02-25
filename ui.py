"""
Graphical user interface built with Tkinter.
Main window with resume list and tabbed editor.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database
from pdf_generator import PDFGenerator
from models import Resume, Experience, Education, Project, Certification, Language
import os


class ResumeApp:
    def __init__(self, db):
        self.db = db
        self.root = tk.Tk()
        self.root.title("Resume Builder Pro")
        self.root.geometry("1120x760")
        self.root.minsize(980, 640)

        # Current state
        self.current_resume_id = None
        self.current_resume_data = {
            'full_name': '',
            'email': '',
            'phone': '',
            'summary': '',
            'experiences': [],
            'educations': [],
            'skills': [],
            'projects': [],
            'certifications': [],
            'languages': []
        }

        self._setup_styles()
        self._build_ui()
        self._refresh_resume_list()

    def _setup_styles(self):
        """Apply a cleaner desktop theme for ttk + tk widgets."""
        self._colors = {
            "bg": "#f2f6ff",
            "card": "#ffffff",
            "text": "#172033",
            "muted": "#5d6b89",
            "line": "#d4deef",
            "accent": "#0f766e",
            "danger": "#b91c1c",
        }
        self.root.configure(bg=self._colors["bg"])

        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Root.TFrame", background=self._colors["bg"])
        style.configure("Card.TFrame", background=self._colors["card"], relief="flat")
        style.configure("Title.TLabel", background=self._colors["card"], foreground=self._colors["text"], font=("Segoe UI", 12, "bold"))
        style.configure("TLabel", background=self._colors["card"], foreground=self._colors["text"], font=("Segoe UI", 10))
        style.configure("TEntry", fieldbackground="#fbfdff", foreground=self._colors["text"], bordercolor=self._colors["line"])
        style.configure("TCombobox", fieldbackground="#fbfdff", foreground=self._colors["text"])
        style.configure("TNotebook", background=self._colors["card"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(12, 6), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#e8f8f6"), ("!selected", "#edf3ff")])
        style.configure("TButton", padding=(10, 6), font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=self._colors["accent"], foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#0d665f"), ("pressed", "#0b5a54")])
        style.configure("Danger.TButton", background=self._colors["danger"], foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#9f1c1c"), ("pressed", "#7f1515")])

    def _build_ui(self):
        """Construct the main window layout."""
        # Main paned window: left (list) | right (editor)
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # ----- Left panel: resume list -----
        left_frame = ttk.Frame(main_pane, width=280, style="Card.TFrame")
        main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="My Resumes", style="Title.TLabel").pack(pady=(10, 6))

        # Listbox with scrollbar
        list_frame = ttk.Frame(left_frame, style="Card.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.resume_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg=self._colors["text"],
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=self._colors["line"],
            selectbackground="#d9f3ef",
            selectforeground=self._colors["text"],
        )
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.resume_listbox.yview)
        self.resume_listbox.configure(yscrollcommand=scrollbar.set)
        self.resume_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.resume_listbox.bind('<<ListboxSelect>>', self._on_resume_select)

        # Buttons under list
        btn_frame = ttk.Frame(left_frame, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=(2, 10), padx=10)

        ttk.Button(btn_frame, text="New", command=self._on_new, style="Primary.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Delete", command=self._on_delete, style="Danger.TButton").pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Export PDF", command=self._on_export_pdf).pack(side=tk.LEFT, padx=3)

        # ----- Right panel: editor -----
        right_frame = ttk.Frame(main_pane, style="Card.TFrame")
        main_pane.add(right_frame, weight=3)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_personal_tab()
        self._build_experience_tab()
        self._build_education_tab()
        self._build_project_tab()
        self._build_cert_tab()
        self._build_lang_tab()
        self._build_skills_tab()

        # Save button at bottom
        save_frame = ttk.Frame(right_frame, style="Card.TFrame")
        save_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        ttk.Button(save_frame, text="Save Resume", command=self._on_save, style="Primary.TButton").pack(side=tk.RIGHT, padx=5)

    # ---------- Tab construction ----------
    def _build_personal_tab(self):
        """Tab 1: Full name, email, phone, summary."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Personal")

        # Grid layout
        pad = {'padx': 10, 'pady': 5}
        row = 0

        ttk.Label(tab, text="Full Name:").grid(row=row, column=0, sticky='w', **pad)
        self.entry_fullname = ttk.Entry(tab, width=40)
        self.entry_fullname.grid(row=row, column=1, sticky='w', **pad)
        row += 1

        ttk.Label(tab, text="Email:").grid(row=row, column=0, sticky='w', **pad)
        self.entry_email = ttk.Entry(tab, width=40)
        self.entry_email.grid(row=row, column=1, sticky='w', **pad)
        row += 1

        ttk.Label(tab, text="Phone:").grid(row=row, column=0, sticky='w', **pad)
        self.entry_phone = ttk.Entry(tab, width=40)
        self.entry_phone.grid(row=row, column=1, sticky='w', **pad)
        row += 1

        ttk.Label(tab, text="Professional Summary:").grid(row=row, column=0, sticky='nw', **pad)
        self.text_summary = tk.Text(tab, width=50, height=8)
        self.text_summary.grid(row=row, column=1, sticky='w', **pad)

    def _build_experience_tab(self):
        """Tab 2: Work experiences - list and add/edit/delete."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Experience")

        # Treeview to show experiences
        columns = ('job_title', 'company', 'start_date', 'end_date')
        self.exp_tree = ttk.Treeview(tab, columns=columns, show='headings', height=8)
        self.exp_tree.heading('job_title', text='Job Title')
        self.exp_tree.heading('company', text='Company')
        self.exp_tree.heading('start_date', text='Start')
        self.exp_tree.heading('end_date', text='End')

        self.exp_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Experience", command=self._add_experience).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit Experience", command=self._edit_experience).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Experience", command=self._remove_experience).pack(side=tk.LEFT, padx=2)

        # Store experiences in memory
        self.experiences = []  # list of dicts

    def _build_education_tab(self):
        """Tab 3: Education - similar to experience."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Education")

        columns = ('degree', 'institution', 'start_date', 'end_date')
        self.edu_tree = ttk.Treeview(tab, columns=columns, show='headings', height=8)
        self.edu_tree.heading('degree', text='Degree')
        self.edu_tree.heading('institution', text='Institution')
        self.edu_tree.heading('start_date', text='Start')
        self.edu_tree.heading('end_date', text='End')

        self.edu_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Education", command=self._add_education).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit Education", command=self._edit_education).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Education", command=self._remove_education).pack(side=tk.LEFT, padx=2)

        self.educations = []

    def _build_project_tab(self):
        """Tab 3.5: Projects - list and add/edit/delete."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Projects")

        columns = ('name', 'role', 'technologies')
        self.proj_tree = ttk.Treeview(tab, columns=columns, show='headings', height=8)
        self.proj_tree.heading('name', text='Project Name')
        self.proj_tree.heading('role', text='Role')
        self.proj_tree.heading('technologies', text='Tech Stack')
        
        self.proj_tree.column('name', width=150)
        self.proj_tree.column('role', width=100)
        self.proj_tree.column('technologies', width=200)

        self.proj_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Project", command=self._add_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Edit Project", command=self._edit_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Project", command=self._remove_project).pack(side=tk.LEFT, padx=2)

        self.projects = []

    def _build_cert_tab(self):
        """Tab 3.6: Certifications."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Certifications")

        columns = ('name', 'issuer', 'date')
        self.cert_tree = ttk.Treeview(tab, columns=columns, show='headings', height=6)
        self.cert_tree.heading('name', text='Name')
        self.cert_tree.heading('issuer', text='Issuer')
        self.cert_tree.heading('date', text='Date')
        self.cert_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Add Cert", command=self._add_cert).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove Cert", command=self._remove_cert).pack(side=tk.LEFT, padx=2)

        self.certifications = []

    def _build_lang_tab(self):
        """Tab 3.7: Languages."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Languages")

        columns = ('name', 'proficiency')
        self.lang_tree = ttk.Treeview(tab, columns=columns, show='headings', height=6)
        self.lang_tree.heading('name', text='Language')
        self.lang_tree.heading('proficiency', text='Proficiency')
        self.lang_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Simple entry for language
        self.lang_name_entry = ttk.Entry(btn_frame, width=15)
        self.lang_name_entry.pack(side=tk.LEFT, padx=2)
        self.lang_prof_entry = ttk.Combobox(btn_frame, values=["Native", "Fluent", "Intermediate", "Basic"], width=10)
        self.lang_prof_entry.set("Fluent")
        self.lang_prof_entry.pack(side=tk.LEFT, padx=2)

        ttk.Button(btn_frame, text="Add", command=self._add_lang).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Remove", command=self._remove_lang).pack(side=tk.LEFT, padx=2)

        self.languages = []

    def _build_skills_tab(self):
        """Tab 4: Skills - listbox with add/remove."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Skills")

        # Listbox for skills
        self.skills_listbox = tk.Listbox(tab, height=12)
        self.skills_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Entry and Add button
        entry_frame = ttk.Frame(tab)
        entry_frame.pack(fill=tk.X, pady=5)

        self.skill_entry = ttk.Entry(entry_frame)
        self.skill_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,2))
        ttk.Button(entry_frame, text="Add Skill", command=self._add_skill).pack(side=tk.LEFT, padx=2)

        # Remove button
        ttk.Button(tab, text="Remove Selected Skill", command=self._remove_skill).pack(pady=2)

        self.skills = []

    # ---------- Event handlers ----------
    def _refresh_resume_list(self):
        """Reload the list of resumes from DB and update listbox."""
        resumes = self.db.get_all_resumes()
        self.resume_listbox.delete(0, tk.END)
        for r in resumes:
            display = f"{r['full_name']} ({r['updated'][:10]})"
            self.resume_listbox.insert(tk.END, display)
        # Store IDs for later retrieval
        self.resume_ids = [r['id'] for r in resumes]

    def _on_resume_select(self, event):
        """Load selected resume into editor."""
        selection = self.resume_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        resume_id = self.resume_ids[index]
        data = self.db.get_resume_data(resume_id)
        if data:
            self.current_resume_id = resume_id
            self._populate_form(data)

    def _populate_form(self, data):
        """Fill all form fields with the given resume data."""
        # Personal
        self.entry_fullname.delete(0, tk.END)
        self.entry_fullname.insert(0, data.get('full_name', ''))
        self.entry_email.delete(0, tk.END)
        self.entry_email.insert(0, data.get('email', ''))
        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, data.get('phone', ''))
        self.text_summary.delete(1.0, tk.END)
        self.text_summary.insert(1.0, data.get('summary', ''))

        # Experiences
        self.experiences = data.get('experiences', [])
        self._refresh_exp_tree()

        # Educations
        self.educations = data.get('educations', [])
        self._refresh_edu_tree()

        # Projects
        self.projects = data.get('projects', [])
        self._refresh_proj_tree()

        # Certifications
        self.certifications = data.get('certifications', [])
        self._refresh_cert_tree()

        # Languages
        self.languages = data.get('languages', [])
        self._refresh_lang_tree()

        # Skills
        self.skills = data.get('skills', [])
        self._refresh_skills_listbox()

    def _collect_form_data(self):
        """Gather all current UI data into a dictionary."""
        data = {
            'full_name': self.entry_fullname.get().strip(),
            'email': self.entry_email.get().strip(),
            'phone': self.entry_phone.get().strip(),
            'summary': self.text_summary.get(1.0, tk.END).strip(),
            'experiences': self.experiences,
            'educations': self.educations,
            'projects': self.projects,
            'certifications': self.certifications,
            'languages': self.languages,
            'skills': self.skills
        }
        return data

    def _on_new(self):
        """Clear form and reset state for a new resume."""
        self.current_resume_id = None
        self.experiences = []
        self.educations = []
        self.projects = []
        self.certifications = []
        self.languages = []
        self.skills = []
        self.entry_fullname.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_phone.delete(0, tk.END)
        self.text_summary.delete(1.0, tk.END)
        self._refresh_exp_tree()
        self._refresh_edu_tree()
        self._refresh_proj_tree()
        self._refresh_cert_tree()
        self._refresh_lang_tree()
        self._refresh_skills_listbox()

    def _on_save(self):
        """Save the current resume to database."""
        data = self._collect_form_data()
        if not data['full_name']:
            messagebox.showwarning("Missing Name", "Full name is required.")
            return

        if self.current_resume_id is None:
            # Create new
            new_id = self.db.create_resume(data)
            self.current_resume_id = new_id
            messagebox.showinfo("Success", "Resume created successfully.")
        else:
            # Update existing
            self.db.update_resume(self.current_resume_id, data)
            messagebox.showinfo("Success", "Resume updated successfully.")
        self._refresh_resume_list()

    def _on_delete(self):
        """Delete the currently selected resume."""
        if self.current_resume_id is None:
            messagebox.showwarning("No Selection", "No resume is selected.")
            return
        if messagebox.askyesno("Confirm Delete", "Delete this resume permanently?"):
            self.db.delete_resume(self.current_resume_id)
            self._refresh_resume_list()
            self._on_new()  # clear form
            messagebox.showinfo("Deleted", "Resume deleted.")

    def _on_export_pdf(self):
        """Export the current resume data to a PDF file."""
        data = self._collect_form_data()
        if not data['full_name']:
            messagebox.showwarning("Missing Data", "Cannot export an empty resume.")
            return

        # Ask user for save location
        filename = f"{data['full_name'].replace(' ', '_')}_resume.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=filename
        )
        if not file_path:
            return

        try:
            resume = Resume(
                full_name=data.get('full_name', ''),
                email=data.get('email', ''),
                phone=data.get('phone', ''),
                summary=data.get('summary', ''),
                experiences=[Experience(**exp) for exp in data.get('experiences', [])],
                educations=[Education(**edu) for edu in data.get('educations', [])],
                projects=[Project(**proj) for proj in data.get('projects', [])],
                certifications=[Certification(**c) for c in data.get('certifications', [])],
                languages=[Language(**l) for l in data.get('languages', [])],
                skills=list(data.get('skills', []))
            )
            PDFGenerator.generate(resume, file_path)
            messagebox.showinfo("Success", f"PDF saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Could not generate PDF:\n{str(e)}")

    # ---------- Experience methods ----------
    def _add_experience(self):
        self._open_experience_dialog()

    def _edit_experience(self):
        selected = self.exp_tree.selection()
        if not selected:
            return
        index = self.exp_tree.index(selected[0])
        exp = self.experiences[index]
        self._open_experience_dialog(exp, index)

    def _remove_experience(self):
        selected = self.exp_tree.selection()
        if not selected:
            return
        index = self.exp_tree.index(selected[0])
        del self.experiences[index]
        self._refresh_exp_tree()

    def _open_experience_dialog(self, exp=None, edit_index=None):
        """Popup window to add/edit an experience entry."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add/Edit Experience")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = ['job_title', 'company', 'start_date', 'end_date', 'description']
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(dialog, text=field.replace('_', ' ').title() + ":").grid(row=i, column=0, sticky='e', padx=5, pady=5)
            if field == 'description':
                w = tk.Text(dialog, width=40, height=5)
            else:
                w = ttk.Entry(dialog, width=40)
            w.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[field] = w

        if exp:
            for field in fields:
                if field == 'description':
                    entries[field].insert(1.0, exp.get(field, ''))
                else:
                    entries[field].insert(0, exp.get(field, ''))

        def save():
            new_exp = {}
            for field in fields:
                if field == 'description':
                    value = entries[field].get(1.0, tk.END).strip()
                else:
                    value = entries[field].get().strip()
                new_exp[field] = value
            if edit_index is not None:
                self.experiences[edit_index] = new_exp
            else:
                self.experiences.append(new_exp)
            self._refresh_exp_tree()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=1, pady=10, sticky='e')

    def _refresh_exp_tree(self):
        """Clear and reload the experience treeview."""
        for item in self.exp_tree.get_children():
            self.exp_tree.delete(item)
        for exp in self.experiences:
            self.exp_tree.insert('', tk.END, values=(
                exp.get('job_title', ''),
                exp.get('company', ''),
                exp.get('start_date', ''),
                exp.get('end_date', '')
            ))

    # ---------- Education methods ----------
    def _add_education(self):
        self._open_education_dialog()

    def _edit_education(self):
        selected = self.edu_tree.selection()
        if not selected:
            return
        index = self.edu_tree.index(selected[0])
        edu = self.educations[index]
        self._open_education_dialog(edu, index)

    def _remove_education(self):
        selected = self.edu_tree.selection()
        if not selected:
            return
        index = self.edu_tree.index(selected[0])
        del self.educations[index]
        self._refresh_edu_tree()

    def _open_education_dialog(self, edu=None, edit_index=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add/Edit Education")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = ['degree', 'institution', 'start_date', 'end_date', 'description']
        entries = {}

        for i, field in enumerate(fields):
            ttk.Label(dialog, text=field.replace('_', ' ').title() + ":").grid(row=i, column=0, sticky='e', padx=5, pady=5)
            if field == 'description':
                w = tk.Text(dialog, width=40, height=5)
            else:
                w = ttk.Entry(dialog, width=40)
            w.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[field] = w

        if edu:
            for field in fields:
                if field == 'description':
                    entries[field].insert(1.0, edu.get(field, ''))
                else:
                    entries[field].insert(0, edu.get(field, ''))

        def save():
            new_edu = {}
            for field in fields:
                if field == 'description':
                    value = entries[field].get(1.0, tk.END).strip()
                else:
                    value = entries[field].get().strip()
                new_edu[field] = value
            if edit_index is not None:
                self.educations[edit_index] = new_edu
            else:
                self.educations.append(new_edu)
            self._refresh_edu_tree()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=1, pady=10, sticky='e')

    def _refresh_edu_tree(self):
        for item in self.edu_tree.get_children():
            self.edu_tree.delete(item)
        for edu in self.educations:
            self.edu_tree.insert('', tk.END, values=(
                edu.get('degree', ''),
                edu.get('institution', ''),
                edu.get('start_date', ''),
                edu.get('end_date', '')
            ))

    # ---------- Project methods ----------
    def _add_project(self):
        self._open_project_dialog()

    def _edit_project(self):
        selected = self.proj_tree.selection()
        if not selected:
            return
        index = self.proj_tree.index(selected[0])
        proj = self.projects[index]
        self._open_project_dialog(proj, index)

    def _remove_project(self):
        selected = self.proj_tree.selection()
        if not selected:
            return
        index = self.proj_tree.index(selected[0])
        del self.projects[index]
        self._refresh_proj_tree()

    def _open_project_dialog(self, proj=None, edit_index=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add/Edit Project")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = ['name', 'role', 'technologies', 'link', 'description']
        entries = {}

        for i, field in enumerate(fields):
            label_text = field.replace('_', ' ').title() + ":"
            ttk.Label(dialog, text=label_text).grid(row=i, column=0, sticky='e', padx=5, pady=5)
            
            if field == 'description':
                w = tk.Text(dialog, width=40, height=5)
            else:
                w = ttk.Entry(dialog, width=40)
            
            w.grid(row=i, column=1, padx=5, pady=5, sticky='w')
            entries[field] = w

        if proj:
            for field in fields:
                val = proj.get(field, '')
                if field == 'description':
                    entries[field].insert(1.0, val)
                else:
                    entries[field].insert(0, val)

        def save():
            new_proj = {}
            for field in fields:
                if field == 'description':
                    value = entries[field].get(1.0, tk.END).strip()
                else:
                    value = entries[field].get().strip()
                new_proj[field] = value
            
            # Handle dates (optional for projects, but good to have empty defaults)
            new_proj['start_date'] = proj.get('start_date', '') if proj else ''
            new_proj['end_date'] = proj.get('end_date', '') if proj else ''

            if edit_index is not None:
                self.projects[edit_index] = new_proj
            else:
                self.projects.append(new_proj)
            self._refresh_proj_tree()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=1, pady=10, sticky='e')

    def _refresh_proj_tree(self):
        for item in self.proj_tree.get_children():
            self.proj_tree.delete(item)
        for proj in self.projects:
            self.proj_tree.insert('', tk.END, values=(
                proj.get('name', ''),
                proj.get('role', ''),
                proj.get('technologies', '')
            ))

    # ---------- Certification methods ----------
    def _add_cert(self):
        # Simple dialog for certs
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Certification")
        
        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=5, pady=5)
        e_name = ttk.Entry(dialog)
        e_name.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Issuer:").grid(row=1, column=0, padx=5, pady=5)
        e_issuer = ttk.Entry(dialog)
        e_issuer.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Date:").grid(row=2, column=0, padx=5, pady=5)
        e_date = ttk.Entry(dialog)
        e_date.grid(row=2, column=1, padx=5, pady=5)

        def save():
            self.certifications.append({
                'name': e_name.get(),
                'issuer': e_issuer.get(),
                'date': e_date.get()
            })
            self._refresh_cert_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="Save", command=save).grid(row=3, column=1, pady=10)

    def _remove_cert(self):
        sel = self.cert_tree.selection()
        if sel:
            idx = self.cert_tree.index(sel[0])
            del self.certifications[idx]
            self._refresh_cert_tree()

    def _refresh_cert_tree(self):
        for item in self.cert_tree.get_children():
            self.cert_tree.delete(item)
        for c in self.certifications:
            self.cert_tree.insert('', tk.END, values=(c.get('name'), c.get('issuer'), c.get('date')))

    # ---------- Language methods ----------
    def _add_lang(self):
        name = self.lang_name_entry.get().strip()
        prof = self.lang_prof_entry.get()
        if name:
            self.languages.append({'name': name, 'proficiency': prof})
            self.lang_name_entry.delete(0, tk.END)
            self._refresh_lang_tree()

    def _remove_lang(self):
        sel = self.lang_tree.selection()
        if sel:
            idx = self.lang_tree.index(sel[0])
            del self.languages[idx]
            self._refresh_lang_tree()

    def _refresh_lang_tree(self):
        for item in self.lang_tree.get_children():
            self.lang_tree.delete(item)
        for l in self.languages:
            self.lang_tree.insert('', tk.END, values=(l.get('name'), l.get('proficiency')))

    # ---------- Skills methods ----------
    def _add_skill(self):
        skill = self.skill_entry.get().strip()
        if skill:
            self.skills.append(skill)
            self.skills_listbox.insert(tk.END, skill)
            self.skill_entry.delete(0, tk.END)

    def _remove_skill(self):
        selection = self.skills_listbox.curselection()
        if selection:
            index = selection[0]
            del self.skills[index]
            self.skills_listbox.delete(index)

    def _refresh_skills_listbox(self):
        self.skills_listbox.delete(0, tk.END)
        for skill in self.skills:
            self.skills_listbox.insert(tk.END, skill)

    # ---------- Run ----------
    def run(self):
        self.root.mainloop()

"""
Advanced Tkinter/ttk GUI with preview, threading, undo/redo, search, and settings.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import threading
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
import io

from models import Resume, Experience, Education, Project, Certification, Language
from database import Database
from pdf_generator import PDFGenerator
from config import AppConfig
import utils

logger = utils.setup_logger(__name__)


class AdvancedResumeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{AppConfig.APP_NAME} v{AppConfig.APP_VERSION}")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)

        # Database
        self.db = Database(AppConfig.DB_PATH)

        # Current resume
        self.current_resume = Resume()
        self.current_id = None
        self.undo_stack = []
        self.redo_stack = []

        # Build UI
        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_main_paned()
        self._bind_shortcuts()

        # Load recent or new
        self._init_resume()

        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)
        self.root.mainloop()

    # ---------- UI Construction ----------
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6)
        style.configure("TLabel", padding=4)
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_resume, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_resume_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_resume, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_resume_as)
        file_menu.add_separator()
        file_menu.add_command(label="Import JSON...", command=self.import_json)
        file_menu.add_command(label="Export JSON...", command=self.export_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Preferences...", command=self.open_preferences)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Export PDF...", command=self.export_pdf, accelerator="Ctrl+P")
        tools_menu.add_command(label="Backup Database", command=self.backup_db)
        tools_menu.add_command(label="Restore Backup...", command=self.restore_db)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def _build_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="➕ New", command=self.new_resume).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📂 Open", command=self.open_resume_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Save", command=self.save_resume).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🖨️ PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Resume selector
        self.resume_var = tk.StringVar()
        self.resume_combo = ttk.Combobox(toolbar, textvariable=self.resume_var,
                                          state="readonly", width=40)
        self.resume_combo.pack(side=tk.LEFT, padx=5)
        self.resume_combo.bind("<<ComboboxSelected>>", self._on_resume_selected)
        self._refresh_resume_list()

        ttk.Button(toolbar, text="🗑️ Delete", command=self.delete_resume).pack(side=tk.LEFT, padx=2)

    def _build_main_paned(self):
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left: Notebook (editor)
        self.editor_frame = ttk.Frame(main_pane, width=700)
        main_pane.add(self.editor_frame, weight=2)
        self._build_editor()

        # Right: Preview
        self.preview_frame = ttk.Frame(main_pane, width=500)
        main_pane.add(self.preview_frame, weight=1)
        self._build_preview()

    def _build_editor(self):
        notebook = ttk.Notebook(self.editor_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Personal tab
        self.personal_tab = ttk.Frame(notebook)
        notebook.add(self.personal_tab, text="👤 Personal")
        self._build_personal_tab()

        # Experience tab
        self.exp_tab = ttk.Frame(notebook)
        notebook.add(self.exp_tab, text="💼 Experience")
        self._build_exp_tab()

        # Education tab
        self.edu_tab = ttk.Frame(notebook)
        notebook.add(self.edu_tab, text="🎓 Education")
        self._build_edu_tab()

        # Projects tab
        self.proj_tab = ttk.Frame(notebook)
        notebook.add(self.proj_tab, text="🚀 Projects")
        self._build_proj_tab()

        # Certifications tab
        self.cert_tab = ttk.Frame(notebook)
        notebook.add(self.cert_tab, text="📜 Certifications")
        self._build_cert_tab()

        # Languages tab
        self.lang_tab = ttk.Frame(notebook)
        notebook.add(self.lang_tab, text="🗣️ Languages")
        self._build_lang_tab()

        # Skills tab
        self.skills_tab = ttk.Frame(notebook)
        notebook.add(self.skills_tab, text="🔧 Skills")
        self._build_skills_tab()

    # Detailed tab building methods omitted for brevity – they follow pattern of creating
    # entry fields and using grid layout. Full code available in the complete package.
    # (Will provide a condensed but functional version in final answer.)

    def _build_preview(self):
        """Right panel with live HTML-like preview."""
        ttk.Label(self.preview_frame, text="Live Preview", font=("Helvetica", 14, "bold")).pack(pady=5)
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="white", highlightthickness=0)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self._update_preview()

    def _update_preview(self):
        """Render preview as styled text on canvas."""
        self.preview_canvas.delete("all")
        y = 20
        # Simple text preview – can be enhanced to draw styled boxes
        if self.current_resume.full_name:
            self.preview_canvas.create_text(20, y, anchor="nw", text=self.current_resume.full_name,
                                            font=("Helvetica", 20, "bold"), fill="#2c3e50")
            y += 40
        # ... more preview rendering ...
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    # ---------- Core Functionality ----------
    def _save_state_for_undo(self):
        """Push current state onto undo stack."""
        self.undo_stack.append(utils.resume_to_dict(self.current_resume))
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            self.redo_stack.append(utils.resume_to_dict(self.current_resume))
            self.current_resume = utils.dict_to_resume(state)
            self._refresh_ui_from_resume()
            self._update_preview()

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(utils.resume_to_dict(self.current_resume))
            self.current_resume = utils.dict_to_resume(state)
            self._refresh_ui_from_resume()
            self._update_preview()

    def new_resume(self):
        self._save_state_for_undo()
        self.current_resume = Resume(title="Untitled")
        self.current_id = None
        self._refresh_ui_from_resume()
        self._update_preview()

    def save_resume(self):
        """Save current resume to database."""
        self._gather_form_data()
        self.current_resume.updated = datetime.now()
        if not self.current_resume.title:
            self.current_resume.title = self.current_resume.full_name or "Untitled"
        try:
            self.current_id = self.db.save_resume(self.current_resume)
            self.current_resume.id = self.current_id
            self._save_state_for_undo()
            self._refresh_resume_list()
            status_bar.config(text=f"Saved: {self.current_resume.title}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def open_resume_dialog(self):
        """Show list of resumes and load selected."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Open Resume")
        dialog.geometry("400x500")
        # ... listbox with resumes, on double-click load ...
        pass

    def export_pdf(self):
        """Generate PDF in a separate thread."""
        self._gather_form_data()
        if not self.current_resume.full_name:
            messagebox.showwarning("Missing Info", "Full name is required for PDF.")
            return
        filename = f"{self.current_resume.full_name.replace(' ', '_')}_resume.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=filename
        )
        if not file_path:
            return

        # Run in thread to keep UI responsive
        def generate():
            try:
                PDFGenerator.generate(
                    self.current_resume, file_path,
                    template_name="modern",  # could be user selected
                    accent_color_override=AppConfig.ACCENT_COLOR
                )
                self.root.after(0, lambda: messagebox.showinfo("Success", f"PDF saved to {file_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("PDF Error", str(e)))

        threading.Thread(target=generate, daemon=True).start()

    # ... many other methods: _gather_form_data, _refresh_ui_from_resume, etc.
'''
# Inside your ResumeApp.__init__ or _build_editor
def _build_settings_tab(self):
    """Add Appearance tab with template and alignment controls."""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="🎨 Appearance")
    
    # Template selection
    row = 0
    ttk.Label(tab, text="Template:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.template_var = tk.StringVar(value="modern")
    template_combo = ttk.Combobox(tab, textvariable=self.template_var,
                                  values=list(AppConfig.TEMPLATES.keys()), state="readonly", width=20)
    template_combo.grid(row=row, column=1, sticky='w', padx=10, pady=5)
    template_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())
    row += 1
    
    # Layout override
    ttk.Label(tab, text="Layout:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.layout_var = tk.StringVar(value="")
    layout_frame = ttk.Frame(tab)
    layout_frame.grid(row=row, column=1, sticky='w')
    ttk.Radiobutton(layout_frame, text="Default", variable=self.layout_var, 
                    value="").pack(side=tk.LEFT, padx=2)
    ttk.Radiobutton(layout_frame, text="Single Column", variable=self.layout_var,
                    value="single").pack(side=tk.LEFT, padx=2)
    ttk.Radiobutton(layout_frame, text="Two Column", variable=self.layout_var,
                    value="two_column").pack(side=tk.LEFT, padx=2)
    row += 1
    
    # Heading alignment
    ttk.Label(tab, text="Heading Align:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.heading_align_var = tk.StringVar(value="")
    heading_frame = ttk.Frame(tab)
    heading_frame.grid(row=row, column=1, sticky='w')
    ttk.Radiobutton(heading_frame, text="Default", variable=self.heading_align_var,
                    value="").pack(side=tk.LEFT, padx=2)
    for align in ["left", "center", "right"]:
        ttk.Radiobutton(heading_frame, text=align.title(), variable=self.heading_align_var,
                        value=align).pack(side=tk.LEFT, padx=2)
    row += 1
    
    # Body alignment
    ttk.Label(tab, text="Body Align:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.body_align_var = tk.StringVar(value="")
    body_frame = ttk.Frame(tab)
    body_frame.grid(row=row, column=1, sticky='w')
    ttk.Radiobutton(body_frame, text="Default", variable=self.body_align_var,
                    value="").pack(side=tk.LEFT, padx=2)
    for align in ["left", "center", "right", "justify"]:
        ttk.Radiobutton(body_frame, text=align.title(), variable=self.body_align_var,
                        value=align).pack(side=tk.LEFT, padx=2)
    row += 1
    
    # Accent color override
    ttk.Label(tab, text="Accent Color:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.accent_color_var = tk.StringVar(value="")
    ttk.Entry(tab, textvariable=self.accent_color_var, width=10).grid(row=row, column=1, sticky='w', padx=10)
    ttk.Button(tab, text="Pick", command=self._pick_accent_color).grid(row=row, column=2, padx=5)
    row += 1
    
    # Font override
    ttk.Label(tab, text="Font:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
    self.font_var = tk.StringVar(value="")
    font_combo = ttk.Combobox(tab, textvariable=self.font_var,
                              values=["", "Helvetica", "Times", "Courier", "Georgia"],
                              state="readonly", width=15)
    font_combo.grid(row=row, column=1, sticky='w', padx=10, pady=5)
    row += 1
    
    # Preview note
    ttk.Label(tab, text="Note: Settings apply to PDF export only.", 
              font=("Arial", 9, "italic")).grid(row=row, column=0, columnspan=3, pady=20)

def _pick_accent_color(self):
    from tkinter import colorchooser
    color = colorchooser.askcolor(initialcolor=self.accent_color_var.get() or "#2c3e50")[1]
    if color:
        self.accent_color_var.set(color)

def export_pdf(self):
    """Export current resume to PDF with selected template settings."""
    # Gather form data (your existing function)
    self._gather_form_data()
    
    if not self.current_resume.full_name:
        messagebox.showwarning("Missing Info", "Full name is required.")
        return
    
    # Get save path
    filename = f"{self.current_resume.full_name.replace(' ', '_')}_resume.pdf"
    file_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialfile=filename
    )
    if not file_path:
        return
    
    # Gather settings from Appearance tab
    template = self.template_var.get()
    layout = self.layout_var.get() or None  # empty string = no override
    heading_align = self.heading_align_var.get() or None
    body_align = self.body_align_var.get() or None
    accent_color = self.accent_color_var.get() or None
    font = self.font_var.get() or None
    
    # Run PDF generation in thread (to keep UI responsive)
    import threading
    def generate():
        try:
            from pdf_generator import PDFGenerator
            PDFGenerator.generate(
                self.current_resume,
                file_path,
                template_name=template,
                layout_override=layout,
                heading_align_override=heading_align,
                body_align_override=body_align,
                accent_color_override=accent_color,
                font_override=font
            )
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", f"PDF saved to:\n{file_path}"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror(
                "PDF Error", f"Failed to generate PDF:\n{str(e)}"))
            
            # In _build_personal_tab()
ttk.Label(tab, text="Profile Title:").grid(row=next_row, column=0, sticky='w', padx=5, pady=5)
self.entry_profile_title = ttk.Entry(tab, width=40)
self.entry_profile_title.grid(row=next_row, column=1, sticky='w', padx=5, pady=5)
def _build_achievements_tab(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="🏆 Achievements")
    
    # Treeview for achievements
    columns = ('title', 'subtitle', 'description')
    self.ach_tree = ttk.Treeview(tab, columns=columns, show='headings', height=6)
    self.ach_tree.heading('title', text='Title')
    self.ach_tree.heading('subtitle', text='Subtitle')
    self.ach_tree.heading('description', text='Description')
    self.ach_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    btn_frame = ttk.Frame(tab)
    btn_frame.pack(fill=tk.X, pady=5)
    ttk.Button(btn_frame, text="Add Achievement", command=self._add_achievement).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Edit", command=self._edit_achievement).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Remove", command=self._remove_achievement).pack(side=tk.LEFT, padx=2)
    
    self.achievements = []
    def _build_references_tab(self):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="👥 References")
    
    # Treeview
    columns = ('name', 'title', 'company', 'phone', 'email')
    self.ref_tree = ttk.Treeview(tab, columns=columns, show='headings', height=6)
    self.ref_tree.heading('name', text='Name')
    self.ref_tree.heading('title', text='Title')
    self.ref_tree.heading('company', text='Company')
    self.ref_tree.heading('phone', text='Phone')
    self.ref_tree.heading('email', text='Email')
    self.ref_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    btn_frame = ttk.Frame(tab)
    btn_frame.pack(fill=tk.X, pady=5)
    ttk.Button(btn_frame, text="Add Reference", command=self._add_reference).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Edit", command=self._edit_reference).pack(side=tk.LEFT, padx=2)
    ttk.Button(btn_frame, text="Remove", command=self._remove_reference).pack(side=tk.LEFT, padx=2)
    
    self.references = []
            
    
    threading.Thread(target=generate, daemon=True).start()
'''
    
