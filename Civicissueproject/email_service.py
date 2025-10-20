import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv
from email_templates import get_complaint_notification_template, get_confirmation_email_template

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        
        # Admin email for escalations
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.admin_password = os.getenv('ADMIN_PASSWORD')
        
        # Department email mapping
        self.department_emails = {
            'Education': os.getenv('EDUCATION_EMAIL'),
            'Roads & Transport': os.getenv('ROADS_EMAIL'),
            'Electricity': os.getenv('ELECTRICITY_EMAIL'),
            'Health & Sanitation': os.getenv('SANITATION_EMAIL'),
            'Water Supply': os.getenv('WATER_SUPPLY_EMAIL'),
            'Other': self.sender_email  # Default to sender for now
        }
    
    def get_department_email(self, department):
        """Get the appropriate email for a department"""
        return self.department_emails.get(department, self.sender_email)
    
    def send_complaint_notification(self, complaint_data, complaint_id=None):
        """Send email notification to the appropriate department"""
        try:
            # Get department email
            department = complaint_data.get('department', '')
            recipient_email = self.get_department_email(department)
            
            if not recipient_email:
                print(f"No email configured for department: {department}")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"🚨 URGENT: New {department} Complaint #{complaint_id or 'TBD'} - Immediate Action Required | CityZen"
            
            # Create HTML content using enhanced template
            html_content = get_complaint_notification_template(complaint_data, complaint_id)
            
            # Create plain text version
            text_content = f"""
🚨 URGENT: NEW COMPLAINT NOTIFICATION - CITYZEN

Complaint ID: #{complaint_id or 'TBD'}
Department: {complaint_data.get('department', 'N/A')}
Priority: HIGH
Status: PENDING REVIEW
Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}

COMPLAINANT DETAILS:
===================
Name: {complaint_data.get('name', 'N/A')}
Phone: {complaint_data.get('phone', 'N/A')}

LOCATION DETAILS:
================
District: {complaint_data.get('district', 'N/A')}
Block: {complaint_data.get('block', 'N/A')}
Village: {complaint_data.get('village', 'N/A')}
Gram Panchayat: {complaint_data.get('gp', 'N/A')}
Landmark: {complaint_data.get('landmark', 'N/A')}
PIN Code: {complaint_data.get('pincode', 'N/A')}

COMPLAINT DESCRIPTION:
=====================
{complaint_data.get('complaint', 'No description provided.')}

REQUIRED ACTIONS:
================
✓ Acknowledge receipt within 2 hours
✓ Conduct initial assessment and field verification
✓ Assign appropriate personnel for resolution
✓ Update complaint status within 24-48 hours
✓ Contact complainant if additional information needed
✓ Ensure resolution within department SLA timeline

This is an automated notification from CityZen Digital Governance Platform.
Please login to the admin dashboard to view full details and take action.

Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            print(f"✅ Email notification sent successfully to {recipient_email} for {department} department")
            return True
            
        except Exception as e:
            print(f"❌ Error sending email notification: {str(e)}")
            return False
    
    def send_confirmation_email(self, complaint_data, complaint_id):
        """Send confirmation email to the complainant"""
        try:
            complainant_email = complaint_data.get('email')  # We might need to add email field to form
            if not complainant_email:
                # Skip sending confirmation if no email provided
                return True
            
            # Create confirmation message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = complainant_email
            msg['Subject'] = f"✅ Complaint #{complaint_id} Registered Successfully - CityZen"
            
            # Create confirmation email content using enhanced template
            confirmation_html = get_confirmation_email_template(complaint_data, complaint_id)
            
            # Create plain text version
            text_content = f"""
✅ COMPLAINT REGISTERED SUCCESSFULLY - CITYZEN

Dear {complaint_data.get('name', 'Citizen')},

Thank you for using CityZen to lodge your complaint. Your complaint has been successfully registered and forwarded to the concerned department.

Complaint ID: #{complaint_id}
Department: {complaint_data.get('department', 'N/A')}
Date Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}

WHAT HAPPENS NEXT:
- Your complaint has been forwarded to the {complaint_data.get('department', 'concerned')} department
- Department officials will review and take appropriate action
- You will receive SMS updates on your registered mobile number
- Track progress by logging into your CityZen account

Thank you for being an active citizen and helping us build a better community!

