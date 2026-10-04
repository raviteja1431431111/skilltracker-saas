from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student') # 'student', 'mentor', 'admin'
    
    # SaaS User Management Extensions
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Inactive, Pending
    student_code = db.Column(db.String(50), nullable=True) # Student ID
    employee_code = db.Column(db.String(50), nullable=True) # Employee ID
    phone_number = db.Column(db.String(30), nullable=True)
    last_active_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    skills = db.relationship('StudentSkill', backref='user', cascade="all, delete-orphan")
    goals = db.relationship('Goal', backref='user', cascade="all, delete-orphan")
    courses = db.relationship('Course', backref='user', cascade="all, delete-orphan")
    projects = db.relationship('Project', backref='user', cascade="all, delete-orphan")
    certificates = db.relationship('Certificate', backref='user', cascade="all, delete-orphan")
    achievements = db.relationship('Achievement', backref='user', cascade="all, delete-orphan")
    assessment_results = db.relationship('AssessmentResult', backref='user', cascade="all, delete-orphan")
    feedbacks_received = db.relationship('MentorFeedback', foreign_keys='MentorFeedback.student_id', backref='student', cascade="all, delete-orphan")
    feedbacks_given = db.relationship('MentorFeedback', foreign_keys='MentorFeedback.mentor_id', backref='mentor')
    points = db.relationship('GamificationPoint', backref='user', cascade="all, delete-orphan")
    badges = db.relationship('Badge', backref='user', cascade="all, delete-orphan")
    
    tasks_assigned = db.relationship('MentorTask', foreign_keys='MentorTask.student_id', backref='student', cascade="all, delete-orphan")
    tasks_created = db.relationship('MentorTask', foreign_keys='MentorTask.mentor_id', backref='mentor')
    daily_activities = db.relationship('DailyActivity', backref='student', cascade="all, delete-orphan")
    activity_logs = db.relationship('ActivityLog', backref='student', cascade="all, delete-orphan")
    platform_connections = db.relationship('PlatformConnection', backref='student', cascade="all, delete-orphan")
    external_courses = db.relationship('ExternalCourse', backref='student', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan")
    audit_events = db.relationship('AuditLog', backref='actor', cascade="all, delete-orphan")

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    college = db.Column(db.String(150), default='National Institute of Technology')
    department = db.Column(db.String(100), default='Computer Science & Engineering')
    year = db.Column(db.String(50), default='3rd Year B.Tech')
    career_goal = db.Column(db.String(100), default='Full-Stack Software Engineer')
    bio = db.Column(db.Text, default='Passionate engineering student focused on building modern web applications and cloud services.')
    github_url = db.Column(db.String(200), default='https://github.com/studentdemo')
    linkedin_url = db.Column(db.String(200), default='https://linkedin.com/in/studentdemo')
    portfolio_url = db.Column(db.String(200), default='https://studentdemo.dev')

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50), default='Technical') # Technical, Programming, Data, Cloud, DevOps, AI / ML, Communication, Leadership, Professional, Other
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Active') # Active, Archived
    expected_proficiency = db.Column(db.String(50), default='Advanced') # Beginner, Intermediate, Advanced, Expert

class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    level = db.Column(db.String(50), default='Beginner') # Beginner, Intermediate, Advanced, Expert
    progress = db.Column(db.Integer, default=30) # 0 to 100%
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    skill = db.relationship('Skill')

class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    target_level = db.Column(db.String(50), default='Advanced')
    deadline = db.Column(db.String(50), nullable=False)
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='In Progress')

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    platform = db.Column(db.String(100), default='Coursera')
    instructor = db.Column(db.String(100), default='Dr. Andrew Ng')
    start_date = db.Column(db.String(50), default='2026-01-10')
    completion_date = db.Column(db.String(50), default='2026-03-15')
    duration = db.Column(db.String(50), default='30 Hours')
    skills_gained = db.Column(db.String(250), default='Python, Data Structures')
    status = db.Column(db.String(50), default='Completed')
    course_url = db.Column(db.String(250), default='https://coursera.org/learn/example')
    
    progress_percentage = db.Column(db.Integer, default=100)
    completed_items = db.Column(db.Integer, default=40)
    total_items = db.Column(db.Integer, default=40)
    is_synced = db.Column(db.Boolean, default=False)
    sync_source = db.Column(db.String(50), default='MANUAL')

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(250), default='Python, Flask, SQLite, HTML/CSS')
    skills_applied = db.Column(db.String(250), default='Web Development, Database Design')
    duration = db.Column(db.String(50), default='4 Weeks')
    status = db.Column(db.String(50), default='Completed')
    github_link = db.Column(db.String(250), default='https://github.com/studentdemo/project')
    demo_link = db.Column(db.String(250), default='https://project-demo.com')
    mentor_rating = db.Column(db.Float, default=4.5)
    mentor_feedback = db.Column(db.Text, default='Great implementation and clear database schema.')

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuing_organization = db.Column(db.String(150), default='Google / Coursera')
    issue_date = db.Column(db.String(50), default='2026-04-01')
    certificate_id = db.Column(db.String(100), default='CERT-998812')
    skill_category = db.Column(db.String(100), default='Web Development')
    verification_url = db.Column(db.String(250), default='https://coursera.org/verify/CERT-998812')

