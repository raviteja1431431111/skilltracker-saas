from datetime import datetime, date
from models import db, MentorTask, TaskSubmission, ActivityLog, Notification

class TaskService:
    """
    Task Management Service for Mentor Assignments & Student Submissions.
    """

    @staticmethod
    def create_task(mentor_id, student_id, title, description, task_type='Assignment', skill_id=None, course_id=None, priority='Medium', start_date=None, due_date=None, estimated_hours=2.0, resource_url=None, submission_type='GitHub Repository', mentor_notes=None):
        today_str = datetime.utcnow().strftime('%Y-%m-%d')
        start = start_date or today_str
        due = due_date or today_str

        task = MentorTask(
            mentor_id=mentor_id,
            student_id=student_id,
            title=title,
            description=description,
            task_type=task_type,
            skill_id=skill_id,
            course_id=course_id,
            priority=priority,
            start_date=start,
            due_date=due,
            estimated_hours=float(estimated_hours),
            resource_url=resource_url,
            submission_type=submission_type,
            status='Assigned',
            progress=0,
            mentor_notes=mentor_notes
        )
        db.session.add(task)
        db.session.commit()

        # Log Activity & Notification
        log = ActivityLog(student_id=student_id, event_type='TASK_CREATED', description=f'New task assigned by mentor: "{title}"')
        notif = Notification(user_id=student_id, title='New Task Assigned', message=f'Mentor assigned you a new task: "{title}". Due: {due}', type='info', link='/student/tasks')
        db.session.add(log)
        db.session.add(notif)
        db.session.commit()

        return task

    @staticmethod
    def update_task_status(task_id, student_id, new_status, progress=None):
        task = db.session.get(MentorTask, task_id)
        if not task or task.student_id != student_id:
            return None, "Task not found or unauthorized"

        task.status = new_status
        if progress is not None:
            task.progress = int(progress)
            if task.progress == 100 and new_status != 'Completed':
                task.status = 'Submitted'

        if new_status == 'Completed':
            task.completed_at = datetime.utcnow()
            task.progress = 100

        task.updated_at = datetime.utcnow()
        
        # Activity log
        log = ActivityLog(student_id=student_id, event_type='TASK_PROGRESS_UPDATED', description=f'Task "{task.title}" status updated to {new_status} ({task.progress}%)')
        db.session.add(log)
        db.session.commit()

        return task, None

    @staticmethod
    def submit_task(task_id, student_id, submission_type='GitHub Repository', submission_url=None, github_url=None, text_response=None):
        task = db.session.get(MentorTask, task_id)
        if not task or task.student_id != student_id:
            return None, "Task not found or unauthorized"

        submission = TaskSubmission(
            task_id=task.id,
            student_id=student_id,
            submission_type=submission_type,
            submission_url=submission_url,
            github_url=github_url,
            text_response=text_response,
            status='Submitted'
        )
        db.session.add(submission)

        task.status = 'Submitted'
        task.progress = 100
        task.updated_at = datetime.utcnow()

        # Notify mentor
        notif = Notification(user_id=task.mentor_id, title='Task Submission Received', message=f'Student submitted work for task: "{task.title}"', type='success', link=f'/mentor/eval/{student_id}')
        log = ActivityLog(student_id=student_id, event_type='TASK_SUBMITTED', description=f'Submitted work for task "{task.title}"')
        db.session.add(notif)
        db.session.add(log)
        db.session.commit()

        return submission, None

    @staticmethod
    def review_task(task_id, mentor_id, feedback_text, approved=True):
        task = db.session.get(MentorTask, task_id)
        if not task or task.mentor_id != mentor_id:
            return None, "Task not found or unauthorized"

        submission = TaskSubmission.query.filter_by(task_id=task.id).order_by(TaskSubmission.submitted_at.desc()).first()
        if submission:
            submission.mentor_feedback = feedback_text
            submission.status = 'Approved' if approved else 'Revision Requested'

        if approved:
            task.status = 'Completed'
            task.completed_at = datetime.utcnow()
            task.progress = 100
            msg = f'Mentor approved task: "{task.title}"'
        else:
            task.status = 'In Progress'
            msg = f'Mentor requested revisions for task: "{task.title}"'

        notif = Notification(user_id=task.student_id, title='Task Review Update', message=msg, type='info' if approved else 'warning', link='/student/tasks')
        db.session.add(notif)
        db.session.commit()

        return task, None

    @staticmethod
    def get_student_tasks_categorized(student_id):
        tasks = MentorTask.query.filter_by(student_id=student_id).all()
        today_str = datetime.utcnow().strftime('%Y-%m-%d')

        categorized = {
            'today': [],
            'upcoming': [],
            'overdue': [],
            'completed': []
        }

        for t in tasks:
            if t.status == 'Completed':
                categorized['completed'].append(t)
            elif t.due_date < today_str and t.status not in ['Completed', 'Submitted']:
                t.status = 'Overdue'
                categorized['overdue'].append(t)
            elif t.due_date == today_str:
                categorized['today'].append(t)
            else:
                categorized['upcoming'].append(t)

        return categorized
