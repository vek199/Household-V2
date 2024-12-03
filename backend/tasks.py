import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import db, Service, ServiceRequest, Review, User
import os
from io import StringIO
from datetime import datetime
from celery_config import celery
from app import app
from models import *
import csv


@celery.task
def generate_monthly_report():
    with app.app_context():
        current_month = datetime.now().strftime('%B')
        current_year = datetime.now().year

        users = User.query.all()
        for user in users:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Monthly Activity Report</title>
            </head>
            <body>
                <p>{user.username}</p>
                <p>{current_month} {current_year}</p>
            </body>
            </html>"""
            send_email(user.email, 'Monthly Activity Report', html_content)


def send_email(to_email, subject, html_content):
    from_email = 'household@gmail.com'
    msg = MIMEMultipart('alternative')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject  # Use the 'subject' argument

    part1 = MIMEText(html_content, 'html')
    msg.attach(part1)

    smtp_server = 'localhost'
    smtp_port = 1025
    
    # smtp_server = 'smtp.gmail.com'
    # smtp_port = 587
    # ubuntun 20.04

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.sendmail(from_email, to_email, msg.as_string())

@celery.task
def export_service_details_as_csv():
    try:
        # Fetch all the records from the database
        users = User.query.all()
        roles = Role.query.all()
        customer_profiles = CustomerProfile.query.all()
        professionals = Professional.query.all()
        services = Service.query.all()
        service_requests = ServiceRequest.query.all()
        reviews = Review.query.all()
        blocks = Block.query.all()

        # Create an in-memory CSV file
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)

        # Add headers for each table's data
        csv_writer.writerow(['Users'])
        csv_writer.writerow(['ID', 'Username', 'Phone Number', 'Email', 'Active', 'Roles'])
        for user in users:
            csv_writer.writerow([user.id, user.username, user.phone_number, user.email, user.active, ", ".join([role.name for role in user.roles])])

        csv_writer.writerow(['Roles'])
        csv_writer.writerow(['ID', 'Name', 'Description'])
        for role in roles:
            csv_writer.writerow([role.id, role.name, role.description])

        csv_writer.writerow(['CustomerProfiles'])
        csv_writer.writerow(['ID', 'User ID', 'Address', 'Location Pin Code', 'Blocked', 'Preferred Services'])
        for profile in customer_profiles:
            csv_writer.writerow([profile.id, profile.user_id, profile.address, profile.location_pin_code, profile.blocked, profile.preferred_services])

        csv_writer.writerow(['Professionals'])
        csv_writer.writerow(['ID', 'User ID', 'Service Type', 'Experience', 'Description', 'Verified', 'Blocked', 'Average Rating'])
        for professional in professionals:
            csv_writer.writerow([professional.id, professional.user_id, professional.service_type, professional.experience, professional.description, professional.verified, professional.blocked, professional.average_rating])

        csv_writer.writerow(['Services'])
        csv_writer.writerow(['ID', 'Name', 'Price', 'Time Required', 'Description'])
        for service in services:
            csv_writer.writerow([service.id, service.name, service.price, service.time_required, service.description])

        csv_writer.writerow(['ServiceRequests'])
        csv_writer.writerow(['ID', 'Service ID', 'Customer ID', 'Professional ID', 'Date of Request', 'Service Status', 'Remarks', 'Date Closed'])
        for request in service_requests:
            csv_writer.writerow([request.id, request.service_id, request.customer_id, request.professional_id, request.date_of_request, request.service_status, request.remarks, request.date_closed])

        csv_writer.writerow(['Reviews'])
        csv_writer.writerow(['ID', 'Service Request ID', 'Reviewer ID', 'Reviewee ID', 'Rating', 'Review', 'Timestamp'])
        for review in reviews:
            csv_writer.writerow([review.id, review.service_request_id, review.reviewer_id, review.reviewee_id, review.rating, review.review, review.timestamp])

        csv_writer.writerow(['Blocks'])
        csv_writer.writerow(['ID', 'Blocked User ID'])
        for block in blocks:
            csv_writer.writerow([block.id, block.blocked_user_id])

        # Get the path to store the CSV file
        base_dir = os.path.abspath(os.path.dirname(__file__))
        csv_file_path = os.path.join(base_dir, 'backend/csv', f"service_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")

        # Create the 'csv' directory if it doesn't exist
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

        # Write the CSV data to the file
        with open(csv_file_path, 'w') as csv_file:
            csv_file.write(csv_buffer.getvalue())

        # Return the file path (or any other relevant result)
        return csv_file_path

    except Exception as e:
        return str(e)

@celery.task
def daily_reminders():
    with app.app_context():
        users = User.query.all()
        for user in users:
            email_content = f"""
            <html>
            <body>
                <p>Hi {user.username},</p>
                <p>Your task:</p>
                <p><strong>Daily Reminder</strong></p>
                <p>Kindly consider ASAP.</p>
                <p>Thanks!</p>
            </body>
            </html>
            """
            send_email(user.email, 'Daily Reminder', email_content)

if __name__ == '__main__':
    from tasks import celery
    celery.start()
