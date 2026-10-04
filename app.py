import os
import json
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, make_response
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

from config import config
from models import (
    db, User, StudentProfile, Skill, StudentSkill, Goal, Course, Project,
    Certificate, Achievement, Assessment, AssessmentResult, MentorFeedback,
    GamificationPoint, Badge, MentorTask, TaskSubmission, DailyActivity,
    ActivityLog, PlatformConnection, ExternalCourse, SyncLog, Notification,
    AuditLog, SystemSettings
)

from services.scoring_service import SkillScoreService
from services.task_service import TaskService
from services.progress_service import ProgressService
from services.notification_service import NotificationService
from services.integration_service import IntegrationService
from services.audit_service import AuditService
from services.user_service import UserService
from services.report_service import ReportService

migrate = Migrate()

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app_instance = Flask(__name__)
    app_instance.config.from_object(config.get(config_name, config['default']))

    db.init_app(app_instance)
    migrate.init_app(app_instance, db)

    # Health Check Endpoint
    @app_instance.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'skilltracker'
        }), 200

    # Custom Error Handlers
    @app_instance.errorhandler(400)
    def bad_request_error(error):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Bad Request', 'message': str(error)}), 400
        flash('Invalid request submitted.', 'warning')
        return redirect(url_for('dashboard'))

    @app_instance.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
        flash('Unauthorized access for your account role.', 'danger')
        return redirect(url_for('dashboard'))

    @app_instance.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404
        flash('The requested page does not exist.', 'warning')
        return redirect(url_for('dashboard'))

    @app_instance.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/') or request.is_json:
            return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected server error occurred.'}), 500
        flash('An unexpected server error occurred. Please try again.', 'danger')
        return redirect(url_for('dashboard'))

    return app_instance

app = create_app()

# Helper Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash('Unauthorized access for your account role.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Context Processor for Templates
@app.context_processor
def inject_user():
    current_user = None
    unread_notifications_count = 0
    if 'user_id' in session:
        current_user = db.session.get(User, session['user_id'])

        if current_user:
            unread_notifications_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return dict(current_user=current_user, unread_notifications_count=unread_notifications_count)

# Score Engine Delegate
def calculate_student_score(user_id):
    return {
        'overall': SkillScoreService.calculate_overall_score(user_id),
        'courses': SkillScoreService.calculate_course_score(user_id),
        'projects': SkillScoreService.calculate_project_score(user_id),
        'assessments': SkillScoreService.calculate_assessment_score(user_id),
        'certs': SkillScoreService.calculate_certificate_score(user_id),
        'mentor': SkillScoreService.calculate_mentor_score(user_id)
    }

# Gamification Helper
def award_points(user_id, pts, reason):
    point = GamificationPoint(user_id=user_id, points=pts, reason=reason)
    db.session.add(point)

    user = db.session.get(User, user_id)
    if user:
        badge_names = [b.badge_name for b in user.badges]
        if len(user.courses) >= 3 and "Fast Learner" not in badge_names:
            db.session.add(Badge(user_id=user_id, badge_name="Fast Learner", description="Completed 3+ learning courses", icon="fa-bolt"))
        if len(user.projects) >= 3 and "Project Builder" not in badge_names:
            db.session.add(Badge(user_id=user_id, badge_name="Project Builder", description="Built and documented 3+ projects", icon="fa-laptop-code"))
        if any(g.status == 'Completed' for g in user.goals) and "Goal Achiever" not in badge_names:
            db.session.add(Badge(user_id=user_id, badge_name="Goal Achiever", description="Successfully completed a target learning goal", icon="fa-bullseye"))
        if any(r.percentage >= 80 for r in user.assessment_results) and "Learning Champion" not in badge_names:
            db.session.add(Badge(user_id=user_id, badge_name="Learning Champion", description="Achieved 80%+ on technical skill assessment", icon="fa-trophy"))

    db.session.commit()

