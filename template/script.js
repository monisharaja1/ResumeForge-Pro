// =============== STATE ================
let resumeData = {
    fullName: "",
    email: "",
    phone: "",
    address: "",
    summary: "",
    experiences: [],
    educations: [],
    skills: []
};
const API_BASE = 'http://localhost:5000/api';
let savedResumes = JSON.parse(localStorage.getItem("resumeBuilderSaves")) || {};

// =============== DOM ELEMENTS ================
const fullNameInput = document.getElementById("fullName");
const emailInput = document.getElementById("email");
const phoneInput = document.getElementById("phone");
const summaryInput = document.getElementById("summary");
const addressInput = document.getElementById("address");

const expContainer = document.getElementById("experienceContainer");
const eduContainer = document.getElementById("educationContainer");
const skillsContainer = document.getElementById("skillsContainer");

const resumeSelect = document.getElementById("resumeSelect");
const newBtn = document.getElementById("newBtn");
const saveBtn = document.getElementById("saveBtn");
const deleteBtn = document.getElementById("deleteBtn");
const pdfBtn = document.getElementById("pdfBtn");

// =============== INITIALISE ================
function init() {
    // Load default or last used resume
    const lastId = localStorage.getItem("lastResumeId");
    if (lastId && savedResumes[lastId]) {
        loadResumeById(lastId);
    } else {
        // Start fresh
        updatePreview();
    }
    populateResumeDropdown();
    attachEventListeners();
}

// =============== EVENT LISTENERS ================
function attachEventListeners() {
    // Personal fields – update preview on input
    [fullNameInput, emailInput, phoneInput, addressInput, summaryInput].forEach(input => {
        input.addEventListener("input", () => {
            resumeData.fullName = fullNameInput.value;
            resumeData.email = emailInput.value;
            resumeData.phone = phoneInput.value;
            resumeData.address = addressInput.value;
            resumeData.summary = summaryInput.value;
            updatePreview();
        });
    });

    // Add buttons
    document.getElementById("addExpBtn").addEventListener("click", () => addExperience());
    document.getElementById("addEduBtn").addEventListener("click", () => addEducation());
    document.getElementById("addSkillBtn").addEventListener("click", addSkillPrompt);

    // Global controls
    newBtn.addEventListener("click", newResume);
    saveBtn.addEventListener("click", saveResume);
    deleteBtn.addEventListener("click", deleteResume);
    pdfBtn.addEventListener("click", exportPDF);
    resumeSelect.addEventListener("change", (e) => {
        if (e.target.value) loadResumeById(e.target.value);
    });
}

// =============== EXPERIENCE ================
function addExperience(exp = { jobTitle: "", company: "", startDate: "", endDate: "", description: "" }) {
    resumeData.experiences.push(exp);
    renderExperiences();
    updatePreview();
}

function renderExperiences() {
    expContainer.innerHTML = "";
    resumeData.experiences.forEach((exp, index) => {
        const card = document.createElement("div");
        card.className = "entry-card";
        card.innerHTML = `
            <button class="remove-btn" onclick="removeExperience(${index})">✕</button>
            <div class="entry-grid">
                <input type="text" placeholder="Job Title" value="${escapeHtml(exp.jobTitle || '')}" oninput="updateExperience(${index}, 'jobTitle', this.value)">
                <input type="text" placeholder="Company" value="${escapeHtml(exp.company || '')}" oninput="updateExperience(${index}, 'company', this.value)">
                <input type="text" placeholder="Start Date" value="${escapeHtml(exp.startDate || '')}" oninput="updateExperience(${index}, 'startDate', this.value)">
                <input type="text" placeholder="End Date" value="${escapeHtml(exp.endDate || '')}" oninput="updateExperience(${index}, 'endDate', this.value)">
                <textarea placeholder="Description" rows="3" class="full-width" oninput="updateExperience(${index}, 'description', this.value)">${escapeHtml(exp.description || '')}</textarea>
            </div>
        `;
        expContainer.appendChild(card);
    });
}

window.updateExperience = function(index, field, value) {
    resumeData.experiences[index][field] = value;
    updatePreview();
};

window.removeExperience = function(index) {
    resumeData.experiences.splice(index, 1);
    renderExperiences();
    updatePreview();
};

// =============== EDUCATION ================
function addEducation(edu = { degree: "", institution: "", startDate: "", endDate: "", description: "" }) {
    resumeData.educations.push(edu);
    renderEducations();
    updatePreview();
}

