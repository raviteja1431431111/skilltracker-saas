import unittest
from datetime import date
from app import app, db
from models import User, Skill, AuditLog
from services.scoring_service import SkillScoreService
from services.user_service import UserService
from services.audit_service import AuditService
from services.report_service import ReportService

class SkillTrackerSaaSEnterpriseTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_landing_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_health_check_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'skilltracker')

    def test_admin_user_creation_and_soft_deactivate(self):
        with app.app_context():
            # Clean up existing test user if present from prior runs
            existing = User.query.filter_by(email="saastest@college.edu").first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            admin = User.query.filter_by(email='admin@college.edu').first()
            
            # 1. Create Student
            new_student, err = UserService.create_student(
                actor_id=admin.id,
                name="SaaS Test Student",
                email="saastest@college.edu",
                password="password123",
                student_code="STU-9999"
            )
            self.assertIsNone(err)
            self.assertTrue(new_student.is_active)

            # 2. Deactivate User (Soft Delete)
            deact_user, d_err = UserService.toggle_user_status(admin.id, new_student.id)
            self.assertIsNone(d_err)
            self.assertFalse(deact_user.is_active)
            self.assertEqual(deact_user.status, 'Inactive')

            # 3. Verify Audit Log
            latest_audit = AuditLog.query.filter_by(actor_id=admin.id).order_by(AuditLog.timestamp.desc()).first()
            self.assertIn("Deactivated User Account", latest_audit.action)

            # Clean up after test
            db.session.delete(new_student)
            db.session.commit()

    def test_csv_report_generation(self):
        with app.app_context():
            csv_data = ReportService.generate_student_development_csv()
            self.assertIn("Student ID", csv_data)
            self.assertIn("Rahul Sharma", csv_data)

    def test_score_transparency(self):
        with app.app_context():
            student = User.query.filter_by(email='student@college.edu').first()
            breakdown = SkillScoreService.calculate_score_transparency(student.id)
            self.assertEqual(len(breakdown['dimensions']), 5)
            self.assertGreater(breakdown['overall'], 0.0)

if __name__ == '__main__':
    unittest.main()