# Skill Gap Helper
def get_skill_gap_analysis(user_id):
    user = db.session.get(User, user_id)
    target_career = user.profile.career_goal if (user and user.profile) else "Full-Stack Software Engineer"

    benchmarks = {
        "Full-Stack Software Engineer": ["Python", "JavaScript", "HTML & CSS", "SQL & Relational Databases", "Flask Framework", "Git & GitHub", "Data Structures & Algorithms"],
        "AI/ML Engineer": ["Python", "Data Structures & Algorithms", "SQL & Relational Databases", "Problem Solving", "Time Management"],
        "Cybersecurity Specialist": ["Python", "Cybersecurity Fundamentals", "Git & GitHub", "Problem Solving", "Communication"]
    }

    req_skills = benchmarks.get(target_career, benchmarks["Full-Stack Software Engineer"])
    student_skills_map = {ss.skill.name: ss.level for ss in user.skills}

    gap_analysis = []
    for s_name in req_skills:
        current_lvl = student_skills_map.get(s_name, "Missing")
        if current_lvl == "Missing":
            gap_analysis.append({'skill': s_name, 'status': 'Missing', 'badge_class': 'bg-danger', 'rec': 'Recommended to add this skill to your learning plan.'})
        elif current_lvl in ["Beginner"]:
            gap_analysis.append({'skill': s_name, 'status': 'Needs Improvement', 'badge_class': 'bg-warning text-dark', 'rec': 'Upgrade from Beginner to Intermediate via courses.'})
        else:
            gap_analysis.append({'skill': s_name, 'status': 'On Track', 'badge_class': 'bg-success', 'rec': 'Proficiency meets industry target level.'})

    return gap_analysis

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact platform administration.', 'danger')
                return redirect(url_for('login'))

            user.last_active_at = datetime.utcnow()
            db.session.commit()

            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'warning')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(name=name, email=email, password_hash=hashed_pw, role=role, is_active=True, status='Active')
        db.session.add(new_user)
        db.session.commit()

        if role == 'student':
            profile = StudentProfile(user_id=new_user.id)
            db.session.add(profile)
            db.session.commit()

        flash('Registration successful! Please log in with your credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Dispatcher Dashboard Route
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('user_role')
    if role == 'mentor':
        return redirect(url_for('mentor_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))

# Student Views
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    user = db.session.get(User, session['user_id'])
    score_data = calculate_student_score(user.id)
    streak_data = ProgressService.calculate_streak(user.id)
    tasks_cat = TaskService.get_student_tasks_categorized(user.id)

    prof = user.profile
    profile_fields = [prof.college, prof.department, prof.year, prof.career_goal, prof.bio, prof.github_url, prof.linkedin_url, prof.portfolio_url]
    filled = sum([1 for f in profile_fields if f and len(f) > 0])
    profile_completion = int((filled / len(profile_fields)) * 100)

    total_points = sum([p.points for p in user.points])
    recent_courses = user.courses[-3:]
    recent_projects = user.projects[-3:]
    active_goals = [g for g in user.goals if g.status != 'Completed']
    recent_feedback = user.feedbacks_received[-2:]
    today_activities = DailyActivity.query.filter_by(student_id=user.id, date=date.today().strftime('%Y-%m-%d')).all()

    return render_template(
        'student/dashboard.html',
        user=user,
        score_data=score_data,
        streak_data=streak_data,
        tasks_cat=tasks_cat,
        profile_completion=profile_completion,
        total_points=total_points,
        recent_courses=recent_courses,
        recent_projects=recent_projects,
        active_goals=active_goals,
        recent_feedback=recent_feedback,
        today_activities=today_activities
    )

@app.route('/student/tasks')
@login_required
@role_required('student')
def student_tasks():
    user = db.session.get(User, session['user_id'])
    tasks_cat = TaskService.get_student_tasks_categorized(user.id)
    skills = user.skills
    courses = user.courses

    return render_template('student/tasks.html', user=user, tasks_cat=tasks_cat, skills=skills, courses=courses)

@app.route('/student/tasks/update/<int:task_id>', methods=['POST'])
@login_required
@role_required('student')
def student_update_task(task_id):
    user_id = session['user_id']
    status = request.form.get('status')
    progress = request.form.get('progress')

    task, err = TaskService.update_task_status(task_id, user_id, status, progress)
    if err:
        flash(err, 'danger')
    else:
        flash(f'Task "{task.title}" updated to {status}.', 'success')

    return redirect(url_for('student_tasks'))

@app.route('/student/tasks/submit/<int:task_id>', methods=['POST'])
@login_required
@role_required('student')
def student_submit_task(task_id):
    user_id = session['user_id']
    sub_type = request.form.get('submission_type', 'GitHub Repository')
    sub_url = request.form.get('submission_url')
    github_url = request.form.get('github_url')
    text_resp = request.form.get('text_response')

    sub, err = TaskService.submit_task(task_id, user_id, sub_type, sub_url, github_url, text_resp)
    if err:
        flash(err, 'danger')
    else:
        award_points(user_id, 150, "Submitted mentor task for evaluation")
        flash('Task submission sent to mentor for review!', 'success')

    return redirect(url_for('student_tasks'))

@app.route('/student/daily-tracker')
@login_required
@role_required('student')
def student_daily_tracker():
    user = db.session.get(User, session['user_id'])
    streak_data = ProgressService.calculate_streak(user.id)
    tasks = MentorTask.query.filter_by(student_id=user.id).filter(MentorTask.status != 'Completed').all()
    recent_logs = DailyActivity.query.filter_by(student_id=user.id).order_by(DailyActivity.created_at.desc()).limit(15).all()
    today_str = date.today().strftime('%Y-%m-%d')

    return render_template('student/daily_tracker.html', user=user, streak_data=streak_data, tasks=tasks, recent_logs=recent_logs, today_str=today_str)

@app.route('/student/daily-tracker/log', methods=['POST'])
@login_required
@role_required('student')
def student_log_daily_activity():
    user_id = session['user_id']
    task_id = request.form.get('task_id')
    task_id = int(task_id) if task_id and task_id.isdigit() else None
    date_str = request.form.get('date', date.today().strftime('%Y-%m-%d'))
    time_spent = int(request.form.get('time_spent_minutes', 60))
    pct_start = int(request.form.get('progress_pct_start', 0))
    pct_end = int(request.form.get('progress_pct_end', 50))
    activity_notes = request.form.get('activity_notes', '')
    remaining_notes = request.form.get('remaining_notes', '')
    difficulty = request.form.get('difficulty_level', 'Medium')

    ProgressService.log_daily_activity(
        student_id=user_id,
        task_id=task_id,
        date_str=date_str,
        time_spent_minutes=time_spent,
        progress_pct_start=pct_start,
        progress_pct_end=pct_end,
        activity_notes=activity_notes,
        remaining_notes=remaining_notes,
        difficulty_level=difficulty
    )

    award_points(user_id, 30, f"Logged daily activity for {date_str}")
    flash('Daily learning progress logged successfully!', 'success')
    return redirect(url_for('student_daily_tracker'))

@app.route('/student/score-breakdown')
@login_required
@role_required('student')
def student_score_breakdown():
    user = db.session.get(User, session['user_id'])
    breakdown = SkillScoreService.calculate_score_transparency(user.id)
    return render_template('student/score_breakdown.html', user=user, breakdown=breakdown)

@app.route('/student/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_profile():
    user = db.session.get(User, session['user_id'])
    prof = user.profile

    if request.method == 'POST':
        user.name = request.form.get('name', user.name)
        prof.college = request.form.get('college', prof.college)
        prof.department = request.form.get('department', prof.department)
        prof.year = request.form.get('year', prof.year)
        prof.career_goal = request.form.get('career_goal', prof.career_goal)
        prof.bio = request.form.get('bio', prof.bio)
        prof.github_url = request.form.get('github_url', prof.github_url)
        prof.linkedin_url = request.form.get('linkedin_url', prof.linkedin_url)
        prof.portfolio_url = request.form.get('portfolio_url', prof.portfolio_url)

        db.session.commit()
        flash('Profile details updated successfully!', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student/profile.html', user=user, prof=prof)

@app.route('/student/skills', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_skills():
    user = db.session.get(User, session['user_id'])
    all_skills = Skill.query.all()
    gap_analysis = get_skill_gap_analysis(user.id)

    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        level = request.form.get('level', 'Beginner')
        progress_map = {'Beginner': 30, 'Intermediate': 65, 'Advanced': 85, 'Expert': 95}

        existing_ss = StudentSkill.query.filter_by(user_id=user.id, skill_id=skill_id).first()
        if existing_ss:
            existing_ss.level = level
            existing_ss.progress = progress_map.get(level, 50)
            existing_ss.updated_at = datetime.utcnow()
        else:
            new_ss = StudentSkill(user_id=user.id, skill_id=skill_id, level=level, progress=progress_map.get(level, 50))
            db.session.add(new_ss)

        db.session.commit()
        award_points(user.id, 25, f"Updated skill level to {level}")
        flash('Skill saved successfully!', 'success')
        return redirect(url_for('student_skills'))

    return render_template('student/skills.html', user=user, all_skills=all_skills, gap_analysis=gap_analysis)

@app.route('/student/goals', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_goals():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            title = request.form.get('title')
            target_level = request.form.get('target_level', 'Advanced')
            deadline = request.form.get('deadline')
            new_goal = Goal(user_id=user.id, title=title, target_level=target_level, deadline=deadline, progress=0, status='In Progress')
            db.session.add(new_goal)
            db.session.commit()
            award_points(user.id, 50, f"Created new learning goal: {title}")
            flash('New learning goal created!', 'success')
        elif action == 'update':
            goal_id = request.form.get('goal_id')
            progress = int(request.form.get('progress', 0))
            status = request.form.get('status', 'In Progress')
            g = db.session.get(Goal, goal_id)
            if g and g.user_id == user.id:
                g.progress = progress
                g.status = status
                if progress == 100:
                    g.status = 'Completed'
                    award_points(user.id, 250, f"Completed learning goal: {g.title}")
                db.session.commit()
                flash('Goal progress updated!', 'success')

        return redirect(url_for('student_goals'))

    return render_template('student/goals.html', user=user)

@app.route('/student/courses', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_courses():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name')
        platform = request.form.get('platform')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        skills_gained = request.form.get('skills_gained')
        status = request.form.get('status', 'In Progress')
        course_url = request.form.get('course_url', '')
        progress_pct = int(request.form.get('progress_percentage', 100 if status == 'Completed' else 40))

        c = Course(
            user_id=user.id,
            name=name,
            platform=platform,
            instructor=instructor,
            duration=duration,
            skills_gained=skills_gained,
            status=status,
            course_url=course_url,
            progress_percentage=progress_pct,
            is_synced=False,
            sync_source='MANUAL'
        )
        db.session.add(c)
        db.session.commit()

        if status == 'Completed':
            award_points(user.id, 100, f"Completed Course: {name}")

        flash('Course record added successfully!', 'success')
        return redirect(url_for('student_courses'))

    return render_template('student/courses.html', user=user)

@app.route('/student/projects', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_projects():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        technologies = request.form.get('technologies')
        skills_applied = request.form.get('skills_applied')
        duration = request.form.get('duration')
        github_link = request.form.get('github_link')
        demo_link = request.form.get('demo_link')
        status = request.form.get('status', 'Completed')

        p = Project(user_id=user.id, name=name, description=description, technologies=technologies, skills_applied=skills_applied, duration=duration, github_link=github_link, demo_link=demo_link, status=status)
        db.session.add(p)
        db.session.commit()

        if status == 'Completed':
            award_points(user.id, 200, f"Completed Project: {name}")

        flash('Project added to portfolio!', 'success')
        return redirect(url_for('student_projects'))

    return render_template('student/projects.html', user=user)

@app.route('/student/certificates', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_certificates():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        name = request.form.get('name')
        issuing_organization = request.form.get('issuing_organization')
        issue_date = request.form.get('issue_date')
        certificate_id = request.form.get('certificate_id')
        skill_category = request.form.get('skill_category')
        verification_url = request.form.get('verification_url')

        ct = Certificate(user_id=user.id, name=name, issuing_organization=issuing_organization, issue_date=issue_date, certificate_id=certificate_id, skill_category=skill_category, verification_url=verification_url)
        db.session.add(ct)
        db.session.commit()

        award_points(user.id, 150, f"Earned Certificate: {name}")
        flash('Certificate record saved successfully!', 'success')
        return redirect(url_for('student_certificates'))

    return render_template('student/certificates.html', user=user)

@app.route('/student/achievements', methods=['GET', 'POST'])
@login_required
@role_required('student')
def student_achievements():
    user = db.session.get(User, session['user_id'])

    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        date = request.form.get('date')
        description = request.form.get('description')

        ach = Achievement(user_id=user.id, title=title, category=category, date=date, description=description)
        db.session.add(ach)
        db.session.commit()

        award_points(user.id, 75, f"Added Achievement: {title}")
        flash('Achievement logged successfully!', 'success')
        return redirect(url_for('student_achievements'))

    return render_template('student/achievements.html', user=user)

@app.route('/student/assessments')
@login_required
@role_required('student')
def student_assessments():
    user = db.session.get(User, session['user_id'])
    assessments = Assessment.query.all()
    user_results = {r.assessment_id: r for r in user.assessment_results}

    return render_template('student/assessments.html', user=user, assessments=assessments, user_results=user_results)

@app.route('/student/take_assessment/<int:assessment_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def take_assessment(assessment_id):
    user = db.session.get(User, session['user_id'])
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash('Assessment not found.', 'danger')
        return redirect(url_for('student_assessments'))
    questions = json.loads(assessment.questions_json)

    if request.method == 'POST':
        score = 0
        for i, q in enumerate(questions):
            ans = request.form.get(f'q_{i}')
            if ans is not None and int(ans) == q['ans']:
                score += 1

        total = len(questions)
        pct = round((score / total) * 100.0, 1)

        level = "Beginner"
        if pct >= 80:
            level = "Advanced"
        elif pct >= 60:
            level = "Intermediate"

        existing = AssessmentResult.query.filter_by(user_id=user.id, assessment_id=assessment.id).first()
        if existing:
            existing.score = score
            existing.max_score = total
            existing.percentage = pct
            existing.level_assigned = level
            existing.taken_at = datetime.utcnow()
        else:
            res = AssessmentResult(user_id=user.id, assessment_id=assessment.id, score=score, max_score=total, percentage=pct, level_assigned=level)
            db.session.add(res)

        db.session.commit()
        award_points(user.id, 100, f"Took Assessment: {assessment.title} ({pct}%)")
        flash(f'Assessment complete! You scored {score}/{total} ({pct}%). Level evaluated: {level}.', 'success')
        return redirect(url_for('student_assessments'))

    return render_template('student/take_assessment.html', user=user, assessment=assessment, questions=questions)

@app.route('/student/settings/integrations')
@login_required
@role_required('student')
def student_integrations():
    user = db.session.get(User, session['user_id'])
    platforms = ['Coursera', 'edX', 'Udemy']
    connections = {p: IntegrationService.get_connection_status(user.id, p) for p in platforms}

    return render_template('student/settings/integrations.html', user=user, connections=connections)

@app.route('/student/settings/integrations/<platform>/connect', methods=['POST'])
@login_required
@role_required('student')
def student_connect_integration(platform):
    user_id = session['user_id']
    conn, err = IntegrationService.connect_platform(user_id, platform)
    if err:
        flash(err, 'warning')
    else:
        flash(f'Connected to {platform}! External courses can now be synchronized.', 'success')

    return redirect(url_for('student_integrations'))

@app.route('/student/settings/integrations/<platform>/sync', methods=['POST'])
@login_required
@role_required('student')
def student_sync_integration(platform):
    user_id = session['user_id']
    ok, msg = IntegrationService.sync_platform_courses(user_id, platform)
    if ok:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')

    return redirect(url_for('student_integrations'))

@app.route('/student/report')
@login_required
@role_required('student')
def student_report():
    user = db.session.get(User, session['user_id'])
    score_data = calculate_student_score(user.id)
    gap_analysis = get_skill_gap_analysis(user.id)
    total_points = sum([p.points for p in user.points])

    return render_template(
        'student/report.html',
        user=user,
        score_data=score_data,
        gap_analysis=gap_analysis,
        total_points=total_points
    )

# Mentor Views
@app.route('/mentor/dashboard')
@login_required
@role_required('mentor')
def mentor_dashboard():
    mentor = db.session.get(User, session['user_id'])
    students = User.query.filter_by(role='student', is_active=True).all()
    skills = Skill.query.filter_by(status='Active').all()
    courses = Course.query.all()

    student_matrix = []
    total_tasks_assigned = 0
    total_tasks_completed = 0
    at_risk_count = 0
    pending_evals_count = 0
    attention_required_list = []

    for st in students:
        s_data = calculate_student_score(st.id)
        at_risk_info = ProgressService.detect_at_risk(st.id)
        if at_risk_info['is_at_risk']:
            at_risk_count += 1
            attention_required_list.append({
                'student': st,
                'reasons': at_risk_info['reasons'],
                'score': s_data['overall']
            })

        st_tasks = MentorTask.query.filter_by(student_id=st.id).all()
        t_assigned = len(st_tasks)
        t_completed = len([t for t in st_tasks if t.status == 'Completed'])
        total_tasks_assigned += t_assigned
        total_tasks_completed += t_completed

        if any(t.status == 'Submitted' for t in st_tasks):
            pending_evals_count += 1

        streak_info = ProgressService.calculate_streak(st.id)

        student_matrix.append({
            'student': st,
            'score': s_data['overall'],
            'course_avg_progress': s_data['courses'],
            'task_completion_pct': round((t_completed / t_assigned * 100.0), 1) if t_assigned > 0 else 0.0,
            'streak_days': streak_info['current_streak'],
            'at_risk': at_risk_info['is_at_risk'],
            'at_risk_reasons': at_risk_info['reasons'],
            'last_active': st.last_active_at.strftime('%Y-%m-%d') if st.last_active_at else 'Today'
        })

    avg_student_progress = round(sum([s['score'] for s in student_matrix]) / len(student_matrix), 1) if student_matrix else 0.0

    return render_template(
        'mentor/dashboard.html',
        mentor=mentor,
        students=students,
        skills=skills,
        courses=courses,
        student_matrix=student_matrix,
        attention_required_list=attention_required_list,
        total_assigned_students=len(students),
        active_students=len(students) - at_risk_count,
        at_risk_count=at_risk_count,
        total_tasks_assigned=total_tasks_assigned,
        total_tasks_completed=total_tasks_completed,
        avg_student_progress=avg_student_progress,
        pending_evals_count=pending_evals_count
    )

@app.route('/mentor/tasks/assign', methods=['POST'])
@login_required
@role_required('mentor')
def mentor_assign_task():
    mentor_id = session['user_id']
    student_id = int(request.form.get('student_id'))
    title = request.form.get('title')
    description = request.form.get('description')
    task_type = request.form.get('task_type', 'Assignment')
    skill_id = request.form.get('skill_id')
    skill_id = int(skill_id) if skill_id and skill_id.isdigit() else None
    course_id = request.form.get('course_id')
    course_id = int(course_id) if course_id and course_id.isdigit() else None
    priority = request.form.get('priority', 'Medium')
    due_date = request.form.get('due_date')
    estimated_hours = request.form.get('estimated_hours', 2.0)
    resource_url = request.form.get('resource_url')
    submission_type = request.form.get('submission_type', 'GitHub Repository')
    mentor_notes = request.form.get('mentor_notes')

    task = TaskService.create_task(
        mentor_id=mentor_id,
        student_id=student_id,
        title=title,
        description=description,
        task_type=task_type,
        skill_id=skill_id,
        course_id=course_id,
        priority=priority,
        due_date=due_date,
        estimated_hours=estimated_hours,
        resource_url=resource_url,
        submission_type=submission_type,
        mentor_notes=mentor_notes
    )

    flash(f'Task "{title}" successfully assigned to student!', 'success')
    return redirect(url_for('mentor_dashboard'))

@app.route('/mentor/eval/<int:student_id>', methods=['GET', 'POST'])
@login_required
@role_required('mentor')
def mentor_eval(student_id):
    mentor = db.session.get(User, session['user_id'])
    student = db.session.get(User, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('mentor_dashboard'))

    score_data = calculate_student_score(student.id)
    at_risk_info = ProgressService.detect_at_risk(student.id)
    streak_info = ProgressService.calculate_streak(student.id)
    tasks = MentorTask.query.filter_by(student_id=student.id).all()
    activity_timeline = ActivityLog.query.filter_by(student_id=student.id).order_by(ActivityLog.created_at.desc()).limit(10).all()
    skills = Skill.query.all()
    courses = Course.query.all()

    if request.method == 'POST':
        rating = float(request.form.get('rating', 4.0))
        comments = request.form.get('comments', '')
        recommendations = request.form.get('recommendations', '')

        fb = MentorFeedback(
            student_id=student.id,
            mentor_id=mentor.id,
            rating=rating,
            comments=comments,
            recommendations=recommendations
        )
        db.session.add(fb)
        db.session.commit()

        award_points(student.id, 50, f"Received Mentor Feedback ({rating}/5.0 Stars)")
        AuditService.log_event(mentor.id, "Submitted Mentor Feedback", f"Student: {student.name}")
        flash(f'Evaluation and feedback submitted for {student.name}.', 'success')
        return redirect(url_for('mentor_eval', student_id=student.id))

    feedbacks = MentorFeedback.query.filter_by(student_id=student.id).order_by(MentorFeedback.created_at.desc()).all()
    return render_template(
        'mentor/eval_student.html',
        mentor=mentor,
        student=student,
        score_data=score_data,
        at_risk_info=at_risk_info,
        streak_info=streak_info,
        tasks=tasks,
        activity_timeline=activity_timeline,
        feedbacks=feedbacks,
        skills=skills,
        courses=courses
    )

@app.route('/mentor/tasks/<int:task_id>/review', methods=['POST'])
@login_required
@role_required('mentor')
def mentor_review_task(task_id):
    mentor_id = session['user_id']
    feedback_text = request.form.get('mentor_feedback', '')
    approved = request.form.get('action') == 'approve'

    task, err = TaskService.review_task(task_id, mentor_id, feedback_text, approved)
    if err:
        flash(err, 'danger')
    else:
        status_msg = "approved" if approved else "returned for revisions"
        flash(f'Task submission {status_msg}.', 'success')

    return redirect(request.referrer or url_for('mentor_dashboard'))

# =========================================================================
# SAAS ADMINISTRATION & USER MANAGEMENT ROUTES
# =========================================================================

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    users = User.query.all()
    students = [u for u in users if u.role == 'student' and u.is_active]
    mentors = [u for u in users if u.role == 'mentor' and u.is_active]
    skills = Skill.query.filter_by(status='Active').all()
    courses = Course.query.all()
    audit_logs = AuditService.get_recent_logs(8)

    avg_score = 0.0
    if students:
        avg_score = round(sum([calculate_student_score(st.id)['overall'] for st in students]) / len(students), 1)

    return render_template(
        'admin/dashboard.html',
        users=users,
        students=students,
        mentors=mentors,
        skills=skills,
        courses=courses,
        avg_score=avg_score,
        audit_logs=audit_logs
    )

@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_user_directory():
    role = request.args.get('role', 'all')
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')
    sort_by = request.args.get('sort', 'name')

    users = UserService.search_and_filter_users(
        role=role,
        search_query=search,
        status_filter=status_filter,
        sort_by=sort_by
    )

    return render_template(
        'admin/users.html',
        users=users,
        selected_role=role,
        search_query=search,
        selected_status=status_filter,
        selected_sort=sort_by
    )

@app.route('/admin/users/add-student', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_student():
    actor_id = session['user_id']
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    student_code = request.form.get('student_code', '').strip()
    department = request.form.get('department', 'Computer Science & Engineering')
    year = request.form.get('year', '1st Year B.Tech')
    career_goal = request.form.get('career_goal', 'Software Engineer')

    user, err = UserService.create_student(
        actor_id=actor_id,
        name=name,
        email=email,
        password=password,
        student_code=student_code,
        department=department,
        year=year,
        career_goal=career_goal
    )

    if err:
        flash(err, 'danger')
    else:
        flash(f'Student account for "{name}" created successfully.', 'success')

    return redirect(url_for('admin_user_directory', role='student'))

@app.route('/admin/users/add-mentor', methods=['POST'])
@login_required
@role_required('admin')
def admin_add_mentor():
    actor_id = session['user_id']
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    employee_code = request.form.get('employee_code', '').strip()
    department = request.form.get('department', 'Computer Science & Engineering')

    user, err = UserService.create_mentor(
        actor_id=actor_id,
        name=name,
        email=email,
        password=password,
        employee_code=employee_code,
        department=department
    )

    if err:
        flash(err, 'danger')
    else:
        flash(f'Mentor account for "{name}" created successfully.', 'success')

    return redirect(url_for('admin_user_directory', role='mentor'))

@app.route('/admin/users/<int:user_id>/view')
@login_required
@role_required('admin')
def admin_view_user(user_id):
    target = db.session.get(User, user_id)
    if not target:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_user_directory'))

    score_data = calculate_student_score(target.id) if target.role == 'student' else None
    audit_history = AuditLog.query.filter_by(actor_id=target.id).order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template(
        'admin/user_detail.html',
        target=target,
        score_data=score_data,
        audit_history=audit_history
    )

@app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def admin_toggle_user_status(user_id):
    actor_id = session['user_id']
    target, err = UserService.toggle_user_status(actor_id, user_id)

    if err:
        flash(err, 'danger')
    else:
        status_str = "reactivated" if target.is_active else "deactivated"
        flash(f'User account {target.email} has been {status_str}.', 'info')

    return redirect(request.referrer or url_for('admin_user_directory'))

@app.route('/admin/skills')
@login_required
@role_required('admin')
def admin_skills():
    skills = Skill.query.all()
    # Compute student usage count per skill
    usage_map = {}
    for sk in skills:
        usage_map[sk.id] = StudentSkill.query.filter_by(skill_id=sk.id).count()

    return render_template('admin/skills.html', skills=skills, usage_map=usage_map)

@app.route('/admin/skills/create', methods=['POST'])
@login_required
@role_required('admin')
def admin_create_skill():
    actor_id = session['user_id']
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'Technical')
    description = request.form.get('description', '').strip()
    expected_prof = request.form.get('expected_proficiency', 'Advanced')

    if Skill.query.filter_by(name=name).first():
        flash('Skill with this name already exists.', 'warning')
    else:
        new_skill = Skill(name=name, category=category, description=description, status='Active', expected_proficiency=expected_prof)
        db.session.add(new_skill)
        db.session.commit()

        AuditService.log_event(actor_id, "Created Platform Skill", f"{name} ({category})")
        flash(f'Skill "{name}" created in catalog.', 'success')

    return redirect(url_for('admin_skills'))

@app.route('/admin/skills/<int:skill_id>/archive', methods=['POST'])
@login_required
@role_required('admin')
def admin_archive_skill(skill_id):
    actor_id = session['user_id']
    sk = db.session.get(Skill, skill_id)
    if sk:
        sk.status = 'Archived' if sk.status == 'Active' else 'Active'
        db.session.commit()
        AuditService.log_event(actor_id, "Toggled Skill Status", f"{sk.name} ({sk.status})")
        flash(f'Skill "{sk.name}" status set to {sk.status}.', 'info')

    return redirect(url_for('admin_skills'))

@app.route('/admin/audit-log')
@login_required
@role_required('admin')
def admin_audit_log():
    logs = AuditService.get_recent_logs(100)
    return render_template('admin/audit_log.html', logs=logs)

@app.route('/admin/reports')
@login_required
@role_required('admin')
def admin_reports():
    return render_template('admin/reports.html')

@app.route('/admin/reports/download/<report_type>')
@login_required
@role_required('admin')
def admin_download_report(report_type):
    actor_id = session['user_id']
    if report_type == 'student-development':
        csv_data = ReportService.generate_student_development_csv()
        filename = "student_development_report.csv"
    elif report_type == 'mentor-activity':
        csv_data = ReportService.generate_mentor_activity_csv()
        filename = "mentor_activity_report.csv"
    elif report_type == 'skill-adoption':
        csv_data = ReportService.generate_skill_adoption_csv()
        filename = "skill_adoption_report.csv"
    else:
        flash('Invalid report type requested.', 'danger')
        return redirect(url_for('admin_reports'))

    AuditService.log_event(actor_id, "Downloaded Report CSV", f"Report: {report_type}")
    response = make_response(csv_data)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/admin/settings')
@login_required
@role_required('admin')
def admin_settings():
    settings = SystemSettings.query.all()
    return render_template('admin/settings.html', settings=settings)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

