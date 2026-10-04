from datetime import datetime
from models import db, AuditLog

class AuditService:
    """
    Service for recording administrative audit log events.
    """

    @staticmethod
    def log_event(actor_id, action, target_resource, result='SUCCESS'):
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            target_resource=target_resource,
            result=result,
            timestamp=datetime.utcnow()
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    @staticmethod
    def get_recent_logs(limit=50):
        return AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