function renderEducations() {
    eduContainer.innerHTML = "";
    resumeData.educations.forEach((edu, index) => {
        const card = document.createElement("div");
        card.className = "entry-card";
        card.innerHTML = `
            <button class="remove-btn" onclick="removeEducation(${index})">✕</button>
            <div class="entry-grid">
                <input type="text" placeholder="Degree" value="${escapeHtml(edu.degree || '')}" oninput="updateEducation(${index}, 'degree', this.value)">
                <input type="text" placeholder="Institution" value="${escapeHtml(edu.institution || '')}" oninput="updateEducation(${index}, 'institution', this.value)">
                <input type="text" placeholder="Start Date" value="${escapeHtml(edu.startDate || '')}" oninput="updateEducation(${index}, 'startDate', this.value)">
                <input type="text" placeholder="End Date" value="${escapeHtml(edu.endDate || '')}" oninput="updateEducation(${index}, 'endDate', this.value)">
                <textarea placeholder="Description" rows="3" class="full-width" oninput="updateEducation(${index}, 'description', this.value)">${escapeHtml(edu.description || '')}</textarea>
            </div>
        `;
        eduContainer.appendChild(card);
    });
}

window.updateEducation = function(index, field, value) {
    resumeData.educations[index][field] = value;
    updatePreview();
};

window.removeEducation = function(index) {
    resumeData.educations.splice(index, 1);
    renderEducations();
    updatePreview();
};

// =============== SKILLS ================
function addSkillPrompt() {
    const skill = prompt("Enter a skill:");
    if (skill && skill.trim()) {
        resumeData.skills.push(skill.trim());
        renderSkills();
        updatePreview();
    }
}

function renderSkills() {
    skillsContainer.innerHTML = "";
    const inputGroup = document.createElement("div");
    inputGroup.innerHTML = `
        <input type="text" id="newSkillInput" placeholder="Add a skill and press Enter">
        <button class="add-btn" onclick="addSkillFromInput()">Add</button>
    `;
    skillsContainer.appendChild(inputGroup);

    const skillsDiv = document.createElement("div");
    skillsDiv.style.marginTop = "15px";
    resumeData.skills.forEach((skill, index) => {
        const chip = document.createElement("span");
        chip.className = "skill-chip";
        chip.innerHTML = `${escapeHtml(skill)} <button onclick="removeSkill(${index})">✕</button>`;
        skillsDiv.appendChild(chip);
    });
    skillsContainer.appendChild(skillsDiv);

    // Enter key support
    document.getElementById("newSkillInput")?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") addSkillFromInput();
    });
}

window.addSkillFromInput = function() {
    const input = document.getElementById("newSkillInput");
    if (input.value.trim()) {
        resumeData.skills.push(input.value.trim());
        input.value = "";
        renderSkills();
        updatePreview();
    }
};

window.removeSkill = function(index) {
    resumeData.skills.splice(index, 1);
    renderSkills();
    updatePreview();
};

// =============== PREVIEW ================
function updatePreview() {
    // Sync personal data from inputs
    resumeData.fullName = fullNameInput.value;
    resumeData.email = emailInput.value;
    resumeData.phone = phoneInput.value;
    resumeData.address = addressInput.value;
    resumeData.summary = summaryInput.value;

    const preview = document.getElementById("resumePreview");
    let html = "";

    // Name
    html += `<div class="preview-name">${escapeHtml(resumeData.fullName) || "Your Name"}</div>`;

    // Contact
    let contact = [];
    if (resumeData.email) contact.push(resumeData.email);
    if (resumeData.phone) contact.push(resumeData.phone);
    if (resumeData.address) contact.push(resumeData.address);
    html += `<div class="preview-contact">${escapeHtml(contact.join(" | ")) || " "}</div>`;

    // Summary
    if (resumeData.summary) {
        html += `<div class="preview-section"><h3>Summary</h3><p>${escapeHtml(resumeData.summary).replace(/\n/g, "<br>")}</p></div>`;
    }

    // Experience
    if (resumeData.experiences.length > 0) {
        html += `<div class="preview-section"><h3>Work Experience</h3>`;
        resumeData.experiences.forEach(exp => {
            html += `<div class="preview-item">
                <div class="preview-item-title">${escapeHtml(exp.jobTitle)}</div>
                <div class="preview-item-sub">${escapeHtml(exp.company)}</div>
                <div class="preview-item-date">${escapeHtml(exp.startDate)} – ${escapeHtml(exp.endDate)}</div>
                <div class="preview-item-desc">${escapeHtml(exp.description || '').replace(/\n/g, "<br>")}</div>
            </div>`;
        });
        html += `</div>`;
    }

    // Education
    if (resumeData.educations.length > 0) {
        html += `<div class="preview-section"><h3>Education</h3>`;
        resumeData.educations.forEach(edu => {
            html += `<div class="preview-item">
                <div class="preview-item-title">${escapeHtml(edu.degree)}</div>
                <div class="preview-item-sub">${escapeHtml(edu.institution)}</div>
                <div class="preview-item-date">${escapeHtml(edu.startDate)} – ${escapeHtml(edu.endDate)}</div>
                <div class="preview-item-desc">${escapeHtml(edu.description || '').replace(/\n/g, "<br>")}</div>
            </div>`;
        });
        html += `</div>`;
    }

    // Skills
    if (resumeData.skills.length > 0) {
        html += `<div class="preview-section"><h3>Skills</h3><div class="preview-skills">`;
        resumeData.skills.forEach(skill => {
            html += `<span class="preview-skill">${escapeHtml(skill)}</span>`;
        });
        html += `</div></div>`;
    }

    preview.innerHTML = html;
}

