from celery import Celery
from flask import Flask
from config import LocalDevelopmentConfig
from models import *
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, hash_password
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from management.services_blueprint import services_bp
from management.professionals_pending_blueprint import professionals_pending_bp
from management.service_requests_blueprint import service_requests_bp
from management.customers_blueprint import customers_bp
from management.professionals_blueprint import professionals_bp
from management.customer_servicehistory_bp import service_request_hist_bp
from management.services_pros_bp import service_pros_details_bp
from management.professional_dashboard_bp import professional_dashboard_bluep
from management.submit_review import review_bp
from management.admin_search_bp import admin_bp
from management.customer_search_bp import customer_bp
from management.customer_summary import customer_sum_bp
from management.professsional_search import professional_search_bp
from management.professional_summary import professional_sum_bp


import redis
from flask_caching import Cache

def create_app():
    app = Flask(__name__, template_folder='frontend', static_folder='frontend',static_url_path='/static')
    app.config.from_object(LocalDevelopmentConfig)
    # app.config['CELERY_BROKER_URL'] = 'rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>?ssl_cert_reqs=required'
    # app.config['CELERY_RESULT_BACKEND'] = 'rediss://<USERNAME>:<PASSWORD>@<HOST>:<PORT>/0?ssl_cert_reqs=required'
    
    # Initialize database
    db.init_app(app)
    
    # Flask-Security setup
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    
    app.security = Security(app, datastore=datastore, register_blueprint=False)
    app.app_context().push()
    
    return app

app = create_app()

CORS(app, origins="*")

redis_client = redis.Redis(host='localhost',port=6379,db=0)
cache = Cache(app,config={'CACHE_TYPE':'redis','CACHE_REDIS':redis_client})

# redis_client = redis.Redis(host='localhost', port=6379, db=1)  # Flask Cache
# celery = Celery(__name__, broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')  # Celery



app.register_blueprint(services_bp,url_prefix='/api')
app.register_blueprint(professionals_pending_bp,url_prefix='/api')
app.register_blueprint(service_requests_bp, url_prefix='/api')
app.register_blueprint(customers_bp)
app.register_blueprint(professionals_bp)

app.register_blueprint(service_request_hist_bp, url_prefix='/api')
app.register_blueprint(service_pros_details_bp, url_prefix='/api')
app.register_blueprint(professional_dashboard_bluep)
app.register_blueprint(review_bp, url_prefix='/api')
app.register_blueprint(admin_bp)
app.register_blueprint(customer_sum_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(professional_sum_bp)
app.register_blueprint(professional_search_bp)

import create_initial_data
import routes

if __name__ == '__main__':
    app.run(debug=True)