class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), default='Hackathon')
    date = db.Column(db.String(50), default='2026-05-12')
    description = db.Column(db.Text, default='Secured 1st place in Inter-College CodeHack 2026.')

class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    questions_json = db.Column(db.Text, nullable=False)

class AssessmentResult(db.Model):
    __tablename__ = 'assessment_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessments.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    level_assigned = db.Column(db.String(50), default='Advanced')
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessment = db.relationship('Assessment')

class MentorFeedback(db.Model):
    __tablename__ = 'mentor_feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Float, default=4.5)
    comments = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GamificationPoint(db.Model):
    __tablename__ = 'gamification_points'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    icon = db.Column(db.String(50), default='fa-medal')
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)

class MentorTask(db.Model):
    __tablename__ = 'mentor_tasks'
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.String(50), default='Assignment')
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    priority = db.Column(db.String(20), default='Medium')
    start_date = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.String(50), nullable=False)
    estimated_hours = db.Column(db.Float, default=2.0)
    resource_url = db.Column(db.String(250), nullable=True)
    submission_type = db.Column(db.String(50), default='GitHub Repository')
    status = db.Column(db.String(50), default='Assigned')
    progress = db.Column(db.Integer, default=0)
    mentor_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    skill = db.relationship('Skill')
    course = db.relationship('Course')
    submissions = db.relationship('TaskSubmission', backref='task', cascade="all, delete-orphan")

class TaskSubmission(db.Model):
    __tablename__ = 'task_submissions'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('mentor_tasks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_type = db.Column(db.String(50), default='GitHub Repository')
    submission_url = db.Column(db.String(250), nullable=True)
    github_url = db.Column(db.String(250), nullable=True)
    text_response = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentor_feedback = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Submitted')

class DailyActivity(db.Model):
    __tablename__ = 'daily_activities'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('mentor_tasks.id'), nullable=True)
    date = db.Column(db.String(20), nullable=False)
    time_spent_minutes = db.Column(db.Integer, default=60)
    progress_pct_start = db.Column(db.Integer, default=0)
    progress_pct_end = db.Column(db.Integer, default=50)
    activity_notes = db.Column(db.Text, nullable=False)
    remaining_notes = db.Column(db.Text, nullable=True)
    difficulty_level = db.Column(db.String(20), default='Medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship('MentorTask')

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PlatformConnection(db.Model):
    __tablename__ = 'platform_connections'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    external_user_id = db.Column(db.String(100), nullable=True)
    access_token_encrypted = db.Column(db.Text, nullable=True)
    refresh_token_encrypted = db.Column(db.Text, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    connected_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='DISCONNECTED')

    sync_logs = db.relationship('SyncLog', backref='connection', cascade="all, delete-orphan")

class ExternalCourse(db.Model):
    __tablename__ = 'external_courses'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    platform = db.Column(db.String(50), nullable=False)
    external_course_id = db.Column(db.String(100), nullable=False)
    content_progress = db.Column(db.Float, default=0.0)
    graded_progress = db.Column(db.Float, default=0.0)
    overall_progress = db.Column(db.Float, default=0.0)
    expected_progress = db.Column(db.Float, default=0.0)
    final_grade = db.Column(db.Float, nullable=True)
    sync_status = db.Column(db.String(50), default='OK')
    sync_source = db.Column(db.String(50), default='OAUTH_API')
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship('Course')

class SyncLog(db.Model):
    __tablename__ = 'sync_logs'
    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(db.Integer, db.ForeignKey('platform_connections.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='SUCCESS')
    message = db.Column(db.Text, nullable=False)
    items_checked = db.Column(db.Integer, default=0)
    items_completed = db.Column(db.Integer, default=0)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    link = db.Column(db.String(200), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =========================================================================
# SAAS ADMINISTRATION & AUDIT MODELS
# =========================================================================

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(150), nullable=False) # e.g. "Created Student Account", "Deactivated User"
    target_resource = db.Column(db.String(200), nullable=False) # e.g. "Rahul Sharma (student@college.edu)"
    result = db.Column(db.String(50), default='SUCCESS') # SUCCESS, FAILURE
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
