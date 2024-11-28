class Config():
    DEBUG = False
    SQL_ALCHEMY_TRACK_MODIFICATIONS = False
    
class LocalDevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    DEBUG = True
    FLASK_ENV = 'development'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'thisisthesecretsaltthatshouldbekeptsecret'
    SECRET_KEY = "thisisthesecretkeythatshouldbekepthidden"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    
    WTF_CSRF_ENABLED = False