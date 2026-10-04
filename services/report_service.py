import io
import csv
from models import User, Skill, StudentSkill, MentorTask
from services.scoring_service import SkillScoreService

class ReportService:
    """
    Service for generating CSV export reports for Administrative Monitoring.
    """

    @staticmethod
    def generate_student_development_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Student ID', 'Full Name', 'Email', 'Department', 'Career Goal', 'Overall Development Score (%)', 'Course Score (%)', 'Project Score (%)', 'Assessment Score (%)', 'Certificate Score (%)', 'Mentor Score (%)', 'Status'])

        students = User.query.filter_by(role='student').all()
        for st in students:
            scores = SkillScoreService.calculate_overall_score(st.id)
            trans = SkillScoreService.calculate_score_transparency(st.id)
            dept = st.profile.department if st.profile else 'N/A'
            goal = st.profile.career_goal if st.profile else 'N/A'
            code = st.student_code or f"STU-{st.id}"

            dims = {d['name']: d['raw_score'] for d in trans['dimensions']}
            writer.writerow([
                code,
                st.name,
                st.email,
                dept,
                goal,
                scores,
                dims.get('Courses Progress', 0.0),
                dims.get('Projects Portfolio', 0.0),
                dims.get('Skill Assessments', 0.0),
                dims.get('Certificates', 0.0),
                dims.get('Mentor Evaluation', 0.0),
                st.status
            ])

        return output.getvalue()

    @staticmethod
    def generate_mentor_activity_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Mentor Name', 'Email', 'Assigned Tasks Count', 'Completed Tasks Count', 'Feedbacks Given'])

        mentors = User.query.filter_by(role='mentor').all()
        for m in mentors:
            tasks = MentorTask.query.filter_by(mentor_id=m.id).all()
            completed = [t for t in tasks if t.status == 'Completed']
            fb_count = len(m.feedbacks_given)
            writer.writerow([m.name, m.email, len(tasks), len(completed), fb_count])

        return output.getvalue()

    @staticmethod
    def generate_skill_adoption_csv():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Skill Name', 'Category', 'Status', 'Students Enrolled', 'Average Proficiency Level'])

        skills = Skill.query.all()
        for sk in skills:
            ss_list = StudentSkill.query.filter_by(skill_id=sk.id).all()
            avg_prog = round(sum([ss.progress for ss in ss_list]) / len(ss_list), 1) if ss_list else 0.0
            writer.writerow([sk.name, sk.category, sk.status, len(ss_list), f"{avg_prog}%"])

        return output.getvalue()
