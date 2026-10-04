import os

basedir = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Normalize legacy postgres:// scheme to postgresql:// for SQLAlchemy 1.4+
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    default_db_path = os.path.join(basedir, 'skill_tracker.db')
    return f'sqlite:///{default_db_path}'

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'skill-tracker-saas-production-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Secure Cookie Configuration
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
