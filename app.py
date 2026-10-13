from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
import os
import re
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# -----------------------------
# Skills List
# -----------------------------

SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "javascript",
    "html",
    "css",
    "react",
    "angular",
    "node.js",
    "flask",
    "django",
    "sql",
    "mysql",
    "mongodb",
    "machine learning",
    "deep learning",
    "artificial intelligence",
    "data science",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "keras",
    "pytorch",
    "nlp",
    "tableau",
    "power bi",
    "git",
    "github",
    "docker",
    "aws",
    "azure",
    "linux",
    "excel"
]


# -----------------------------
# Database
# -----------------------------

def create_database():

    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            job_description TEXT,
            match_score REAL,
            matched_skills TEXT,
            missing_skills TEXT
        )
    """)

    conn.commit()
    conn.close()


create_database()


# -----------------------------
# Check File
# -----------------------------

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# -----------------------------
# Extract PDF Text
# -----------------------------

def extract_pdf_text(filepath):

    text = ""

    reader = PdfReader(filepath)

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "
"

    return text


# -----------------------------
# Extract DOCX Text
# -----------------------------

def extract_docx_text(filepath):

    document = Document(filepath)

    text = ""

    for paragraph in document.paragraphs:

        text += paragraph.text + "
"

    return text


# -----------------------------
# Extract Resume Text
# -----------------------------

def extract_resume_text(filepath):

    extension = filepath.rsplit(".", 1)[1].lower()

    if extension == "pdf":

        return extract_pdf_text(filepath)

    elif extension == "docx":

        return extract_docx_text(filepath)

    return ""


# -----------------------------
# Extract Skills
# -----------------------------

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        # Escape special characters
        pattern = r"" + re.escape(skill) + r""

        if re.search(pattern, text):

            found_skills.append(skill)

    return found_skills


# -----------------------------
# Calculate TF-IDF Similarity
# -----------------------------

def calculate_similarity(resume_text, job_description):

    documents = [
        resume_text.lower(),
        job_description.lower()
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(
        vectors[0:1],
        vectors[1:2]
    )[0][0]

    return similarity * 100


# -----------------------------
# Calculate Final Score
# -----------------------------

def calculate_final_score(
    resume_text,
    job_description,
    resume_skills,
    job_skills
):

    # TF-IDF score
    tfidf_score = calculate_similarity(
        resume_text,
        job_description
    )

    # Skill matching
    if len(job_skills) > 0:

        matched = set(resume_skills).intersection(
            set(job_skills)
        )

        skill_score = (
            len(matched) / len(job_skills)
        ) * 100

    else:

        skill_score = 0

    # Hybrid score
    final_score = (
        (skill_score * 0.7)
        + (tfidf_score * 0.3)
    )

    return round(final_score, 2)


# -----------------------------
# Home Page
# -----------------------------

@app.route("/")
def home():

    return render_template("index.html")


# -----------------------------
# Analyze Resume
# -----------------------------

@app.route("/analyze", methods=["POST"])
def analyze():

    if "resume" not in request.files:

        return "No resume uploaded."

    resume = request.files["resume"]

    job_description = request.form.get(
        "job_description",
        ""
    )

    if resume.filename == "":

        return "Please select a resume."

    if job_description.strip() == "":

        return "Please enter a job description."

    if not allowed_file(resume.filename):

        return "Only PDF and DOCX files are allowed."

    # Secure filename
    filename = secure_filename(
        resume.filename
    )

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume.save(filepath)

    # Extract text
    resume_text = extract_resume_text(
        filepath
    )

    if not resume_text.strip():

        return "Could not extract text from resume."

    # Extract skills
    resume_skills = extract_skills(
        resume_text
    )

    job_skills = extract_skills(
        job_description
    )

    # Matched skills
    matched_skills = list(
        set(resume_skills).intersection(
            set(job_skills)
        )
    )

    # Missing skills
    missing_skills = list(
        set(job_skills).difference(
            set(resume_skills)
        )
    )

    # Score
    final_score = calculate_final_score(
        resume_text,
        job_description,
        resume_skills,
        job_skills
    )

    # Recommendations
    recommendations = []

    for skill in missing_skills:

        recommendations.append(
            "Improve your knowledge of " + skill
        )

    if final_score >= 80:

        recommendation_message = (
            "Excellent match! Your resume "
            "closely matches the job requirements."
        )

    elif final_score >= 60:

        recommendation_message = (
            "Good match. Consider improving "
            "your missing skills."
        )

    else:

        recommendation_message = (
            "Your resume needs improvement "
            "to better match this job."
        )

    # Save result
    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analysis
        (
            filename,
            job_description,
            match_score,
            matched_skills,
            missing_skills
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        filename,
        job_description,
        final_score,
        ", ".join(matched_skills),
        ", ".join(missing_skills)
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        filename=filename,
        score=final_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        recommendation_message=recommendation_message,
        recommendations=recommendations
    )


# -----------------------------
# Run Application
# -----------------------------

if __name__ == "__main__":
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    site_url = "http://127.0.0.1:5000"

    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, site_url])

    app.run(debug=True, use_reloader=False)
