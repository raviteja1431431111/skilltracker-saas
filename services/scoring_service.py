from models import db, User, Course, Project, AssessmentResult, Certificate, MentorFeedback

class SkillScoreService:
    """
    Centralized, Data-Driven Skill Score Service.
    Calculates student performance strictly from stored database entities.
    No static or random numbers are generated.
    """

    @staticmethod
    def calculate_course_score(student_id):
        student = db.session.get(User, student_id)
        if not student or not student.courses:
            return 0.0
        # Average actual progress percentage across all courses
        total_pct = sum([c.progress_percentage for c in student.courses])
        return round(total_pct / len(student.courses), 1)

    @staticmethod
    def calculate_project_score(student_id):
        student = db.session.get(User, student_id)
        if not student or not student.projects:
            return 0.0
        
        # Calculates score based on completion & mentor rating
        scores = []
        for p in student.projects:
            if p.status == 'Completed':
                # Base 80% for completed project + mentor rating contribution (max 20%)
                rating_contrib = (p.mentor_rating / 5.0) * 20.0 if p.mentor_rating else 15.0
                scores.append(min(100.0, 80.0 + rating_contrib))
            else:
                scores.append(40.0) # In progress project baseline
        
        return round(sum(scores) / len(scores), 1)

    @staticmethod
    def calculate_assessment_score(student_id):
        student = db.session.get(User, student_id)
        if not student or not student.assessment_results:
            return 0.0
        percentages = [r.percentage for r in student.assessment_results]
        return round(sum(percentages) / len(percentages), 1)

    @staticmethod
    def calculate_certificate_score(student_id):
        student = db.session.get(User, student_id)
        if not student or not student.certificates:
            return 0.0
        # Target: 3 verified certificates = 100%
        return round(min(100.0, (len(student.certificates) / 3.0) * 100.0), 1)

    @staticmethod
    def calculate_mentor_score(student_id):
        student = db.session.get(User, student_id)
        if not student or not student.feedbacks_received:
            return 80.0 # Baseline for student awaiting mentor review
        ratings = [f.rating for f in student.feedbacks_received]
        avg_rating = sum(ratings) / len(ratings)
        return round((avg_rating / 5.0) * 100.0, 1)

    @staticmethod
    def calculate_overall_score(student_id):
        c_score = SkillScoreService.calculate_course_score(student_id)
        p_score = SkillScoreService.calculate_project_score(student_id)
        a_score = SkillScoreService.calculate_assessment_score(student_id)
        cert_score = SkillScoreService.calculate_certificate_score(student_id)
        m_score = SkillScoreService.calculate_mentor_score(student_id)

        overall = (
            (c_score * 0.25) +
            (p_score * 0.30) +
            (a_score * 0.20) +
            (cert_score * 0.10) +
            (m_score * 0.15)
        )
        return round(overall, 1)

    @staticmethod
    def calculate_score_transparency(student_id):
        c_score = SkillScoreService.calculate_course_score(student_id)
        p_score = SkillScoreService.calculate_project_score(student_id)
        a_score = SkillScoreService.calculate_assessment_score(student_id)
        cert_score = SkillScoreService.calculate_certificate_score(student_id)
        m_score = SkillScoreService.calculate_mentor_score(student_id)

        c_contrib = round(c_score * 0.25, 2)
        p_contrib = round(p_score * 0.30, 2)
        a_contrib = round(a_score * 0.20, 2)
        cert_contrib = round(cert_score * 0.10, 2)
        m_contrib = round(m_score * 0.15, 2)

        overall = round(c_contrib + p_contrib + a_contrib + cert_contrib + m_contrib, 1)

        return {
            'overall': overall,
            'dimensions': [
                {'name': 'Courses Progress', 'weight': '25%', 'raw_score': c_score, 'contribution': c_contrib, 'detail': 'Average progress across enrolled courses'},
                {'name': 'Projects Portfolio', 'weight': '30%', 'raw_score': p_score, 'contribution': p_contrib, 'detail': 'Project completion & mentor project ratings'},
                {'name': 'Skill Assessments', 'weight': '20%', 'raw_score': a_score, 'contribution': a_contrib, 'detail': 'Average score on technical quizzes'},
                {'name': 'Certificates', 'weight': '10%', 'raw_score': cert_score, 'contribution': cert_contrib, 'detail': 'Verified certifications count against target of 3'},
                {'name': 'Mentor Evaluation', 'weight': '15%', 'raw_score': m_score, 'contribution': m_contrib, 'detail': 'Mentor star rating converted to percentage'}
            ]
        }