// =============== SAVE / LOAD / DELETE ================
function saveResume() {
    const name = prompt("Save this resume as:", resumeData.fullName || "Untitled");
    if (!name) return;

    const id = "resume_" + Date.now();
    savedResumes[id] = {
        name: name,
        data: JSON.parse(JSON.stringify(resumeData)), // clone
        lastModified: new Date().toISOString()
    };
    localStorage.setItem("resumeBuilderSaves", JSON.stringify(savedResumes));
    localStorage.setItem("lastResumeId", id);
    populateResumeDropdown();
    alert("Resume saved!");
}

function loadResumeById(id) {
    const saved = savedResumes[id];
    if (!saved) return;
    resumeData = JSON.parse(JSON.stringify(saved.data)); // clone

    // Populate form fields
    fullNameInput.value = resumeData.fullName || "";
    emailInput.value = resumeData.email || "";
    phoneInput.value = resumeData.phone || "";
    summaryInput.value = resumeData.summary || "";

    // Re-render dynamic sections
    renderExperiences();
    renderEducations();
    renderSkills();
    updatePreview();
    localStorage.setItem("lastResumeId", id);
}

function deleteResume() {
    const selectedId = resumeSelect.value;
    if (!selectedId || !savedResumes[selectedId]) {
        alert("Select a resume to delete.");
        return;
    }
    if (confirm(`Delete "${savedResumes[selectedId].name}"?`)) {
        delete savedResumes[selectedId];
        localStorage.setItem("resumeBuilderSaves", JSON.stringify(savedResumes));
        if (localStorage.getItem("lastResumeId") === selectedId) {
            localStorage.removeItem("lastResumeId");
        }
        populateResumeDropdown();
        if (Object.keys(savedResumes).length === 0) {
            newResume();
        }
    }
}

function newResume() {
    // Reset state
    resumeData = {
        fullName: "", email: "", phone: "", address: "", summary: "",
        experiences: [], educations: [], skills: []
    };
    fullNameInput.value = "";
    emailInput.value = "";
    phoneInput.value = "";
    const addressInput = document.getElementById("address");
    if (addressInput) addressInput.value = "";
    summaryInput.value = "";
    renderExperiences();
    renderEducations();
    renderSkills();
    updatePreview();
    localStorage.removeItem("lastResumeId");
    // Clear dropdown selection
    resumeSelect.value = "";
}

function populateResumeDropdown() {
    resumeSelect.innerHTML = '<option value="">-- Load Saved Resume --</option>';
    Object.keys(savedResumes).forEach(id => {
        const opt = document.createElement("option");
        opt.value = id;
        opt.textContent = `${savedResumes[id].name} (${new Date(savedResumes[id].lastModified).toLocaleDateString()})`;
        resumeSelect.appendChild(opt);
    });
}

// Build payload for API (convert to backend field names)
function gatherFormData() {
    return {
        full_name: resumeData.fullName || "",
        email: resumeData.email || "",
        phone: resumeData.phone || "",
        address: resumeData.address || "",
        summary: resumeData.summary || "",
        experiences: (resumeData.experiences || []).map(e => ({
            job_title: e.jobTitle || "",
            company: e.company || "",
            start_date: e.startDate || "",
            end_date: e.endDate || "",
            description: e.description || ""
        })),
        educations: (resumeData.educations || []).map(e => ({
            degree: e.degree || "",
            institution: e.institution || "",
            start_date: e.startDate || "",
            end_date: e.endDate || "",
            description: e.description || ""
        })),
        skills: resumeData.skills || []
    };
}

// =============== UTILITIES ================
function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
async function loadResumeList() {
    const response = await fetch(`${API_BASE}/resumes`);
    const resumes = await response.json();
    const select = document.getElementById('loadResumeSelect');
    select.innerHTML = '<option value="">-- Load Resume --</option>';
    resumes.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = `${r.title} (${new Date(r.updated).toLocaleDateString()})`;
        select.appendChild(opt);
    });
}
async function saveResume() {
    const resumeData = gatherFormData();
    const response = await fetch(`${API_BASE}/resumes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resumeData)
    });
    const result = await response.json();
    alert(`Saved! ID: ${result.id}`);
    loadResumeList(); // Refresh dropdown
}
async function exportPDF() {
    const resumeData = gatherFormData();
    const response = await fetch(`${API_BASE}/export-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(resumeData)
    });
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${resumeData.fullName || 'resume'}_resume.pdf`;
    a.click();
}
async function uploadProfilePic(file) {
    const reader = new FileReader();
    reader.onload = async (e) => {
        const base64 = e.target.result;
        const response = await fetch(`${API_BASE}/upload-profile-pic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64 })
        });
        const data = await response.json();
        // Store base64 in your resumeData object
        resumeData.profilePic = data.image;
    };
    reader.readAsDataURL(file);
}
// =============== START ================
init();
