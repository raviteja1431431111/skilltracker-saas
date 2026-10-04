from models import db, Notification

class NotificationService:
    """
    Notification Dispatch Service.
    """

    @staticmethod
    def create_notification(user_id, title, message, type='info', link=None):
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif

    @staticmethod
    def get_unread_notifications(user_id):
        return Notification.query.filter_by(user_id=user_id, is_read=False).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_all_as_read(user_id):
        notifs = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for n in notifs:
            n.is_read = True
        db.session.commit()
