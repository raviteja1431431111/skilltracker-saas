from datetime import datetime, timedelta, date
from models import db, User, DailyActivity, ActivityLog, MentorTask, Course

class ProgressService:
    """
    Daily Progress Tracking, 90-Day Heatmap, Streak Calculation & At-Risk Rules Engine.
    """

    @staticmethod
    def log_daily_activity(student_id, task_id, date_str, time_spent_minutes, progress_pct_start, progress_pct_end, activity_notes, remaining_notes=None, difficulty_level='Medium'):
        entry = DailyActivity(
            student_id=student_id,
            task_id=task_id if task_id else None,
            date=date_str,
            time_spent_minutes=int(time_spent_minutes),
            progress_pct_start=int(progress_pct_start),
            progress_pct_end=int(progress_pct_end),
            activity_notes=activity_notes,
            remaining_notes=remaining_notes,
            difficulty_level=difficulty_level
        )
        db.session.add(entry)

        # Update linked task progress if provided
        if task_id:
            task = db.session.get(MentorTask, task_id)
            if task and task.student_id == student_id:
                task.progress = int(progress_pct_end)
                if task.progress >= 100:
                    task.status = 'Submitted'
                elif task.status == 'Assigned':
                    task.status = 'In Progress'

        # Log Activity Event
        log = ActivityLog(student_id=student_id, event_type='DAILY_ACTIVITY_LOGGED', description=f'Logged {time_spent_minutes}m of activity on {date_str}: "{activity_notes[:60]}"')
        db.session.add(log)
        db.session.commit()

        return entry

    @staticmethod
    def calculate_streak(student_id):
        activities = DailyActivity.query.filter_by(student_id=student_id).all()
        logs = ActivityLog.query.filter_by(student_id=student_id).all()

        # Gather all unique dates with activity
        unique_dates = set()
        for a in activities:
            unique_dates.add(a.date)
        for l in logs:
            unique_dates.add(l.created_at.strftime('%Y-%m-%d'))

        sorted_dates = sorted(list(unique_dates), reverse=True)
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        yesterday_str = (today - timedelta(days=1)).strftime('%Y-%m-%d')

        current_streak = 0
        if sorted_dates:
            # Check if streak starts from today or yesterday
            check_date = today
            if today_str not in unique_dates:
                if yesterday_str in unique_dates:
                    check_date = today - timedelta(days=1)
                else:
                    check_date = None

            if check_date:
                while check_date.strftime('%Y-%m-%d') in unique_dates:
                    current_streak += 1
                    check_date -= timedelta(days=1)

        # Calculate longest streak
        longest_streak = 0
        if sorted_dates:
            date_objs = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in unique_dates])
            temp_streak = 1
            for i in range(1, len(date_objs)):
                if (date_objs[i] - date_objs[i-1]).days == 1:
                    temp_streak += 1
                elif (date_objs[i] - date_objs[i-1]).days > 1:
                    if temp_streak > longest_streak:
                        longest_streak = temp_streak
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)

        # Generate 90-day heatmap grid data
        heatmap = {}
        for i in range(89, -1, -1):
            d_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            # Count activities on this date
            day_acts = [a for a in activities if a.date == d_str]
            total_mins = sum([a.time_spent_minutes for a in day_acts])
            
            intensity = 0
            if total_mins > 120:
                intensity = 4
            elif total_mins > 60:
                intensity = 3
            elif total_mins > 30:
                intensity = 2
            elif total_mins > 0 or d_str in unique_dates:
                intensity = 1
            
            heatmap[d_str] = {
                'date': d_str,
                'minutes': total_mins,
                'intensity': intensity
            }

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_active_days': len(unique_dates),
            'heatmap': heatmap
        }

    @staticmethod
    def detect_at_risk(student_id):
        reasons = []
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')

        # Rule 1: Inactivity check (> 5 days)
        last_activity = DailyActivity.query.filter_by(student_id=student_id).order_by(DailyActivity.date.desc()).first()
        if last_activity:
            last_date = datetime.strptime(last_activity.date, '%Y-%m-%d').date()
            days_inactive = (today - last_date).days
            if days_inactive >= 5:
                reasons.append(f'No recorded learning activity for {days_inactive} days.')
        else:
            reasons.append('No daily learning activity recorded yet.')

        # Rule 2: Overdue tasks check (>= 2 overdue)
        overdue_tasks = MentorTask.query.filter(
            MentorTask.student_id == student_id,
            MentorTask.due_date < today_str,
            MentorTask.status.notin_(['Completed', 'Submitted'])
        ).all()
        if len(overdue_tasks) >= 2:
            reasons.append(f'Student has {len(overdue_tasks)} overdue tasks requiring attention.')

        # Rule 3: Course schedule lag check (> 20% lag)
        courses = Course.query.filter_by(user_id=student_id).all()
        for c in courses:
            if c.status == 'In Progress' and c.start_date and c.completion_date:
                try:
                    s_date = datetime.strptime(c.start_date, '%Y-%m-%d').date()
                    e_date = datetime.strptime(c.completion_date, '%Y-%m-%d').date()
                    total_days = (e_date - s_date).days or 1
                    elapsed_days = (today - s_date).days
                    expected_pct = min(100.0, max(0.0, (elapsed_days / total_days) * 100.0))
                    actual_pct = c.progress_percentage or 0.0

                    if (expected_pct - actual_pct) > 20.0:
                        reasons.append(f'Course "{c.name}" progress ({actual_pct}%) lags behind expected schedule ({int(expected_pct)}%).')
                except Exception:
                    pass

        return {
            'is_at_risk': len(reasons) > 0,
            'reasons': reasons
        }