CityZen - Digital Governance Platform
            """
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(confirmation_html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, complainant_email, text)
            server.quit()
            
            print(f"✅ Confirmation email sent to {complainant_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending confirmation email: {str(e)}")
            return False
    
    def send_escalation_alert(self, complaint_data, complaint_id, days_pending=None):
        """Send escalation alert email to admin"""
        try:
            if not self.admin_email:
                print("No admin email configured for escalation alerts")
                return False
            
            # Create escalation message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = self.admin_email
            msg['Subject'] = f"🚨 URGENT ESCALATION ALERT: Complaint #{complaint_id} - Immediate Admin Intervention Required"
            
            # Create HTML content for escalation alert
            html_content = self.create_escalation_email_template(complaint_data, complaint_id, days_pending)
            
            # Create plain text version
            text_content = f"""
🚨 URGENT ESCALATION ALERT - CITYZEN ADMIN DASHBOARD

CRITICAL: Complaint Requires Immediate Admin Intervention

Complaint ID: #{complaint_id}
Status: ESCALATED
Priority: CRITICAL
Days Pending: {days_pending or 'Unknown'} days
Department: {complaint_data.get('department', 'N/A')}
Escalation Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}

COMPLAINANT DETAILS:
===================
Name: {complaint_data.get('name', 'N/A')}
Phone: {complaint_data.get('phone', 'N/A')}

LOCATION DETAILS:
================
District: {complaint_data.get('district', 'N/A')}
Block: {complaint_data.get('block', 'N/A')}
Village: {complaint_data.get('village', 'N/A')}
Landmark: {complaint_data.get('landmark', 'N/A')}
PIN Code: {complaint_data.get('pincode', 'N/A')}

COMPLAINT DESCRIPTION:
=====================
{complaint_data.get('complaint', 'No description provided.')}

ESCALATION REASON:
=================
This complaint has been pending for more than the acceptable timeframe and requires immediate administrative intervention.

IMMEDIATE ACTIONS REQUIRED:
==========================
✓ Review complaint status and department response
✓ Contact department head for explanation
✓ Assign additional resources if needed
✓ Provide direct oversight until resolution
✓ Update complainant on escalation status
✓ Set priority resolution timeline

