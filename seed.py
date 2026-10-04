import json
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash
from app import app
from models import (
    db, User, StudentProfile, Skill, StudentSkill, Goal, Course, Project,
    Certificate, Achievement, Assessment, AssessmentResult, MentorFeedback,
    GamificationPoint, Badge, MentorTask, TaskSubmission, DailyActivity,
    ActivityLog, PlatformConnection, ExternalCourse, SyncLog, Notification,
    AuditLog, SystemSettings
)

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        print("Creating Skills Catalog...")
        skills_data = [
            ("Python", "Programming", "Core programming language for backend, AI, and script automation.", "Active", "Advanced"),
            ("JavaScript", "Programming", "Frontend dynamic interactions and web application logic.", "Active", "Advanced"),
            ("HTML & CSS", "Technical", "Web markup and UI layout styling.", "Active", "Advanced"),
            ("SQL & Relational Databases", "Data", "Database design, indexing, and SQL query optimization.", "Active", "Advanced"),
            ("Flask Framework", "Programming", "Lightweight Python micro-framework for REST APIs and web apps.", "Active", "Intermediate"),
            ("Git & GitHub", "DevOps", "Version control, branching strategies, and collaboration.", "Active", "Advanced"),
            ("Data Structures & Algorithms", "Technical", "Problem-solving techniques, Big-O complexity, and data organization.", "Active", "Advanced"),
            ("Cybersecurity Fundamentals", "Technical", "Network security, authentication, encryption, and vulnerability assessment.", "Active", "Intermediate"),
            ("Communication", "Communication", "Effective verbal and written technical communication.", "Active", "Advanced"),
            ("Problem Solving", "Professional", "Analytical thinking, debugging, and systematic resolution.", "Active", "Advanced"),
            ("Teamwork & Leadership", "Leadership", "Collaborative project delivery and team leadership.", "Active", "Intermediate"),
            ("Time Management", "Professional", "Prioritization, deadline management, and sprint planning.", "Active", "Intermediate")
        ]

        skill_objs = {}
        for name, category, desc, status, exp_prof in skills_data:
            skill = Skill(name=name, category=category, description=desc, status=status, expected_proficiency=exp_prof)
            db.session.add(skill)
            skill_objs[name] = skill
        db.session.commit()

        print("Creating Users...")
        hashed_pw = generate_password_hash("password123")

        # 1. Student User 1 (Rahul Sharma - Active Student)
        student_user = User(
            name="Rahul Sharma",
            email="student@college.edu",
            password_hash=hashed_pw,
            role="student",
            is_active=True,
            status="Active",
            student_code="STU-2026-0891"
        )
        db.session.add(student_user)

        # 2. Student User 2 (Priya Kumar - At Risk Demo Student)
        student_user2 = User(
            name="Priya Kumar",
            email="priya@college.edu",
            password_hash=hashed_pw,
            role="student",
            is_active=True,
            status="Active",
            student_code="STU-2026-0412"
        )
        db.session.add(student_user2)

        # 3. Mentor User
        mentor_user = User(
            name="Prof. Ananya Roy",
            email="mentor@college.edu",
            password_hash=hashed_pw,
            role="mentor",
            is_active=True,
            status="Active",
            employee_code="EMP-MNT-1092"
        )
        db.session.add(mentor_user)

        # 4. Admin User
        admin_user = User(
            name="Dr. Vikram Malhotra",
            email="admin@college.edu",
            password_hash=hashed_pw,
            role="admin",
            is_active=True,
            status="Active",
            employee_code="EMP-ADM-0001"
        )
        db.session.add(admin_user)
        db.session.commit()

        # Profiles
        p1 = StudentProfile(
            user_id=student_user.id,
            college="National Institute of Technology",
            department="Computer Science & Engineering",
            year="3rd Year B.Tech",
            career_goal="Full-Stack Software Engineer",
            bio="Motivated 3rd year CSE undergraduate passionate about Python, Web Architecture, Data Structures, and Cloud-native applications.",
            github_url="https://github.com/rahulsharma-dev",
            linkedin_url="https://linkedin.com/in/rahulsharma-dev",
            portfolio_url="https://rahulsharma.dev"
        )
        p2 = StudentProfile(
            user_id=student_user2.id,
            college="National Institute of Technology",
            department="Information Technology",
            year="2nd Year B.Tech",
            career_goal="Cybersecurity Specialist",
            bio="Interest in cryptography and network security analysis.",
            github_url="https://github.com/priyakumar",
            linkedin_url="https://linkedin.com/in/priyakumar",
            portfolio_url="https://priyakumar.dev"
        )
        db.session.add(p1)
        db.session.add(p2)

        # Student Skills
        student_skills_data = [
            ("Python", "Advanced", 80),
            ("JavaScript", "Intermediate", 65),
            ("HTML & CSS", "Advanced", 85),
            ("SQL & Relational Databases", "Intermediate", 70),
            ("Flask Framework", "Intermediate", 60),
            ("Git & GitHub", "Advanced", 75),
            ("Data Structures & Algorithms", "Intermediate", 65),
            ("Cybersecurity Fundamentals", "Beginner", 40),
            ("Communication", "Advanced", 85),
            ("Problem Solving", "Intermediate", 75)
        ]
        for name, level, prog in student_skills_data:
            if name in skill_objs:
                ss = StudentSkill(user_id=student_user.id, skill_id=skill_objs[name].id, level=level, progress=prog)
                db.session.add(ss)

        # Learning Goals
        goals = [
            Goal(user_id=student_user.id, title="Master Python & Advanced Flask Backend", target_level="Advanced", deadline="2026-11-30", progress=75, status="In Progress"),
            Goal(user_id=student_user.id, title="Complete Data Structures & Algorithms Practice", target_level="Advanced", deadline="2026-12-15", progress=60, status="In Progress"),
            Goal(user_id=student_user.id, title="Build Full-Stack Portfolio Project", target_level="Expert", deadline="2026-10-10", progress=100, status="Completed")
        ]
        for g in goals:
            db.session.add(g)

        # Courses
        courses = [
            Course(user_id=student_user.id, name="Python for Everybody Specialization", platform="Coursera", instructor="Dr. Charles Severance", start_date="2026-01-15", completion_date="2026-03-01", duration="40 Hours", skills_gained="Python, Data Structures, OOP", status="Completed", progress_percentage=100, is_synced=True, sync_source="COURSERA", course_url="https://coursera.org/learn/python"),
            Course(user_id=student_user.id, name="Full Stack Web Development with Flask & SQLite", platform="Udemy", instructor="Maximilian Schwarzmüller", start_date="2026-03-10", completion_date="2026-04-25", duration="35 Hours", skills_gained="Flask, SQLite, REST API, HTML/CSS", status="Completed", progress_percentage=100, is_synced=False, sync_source="MANUAL", course_url="https://udemy.com/course/flask-masterclass"),
            Course(user_id=student_user.id, name="Modern JavaScript Essentials", platform="edX", instructor="W3C Experts", start_date="2026-05-01", completion_date="2026-06-10", duration="25 Hours", skills_gained="JavaScript ES6+, Async/Await, Fetch API", status="Completed", progress_percentage=100, is_synced=False, sync_source="MANUAL", course_url="https://edx.org/course/js-essentials"),
            Course(user_id=student_user.id, name="Cybersecurity Foundations & Best Practices", platform="Coursera", instructor="Prof. Sourav Mukhopadhyay", start_date="2026-07-01", completion_date="2026-11-15", duration="30 Hours", skills_gained="Network Security, Cryptography", status="In Progress", progress_percentage=45, is_synced=True, sync_source="COURSERA", course_url="https://coursera.org/learn/cybersecurity")
        ]
        for c in courses:
            db.session.add(c)

        # Projects
        projects = [
            Project(
                user_id=student_user.id,
                name="Skill Development Tracking Platform",
                description="Web application designed to help college students track their technical and professional skill growth, document projects, earn badges, and receive mentor feedback.",
                technologies="Python, Flask, SQLite, HTML5, CSS3, JavaScript, Chart.js",
                skills_applied="Full-Stack Web Dev, Relational Schema Design, Gamification Logic",
                duration="4 Weeks",
                status="Completed",
                github_link="https://github.com/rahulsharma-dev/skill-tracker",
                demo_link="http://127.0.0.1:5000",
                mentor_rating=4.8,
                mentor_feedback="Excellent architecture and well-thought-out role separation."
            ),
            Project(
                user_id=student_user.id,
                name="Smart Campus Event Reservation System",
                description="A portal for managing campus auditorium bookings, student registrations, and automated PDF pass generation.",
                technologies="Python, Django, PostgreSQL, Bootstrap 5",
                skills_applied="Backend APIs, Database Management, User Auth",
                duration="3 Weeks",
                status="Completed",
                github_link="https://github.com/rahulsharma-dev/campus-events",
                demo_link="https://campusevents-demo.dev",
                mentor_rating=4.5,
                mentor_feedback="Very good user flow and clean backend code."
            )
        ]
        for p in projects:
            db.session.add(p)

        # Certificates
        certs = [
            Certificate(user_id=student_user.id, name="Python for Everybody Certificate", issuing_organization="Coursera / Univ. of Michigan", issue_date="2026-03-02", certificate_id="CERT-PY-8890", skill_category="Python Programming", verification_url="https://coursera.org/verify/CERT-PY-8890"),
            Certificate(user_id=student_user.id, name="Flask Web Development Developer Certification", issuing_organization="Udemy Academy", issue_date="2026-04-26", certificate_id="UC-77123-FLASK", skill_category="Web Development", verification_url="https://udemy.com/certificate/UC-77123-FLASK"),
            Certificate(user_id=student_user.id, name="Modern JavaScript Professional Certificate", issuing_organization="edX / W3Cx", issue_date="2026-06-12", certificate_id="EDX-JS-90021", skill_category="Frontend Development", verification_url="https://edx.org/credentials/EDX-JS-90021")
        ]
        for ct in certs:
            db.session.add(ct)

        # Achievements
        achievements = [
            Achievement(user_id=student_user.id, title="1st Place - Inter-College Hackathon 2026", category="Hackathon", date="2026-04-15", description="Led a team of 4 to build an automated AI study schedule generator."),
            Achievement(user_id=student_user.id, title="Finalist - National CodeMasters Championship", category="Coding Contest", date="2026-05-20", description="Ranked top 50 out of 3,500 participants across India.")
        ]
        for ach in achievements:
            db.session.add(ach)

        # Assessments & Results
        q_python = [
            {"q": "What is the output of print(type([]))?", "opts": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'array'>"], "ans": 0},
            {"q": "Which decorator in Flask binds a function to a URL route?", "opts": ["@app.path()", "@app.route()", "@app.bind()", "@app.url()"], "ans": 1},
            {"q": "What does SQLAlchemy primary_key=True enforce?", "opts": ["Unique non-null identifier", "Allows duplicate values", "Auto-deletes record", "Requires string format"], "ans": 0},
            {"q": "How do you define a dictionary comprehension in Python?", "opts": ["{k: v for k, v in items}", "[k: v for k, v in items]", "(k: v for k, v in items)", "<k: v for k, v in items>"], "ans": 0},
            {"q": "What HTTP status code represents a successful resource creation?", "opts": ["200 OK", "201 Created", "404 Not Found", "500 Internal Error"], "ans": 1}
        ]

        q_webdev = [
            {"q": "Which HTML tag is used to embed client-side JavaScript code?", "opts": ["<script>", "<js>", "<javascript>", "<code_script>"], "ans": 0},
            {"q": "In CSS flexbox, which property aligns items along the cross axis?", "opts": ["justify-content", "align-items", "flex-direction", "grid-gap"], "ans": 1},
            {"q": "What method fetches asynchronous network data in modern JS?", "opts": ["http.get()", "fetch()", "request()", "curl()"], "ans": 1},
            {"q": "What is the purpose of HTTP POST method?", "opts": ["Retrieve data", "Submit data to create/update resource", "Delete server files", "Test connection"], "ans": 1},
            {"q": "What CSS unit is relative to the root element font size?", "opts": ["em", "rem", "px", "vh"], "ans": 1}
        ]

        ass1 = Assessment(title="Python & Backend Development Assessment", topic="Python & Flask", questions_json=json.dumps(q_python))
        ass2 = Assessment(title="Full-Stack Web Fundamentals Quiz", topic="HTML, CSS & JS", questions_json=json.dumps(q_webdev))
        db.session.add(ass1)
        db.session.add(ass2)
        db.session.commit()

        res1 = AssessmentResult(user_id=student_user.id, assessment_id=ass1.id, score=5, max_score=5, percentage=100.0, level_assigned="Advanced")
        res2 = AssessmentResult(user_id=student_user.id, assessment_id=ass2.id, score=4, max_score=5, percentage=80.0, level_assigned="Intermediate")
        db.session.add(res1)
        db.session.add(res2)

        # Mentor Feedback
        fb1 = MentorFeedback(
            student_id=student_user.id,
            mentor_id=mentor_user.id,
            rating=4.8,
            comments="Rahul exhibits strong technical capability in Python and web development. Code quality is modular and clear.",
            recommendations="Focus next on containerization (Docker) and Cloud deployment (AWS/GCP) to level up full-stack profile."
        )
        db.session.add(fb1)

        # Mentor Tasks & Submissions
        today_str = date.today().strftime('%Y-%m-%d')
        yesterday_str = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        due_next_week = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
        overdue_date = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')

        t1 = MentorTask(
            mentor_id=mentor_user.id,
            student_id=student_user.id,
            title="Implement User Authentication REST API",
            description="Create secure session-based authentication endpoints with password hashing.",
            task_type="Coding Practice",
            skill_id=skill_objs["Flask Framework"].id,
            course_id=courses[1].id,
            priority="High",
            start_date=yesterday_str,
            due_date=today_str,
            estimated_hours=3.5,
            resource_url="https://flask.palletsprojects.com",
            submission_type="GitHub Repository",
            status="In Progress",
            progress=65,
            mentor_notes="Ensure clean error responses for 401 Unauthorized."
        )
        t2 = MentorTask(
            mentor_id=mentor_user.id,
            student_id=student_user.id,
            title="Complete Data Structures Binary Search Module",
            description="Solve 10 binary search problems and document time complexity analysis.",
            task_type="Assignment",
            skill_id=skill_objs["Data Structures & Algorithms"].id,
            course_id=courses[0].id,
            priority="Medium",
            start_date=today_str,
            due_date=due_next_week,
            estimated_hours=4.0,
            submission_type="Text",
            status="Assigned",
            progress=0
        )
        t_priya = MentorTask(
            mentor_id=mentor_user.id,
            student_id=student_user2.id,
            title="Submit Cryptography Lab Assignment 2",
            description="Implement RSA key generation and encryption demonstration.",
            task_type="Assignment",
            skill_id=skill_objs["Cybersecurity Fundamentals"].id,
            priority="High",
            start_date="2026-09-20",
            due_date=overdue_date,
            estimated_hours=4.0,
            submission_type="File",
            status="Overdue",
            progress=20
        )

        db.session.add(t1)
        db.session.add(t2)
        db.session.add(t_priya)

        # Audit Logs Initialization
        al1 = AuditLog(actor_id=admin_user.id, action="Created Student Account", target_resource=f"{student_user.name} ({student_user.email})", result="SUCCESS")
        al2 = AuditLog(actor_id=admin_user.id, action="Created Mentor Account", target_resource=f"{mentor_user.name} ({mentor_user.email})", result="SUCCESS")
        al3 = AuditLog(actor_id=admin_user.id, action="Created Platform Skill", target_resource="Python (Programming)", result="SUCCESS")
        db.session.add(al1)
        db.session.add(al2)
        db.session.add(al3)

        # Platform Connection
        conn = PlatformConnection(
            student_id=student_user.id,
            platform="Coursera",
            external_user_id="coursera_usr_88123",
            access_token_encrypted="encrypted_token_sample",
            status="CONNECTED",
            connected_at=datetime.utcnow() - timedelta(days=15),
            last_synced_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add(conn)

        db.session.commit()
        print("Database re-seeded successfully with SkillTracker SaaS dataset!")

if __name__ == '__main__':
    seed_database()
