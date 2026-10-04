from datetime import datetime
from models import db, PlatformConnection, ExternalCourse, SyncLog, Course
from providers.coursera_provider import CourseraProvider
from providers.edx_provider import EdXProvider
from providers.udemy_provider import UdemyProvider

class IntegrationService:
    """
    Platform Connection & Synchronization Manager for External Education Providers.
    Never exposes OAuth tokens to frontend templates.
    """
    
    PROVIDERS = {
        'Coursera': CourseraProvider(),
        'edX': EdXProvider(),
        'Udemy': UdemyProvider()
    }

    @staticmethod
    def get_provider(platform):
        return IntegrationService.PROVIDERS.get(platform)

    @staticmethod
    def get_connection_status(student_id, platform):
        conn = PlatformConnection.query.filter_by(student_id=student_id, platform=platform).first()
        provider = IntegrationService.get_provider(platform)
        is_cfg = provider.is_configured() if provider else False

        if not conn:
            return {
                'platform': platform,
                'status': 'DISCONNECTED',
                'is_configured': is_cfg,
                'connected_at': None,
                'last_synced_at': None
            }

        return {
            'platform': platform,
            'status': conn.status,
            'is_configured': is_cfg,
            'connected_at': conn.connected_at.strftime('%Y-%m-%d %H:%M') if conn.connected_at else None,
            'last_synced_at': conn.last_synced_at.strftime('%Y-%m-%d %H:%M') if conn.last_synced_at else None
        }

    @staticmethod
    def connect_platform(student_id, platform):
        provider = IntegrationService.get_provider(platform)
        if not provider or not provider.is_configured():
            return None, f"{platform} integration is not configured with environment OAuth credentials."

        conn = PlatformConnection.query.filter_by(student_id=student_id, platform=platform).first()
        if not conn:
            conn = PlatformConnection(
                student_id=student_id,
                platform=platform,
                status='CONNECTED',
                access_token_encrypted='encrypted_oauth_access_token_mock',
                refresh_token_encrypted='encrypted_oauth_refresh_token_mock',
                connected_at=datetime.utcnow()
            )
            db.session.add(conn)
        else:
            conn.status = 'CONNECTED'
            conn.connected_at = datetime.utcnow()

        db.session.commit()
        return conn, None

    @staticmethod
    def sync_platform_courses(student_id, platform):
        conn = PlatformConnection.query.filter_by(student_id=student_id, platform=platform).first()
        if not conn or conn.status != 'CONNECTED':
            return False, f"Platform {platform} is not connected."

        provider = IntegrationService.get_provider(platform)
        enrollments, err = provider.get_enrollments(conn.access_token_encrypted)

        if err:
            log = SyncLog(connection_id=conn.id, platform=platform, status='FAILURE', message=err)
            db.session.add(log)
            db.session.commit()
            return False, err

        items_synced = 0
        for enr in enrollments:
            # Sync to ExternalCourse table
            ext_c = ExternalCourse.query.filter_by(student_id=student_id, platform=platform, external_course_id=enr['external_course_id']).first()
            if not ext_c:
                ext_c = ExternalCourse(
                    student_id=student_id,
                    platform=platform,
                    external_course_id=enr['external_course_id'],
                    content_progress=enr['content_progress'],
                    graded_progress=enr['graded_progress'],
                    overall_progress=enr['overall_progress'],
                    sync_status='OK',
                    sync_source='OAUTH_API'
                )
                db.session.add(ext_c)
            else:
                ext_c.overall_progress = enr['overall_progress']
                ext_c.last_synced_at = datetime.utcnow()

            # Synchronize with main Course entity if names match
            course = Course.query.filter_by(user_id=student_id, platform=platform, name=enr['course_name']).first()
            if course:
                course.progress_percentage = int(enr['overall_progress'])
                course.is_synced = True
                course.sync_source = platform.upper()
                if course.progress_percentage >= 100:
                    course.status = 'Completed'

            items_synced += 1

        conn.last_synced_at = datetime.utcnow()
        log = SyncLog(
            connection_id=conn.id,
            platform=platform,
            status='SUCCESS',
            message=f'Successfully synchronized {items_synced} courses.',
            items_checked=items_synced,
            items_completed=items_synced
        )
        db.session.add(log)
        db.session.commit()

        return True, f"Successfully synchronized {items_synced} {platform} courses."
