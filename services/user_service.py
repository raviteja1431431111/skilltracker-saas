from datetime import datetime
from werkzeug.security import generate_password_hash
from models import db, User, StudentProfile
from services.audit_service import AuditService

class UserService:
    """
    User Management Service for Admin Operations (Add Student, Add Mentor, Soft Deactivate).
    """

    @staticmethod
    def create_student(actor_id, name, email, password, student_code=None, department='Computer Science & Engineering', year='1st Year B.Tech', college='National Institute of Technology', career_goal='Software Engineer', phone_number=None):
        if User.query.filter_by(email=email).first():
            return None, "An account with this email address already exists."

        hashed_pw = generate_password_hash(password)
        user = User(
            name=name,
            email=email,
            password_hash=hashed_pw,
            role='student',
            is_active=True,
            status='Active',
            student_code=student_code,
            phone_number=phone_number
        )
        db.session.add(user)
        db.session.commit()

        profile = StudentProfile(
            user_id=user.id,
            college=college,
            department=department,
            year=year,
            career_goal=career_goal
        )
        db.session.add(profile)
        db.session.commit()

        AuditService.log_event(actor_id, "Created Student Account", f"{user.name} ({user.email})")
        return user, None

    @staticmethod
    def create_mentor(actor_id, name, email, password, employee_code=None, department='Computer Science & Engineering', phone_number=None):
        if User.query.filter_by(email=email).first():
            return None, "An account with this email address already exists."

        hashed_pw = generate_password_hash(password)
        user = User(
            name=name,
            email=email,
            password_hash=hashed_pw,
            role='mentor',
            is_active=True,
            status='Active',
            employee_code=employee_code,
            phone_number=phone_number
        )
        db.session.add(user)
        db.session.commit()

        AuditService.log_event(actor_id, "Created Mentor Account", f"{user.name} ({user.email})")
        return user, None

    @staticmethod
    def toggle_user_status(actor_id, target_user_id):
        target = db.session.get(User, target_user_id)
        if not target:
            return None, "User account not found."

        if target.id == actor_id:
            return None, "You cannot deactivate your own account."

        target.is_active = not target.is_active
        target.status = 'Active' if target.is_active else 'Inactive'
        db.session.commit()

        action_str = "Reactivated User Account" if target.is_active else "Deactivated User Account"
        AuditService.log_event(actor_id, action_str, f"{target.name} ({target.email})")
        return target, None

    @staticmethod
    def search_and_filter_users(role=None, search_query=None, status_filter=None, department_filter=None, sort_by='name'):
        query = User.query

        if role and role != 'all':
            query = query.filter_by(role=role)

        if status_filter and status_filter != 'all':
            if status_filter == 'active':
                query = query.filter_by(is_active=True)
            elif status_filter == 'inactive':
                query = query.filter_by(is_active=False)

        if search_query:
            term = f"%{search_query}%"
            query = query.filter((User.name.like(term)) | (User.email.like(term)) | (User.student_code.like(term)) | (User.employee_code.like(term)))

        if sort_by == 'recently_joined':
            query = query.order_by(User.created_at.desc())
        elif sort_by == 'last_active':
            query = query.order_by(User.last_active_at.desc())
        elif sort_by == 'role':
            query = query.order_by(User.role.asc())
        else:
            query = query.order_by(User.name.asc())

        return query.all()