This is an automated escalation alert from CityZen.
Please login to the admin dashboard immediately to address this critical issue.

Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}
            """
            
            # Attach parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email using admin credentials for escalations
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.admin_email, text)
            server.quit()
            
            print(f"🚨 ESCALATION ALERT sent successfully to {self.admin_email} for complaint #{complaint_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending escalation alert: {str(e)}")
            return False
    
    def create_escalation_email_template(self, complaint_data, complaint_id, days_pending=None):
        """Create escalation alert email template"""
        from datetime import datetime
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>URGENT: Escalation Alert - CityZen</title>
            <style>
                body {{
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 650px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(220, 53, 69, 0.2);
                    overflow: hidden;
                    border: 3px solid #dc3545;
                }}
                .header {{
                    background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                    color: white;
                    padding: 25px;
                    text-align: center;
                    position: relative;
                }}
                .header::before {{
                    content: '⚠️';
                    position: absolute;
                    top: 10px;
                    left: 20px;
                    font-size: 24px;
                    animation: blink 1s infinite;
                }}
                .header::after {{
                    content: '⚠️';
                    position: absolute;
                    top: 10px;
                    right: 20px;
                    font-size: 24px;
                    animation: blink 1s infinite;
                }}
                @keyframes blink {{
                    0%, 50% {{ opacity: 1; }}
                    51%, 100% {{ opacity: 0.3; }}
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .critical-alert {{
                    background: linear-gradient(90deg, #ff6b6b, #ee5a52);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-weight: 700;
                    font-size: 18px;
                    border-bottom: 3px solid #dc3545;
                    animation: pulse 2s infinite;
                }}
                @keyframes pulse {{
                    0% {{ background: linear-gradient(90deg, #ff6b6b, #ee5a52); }}
                    50% {{ background: linear-gradient(90deg, #dc3545, #c82333); }}
                    100% {{ background: linear-gradient(90deg, #ff6b6b, #ee5a52); }}
                }}
                .content {{
                    padding: 25px;
                }}
                .complaint-id {{
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    text-align: center;
                    margin: 20px 0;
                    font-weight: 700;
                    font-size: 20px;
                    border: 2px solid #a71e2a;
                }}
                .escalation-info {{
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    border: 2px solid #ffc107;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 6px solid #dc3545;
                }}
                .details-grid {{
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    margin-bottom: 10px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #e9ecef;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #6c757d;
                    width: 140px;
                    flex-shrink: 0;
                }}
                .detail-value {{
                    color: #212529;
                    font-weight: 500;
                }}
                .complaint-description {{
                    background: #ffffff;
                    border: 2px solid #dc3545;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    border-left: 6px solid #dc3545;
                }}
                .action-required {{
                    background: linear-gradient(135deg, #dc3545, #c82333);
                    color: white;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 25px 0;
                    text-align: center;
                }}
                .action-buttons {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-top: 20px;
                    flex-wrap: wrap;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    transition: all 0.3s ease;
                    border: 2px solid transparent;
                }}
                .btn-emergency {{
                    background: #ffffff;
                    color: #dc3545;
                    border-color: #ffffff;
                }}
                .btn-primary {{
                    background: #007bff;
                    color: white;
                }}
                .btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                }}
                .footer {{
                    background: #343a40;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .urgency-meter {{
                    background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
                    height: 8px;
                    border-radius: 4px;
                    margin: 15px 0;
                    position: relative;
                }}
                .urgency-indicator {{
                    position: absolute;
                    right: 0;
                    top: -5px;
                    width: 18px;
                    height: 18px;
                    background: #dc3545;
                    border-radius: 50%;
                    border: 3px solid white;
                    animation: urgent-pulse 1s infinite;
                }}
                @keyframes urgent-pulse {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.2); }}
                    100% {{ transform: scale(1); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 ESCALATION ALERT 🚨</h1>
                    <p>Immediate Administrative Intervention Required</p>
                </div>
                
                <div class="critical-alert">
                    ⚠️ CRITICAL: Complaint Has Been Escalated Due to Delayed Response ⚠️
                </div>
                
                <div class="content">
                    <div class="complaint-id">
                        ESCALATED COMPLAINT ID: #{complaint_id}
                    </div>
                    
                    <div class="escalation-info">
                        <h3 style="color: #856404; margin-top: 0;">📊 Escalation Summary</h3>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>Days Pending:</strong> {days_pending or 'Unknown'} days<br>
                                <strong>Department:</strong> {complaint_data.get('department', 'N/A')}<br>
                                <strong>Escalation Time:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}
                            </div>
                            <div>
                                <div class="urgency-meter">
                                    <div class="urgency-indicator"></div>
                                </div>
                                <small style="color: #856404;">Urgency: CRITICAL</small>
                            </div>
                        </div>
                    </div>
                    
                    <h3 style="color: #dc3545;">👤 Complainant Details</h3>
                    <div class="details-grid">
                        <div class="detail-row">
                            <div class="detail-label">Name:</div>
                            <div class="detail-value">{complaint_data.get('name', 'N/A')}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Phone:</div>
                            <div class="detail-value">{complaint_data.get('phone', 'N/A')}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">Location:</div>
                            <div class="detail-value">{complaint_data.get('village', '')}, {complaint_data.get('block', '')}, {complaint_data.get('district', '')}</div>
                        </div>
                        <div class="detail-row">
                            <div class="detail-label">PIN Code:</div>
                            <div class="detail-value">{complaint_data.get('pincode', 'N/A')}</div>
                        </div>
                    </div>
                    
                    <h3 style="color: #dc3545;">📝 Complaint Details</h3>
                    <div class="complaint-description">
                        <strong>Department:</strong> {complaint_data.get('department', 'N/A')}<br><br>
                        <strong>Description:</strong><br>
                        {complaint_data.get('complaint', 'No description provided.')}
                    </div>
                    
                    <div class="action-required">
                        <h3>⚡ IMMEDIATE ACTIONS REQUIRED</h3>
                        <ul style="text-align: left; margin: 15px 0;">
                            <li>Review complaint status and department response</li>
                            <li>Contact department head for immediate explanation</li>
                            <li>Assign additional resources if necessary</li>
                            <li>Provide direct administrative oversight</li>
                            <li>Set priority resolution timeline</li>
                            <li>Update complainant on escalation status</li>
                        </ul>
                        
                        <div class="action-buttons">
                            <a href="#" class="btn btn-emergency">🚨 Open Admin Dashboard</a>
                            <a href="#" class="btn btn-primary">📞 Contact Department</a>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>⚠️ CityZen Critical Alert System ⚠️</strong></p>
                    <p>This escalation requires immediate administrative attention</p>
                    <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_template