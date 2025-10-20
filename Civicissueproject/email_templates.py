"""
Email Templates for CityZen Complaint Management System
"""

def get_complaint_notification_template(complaint_data, complaint_id=None):
    """
    Enhanced professional email template for complaint notifications
    """
    from datetime import datetime
    
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Complaint Notification - CityZen</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                line-height: 1.6;
                color: #2c3e50;
                background-color: #f8f9fa;
            }}
            
            .email-container {{
                max-width: 650px;
                margin: 20px auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                overflow: hidden;
                border: 1px solid #e9ecef;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 25px;
                text-align: center;
                position: relative;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.05"/><circle cx="10" cy="60" r="1" fill="white" opacity="0.05"/><circle cx="90" cy="40" r="1" fill="white" opacity="0.05"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            }}
            
            .header h1 {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
                position: relative;
                z-index: 1;
            }}
            
            .header .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                position: relative;
                z-index: 1;
            }}
            
            .alert-banner {{
                background: linear-gradient(90deg, #ff6b6b, #ee5a52);
                color: white;
                padding: 15px 25px;
                text-align: center;
                font-weight: 600;
                border-bottom: 3px solid #dc3545;
            }}
            
            .content {{
                padding: 30px 25px;
            }}
            
            .complaint-id {{
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 25px;
                font-weight: 600;
                font-size: 18px;
            }}
            
            .priority-status {{
                display: flex;
                gap: 10px;
                justify-content: center;
                margin-bottom: 25px;
            }}
            
            .badge {{
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .badge-priority {{
                background: linear-gradient(45deg, #dc3545, #c82333);
                color: white;
                box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
            }}
            
            .badge-status {{
                background: linear-gradient(45deg, #ffc107, #e0a800);
                color: #212529;
                box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
            }}
            
            .section-header {{
                color: #495057;
                font-size: 20px;
                font-weight: 600;
                margin: 25px 0 15px 0;
                padding-bottom: 8px;
                border-bottom: 2px solid #667eea;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .details-grid {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border: 1px solid #dee2e6;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
            
            .detail-row {{
                display: flex;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }}
            
            .detail-row:last-child {{
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }}
            
            .detail-label {{
                font-weight: 600;
                color: #6c757d;
                width: 140px;
                flex-shrink: 0;
                font-size: 14px;
            }}
            
            .detail-value {{
                color: #212529;
                font-weight: 500;
                flex-grow: 1;
            }}
            
            .complaint-description {{
                background: #ffffff;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                font-style: italic;
                line-height: 1.7;
                border-left: 4px solid #667eea;
                position: relative;
            }}
            
            .complaint-description::before {{
                content: '"';
                position: absolute;
                top: -10px;
                left: 10px;
                font-size: 40px;
                color: #667eea;
                font-family: serif;
            }}
            
            .action-section {{
                background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                border-radius: 10px;
                padding: 25px;
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
                text-align: center;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                font-size: 14px;
                min-width: 140px;
            }}
            
            .btn-primary {{
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
            }}
            
            .btn-success {{
                background: linear-gradient(135deg, #28a745, #1e7e34);
                color: white;
                box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            }}
            
            .btn-warning {{
                background: linear-gradient(135deg, #ffc107, #e0a800);
                color: #212529;
                box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);
            }}
            
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
            }}
            
            .next-steps {{
                background: linear-gradient(135deg, #e8f5e8, #d4edda);
                border: 1px solid #c3e6cb;
                border-radius: 10px;
                padding: 20px;
                margin: 25px 0;
                border-left: 4px solid #28a745;
            }}
            
            .next-steps h4 {{
                color: #155724;
                margin-bottom: 15px;
                font-size: 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .next-steps ul {{
                list-style: none;
                margin: 0;
                padding: 0;
            }}
            
            .next-steps li {{
                color: #155724;
                margin-bottom: 8px;
                padding-left: 25px;
                position: relative;
            }}
            
            .next-steps li::before {{
                content: '✓';
                position: absolute;
                left: 0;
                color: #28a745;
                font-weight: bold;
            }}
            
            .footer {{
                background: linear-gradient(135deg, #343a40, #495057);
                color: #ffffff;
                text-align: center;
                padding: 25px;
            }}
            
            .footer p {{
                margin: 5px 0;
                opacity: 0.9;
            }}
            
            .footer .main-title {{
                font-weight: 700;
                font-size: 16px;
                margin-bottom: 10px;
            }}
            
            .timestamp {{
                background: rgba(255, 255, 255, 0.1);
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                margin-top: 10px;
                display: inline-block;
            }}
            
            @media (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                }}
                
                .content {{
                    padding: 20px 15px;
                }}
                
                .action-buttons {{
                    flex-direction: column;
                    align-items: center;
                }}
                
                .btn {{
                    width: 100%;
                    max-width: 200px;
                }}
                
                .detail-row {{
                    flex-direction: column;
                    gap: 5px;
                }}
                
                .detail-label {{
                    width: auto;
                    font-weight: 700;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🏛️ CityZen</h1>
                <div class="subtitle">Digital Governance & Citizen Services Platform</div>
            </div>
            
            <div class="alert-banner">
                🚨 URGENT: New Complaint Requires Immediate Attention
            </div>
            
            <div class="content">
                {f'<div class="complaint-id">Complaint ID: #{complaint_id}</div>' if complaint_id else ''}
                
                <div class="priority-status">
                    <span class="badge badge-priority">🔥 High Priority</span>
                    <span class="badge badge-status">⏳ Pending Review</span>
                </div>
                
                <h2 class="section-header">
                    📋 Complaint Overview
                </h2>
                
                <div class="details-grid">
                    <div class="detail-row">
                        <div class="detail-label">📅 Submitted:</div>
                        <div class="detail-value">{datetime.now().strftime('%A, %B %d, %Y at %I:%M %p IST')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">🏢 Department:</div>
                        <div class="detail-value"><strong>{complaint_data.get('department', 'N/A')}</strong></div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">👤 Complainant:</div>
                        <div class="detail-value">{complaint_data.get('name', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">📱 Contact:</div>
                        <div class="detail-value">{complaint_data.get('phone', 'N/A')}</div>
                    </div>
                </div>
                
                <h3 class="section-header">
                    📍 Location Details
                </h3>
                
                <div class="details-grid">
                    <div class="detail-row">
                        <div class="detail-label">🌍 District:</div>
                        <div class="detail-value">{complaint_data.get('district', 'N/A').title()}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">🏘️ Block:</div>
                        <div class="detail-value">{complaint_data.get('block', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">🏡 Village:</div>
                        <div class="detail-value">{complaint_data.get('village', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">🏛️ Gram Panchayat:</div>
                        <div class="detail-value">{complaint_data.get('gp', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">📍 Landmark:</div>
                        <div class="detail-value">{complaint_data.get('landmark', 'N/A')}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">📮 PIN Code:</div>
                        <div class="detail-value">{complaint_data.get('pincode', 'N/A')}</div>
                    </div>
                </div>
                
                <h3 class="section-header">
                    💬 Complaint Description
                </h3>
                
                <div class="complaint-description">
                    {complaint_data.get('complaint', 'No description provided.')}
                </div>
                
                <div class="action-section">
                    <h3 style="color: #0056b3; margin-bottom: 15px;">⚡ Immediate Action Required</h3>
                    <p style="margin-bottom: 20px; color: #495057;">This complaint needs your urgent attention. Please take appropriate action within the prescribed timeline.</p>
                    
                    <div class="action-buttons">
                        <a href="#" class="btn btn-primary">🔍 Open Dashboard</a>
                        <a href="#" class="btn btn-success">✅ Accept & Resolve</a>
                        <a href="#" class="btn btn-warning">👥 Assign Team</a>
                    </div>
                </div>
                
                <div class="next-steps">
                    <h4>📋 Required Next Steps:</h4>
                    <ul>
                        <li>Acknowledge receipt within 2 hours</li>
                        <li>Conduct initial assessment and field verification</li>
                        <li>Assign appropriate personnel for resolution</li>
                        <li>Update complaint status within 24-48 hours</li>
                        <li>Contact complainant if additional information is needed</li>
                        <li>Ensure resolution within department SLA timeline</li>
                    </ul>
                </div>
            </div>
            
            <div class="footer">
                <p class="main-title">🏛️ CityZen - Digital Governance Platform</p>
                <p>📧 This is an automated notification • Please do not reply directly to this email</p>
                <p>🔒 Confidential: This information is intended only for authorized department personnel</p>
                <div class="timestamp">
                    🕒 Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p IST')}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return template


def get_confirmation_email_template(complaint_data, complaint_id):
    """
    Enhanced confirmation email template for complainants
    """
    from datetime import datetime
    
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Complaint Registered Successfully - CityZen</title>
        <style>
            body {{
                font-family: 'Segoe UI', system-ui, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .success-header {{
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .content {{
                padding: 30px;
            }}
            .complaint-id-box {{
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
                font-weight: 600;
                font-size: 18px;
            }}
            .info-box {{
                background: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .footer {{
                background: #343a40;
                color: white;
                padding: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-header">
                <h1>✅ Complaint Registered Successfully!</h1>
                <p>Thank you for using CityZen digital platform</p>
            </div>
            
            <div class="content">
                <p>Dear <strong>{complaint_data.get('name', 'Citizen')}</strong>,</p>
                
                <p>Your complaint has been successfully registered in our system and forwarded to the concerned department for immediate action.</p>
                
                <div class="complaint-id-box">
                    Your Complaint ID: <strong>#{complaint_id}</strong>
                </div>
                
                <div class="info-box">
                    <h3>📋 Complaint Summary:</h3>
                    <p><strong>Department:</strong> {complaint_data.get('department', 'N/A')}</p>
                    <p><strong>Location:</strong> {complaint_data.get('village', '')}, {complaint_data.get('block', '')}, {complaint_data.get('district', '')}</p>
                    <p><strong>Submitted on:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                <h3>🔄 What happens next?</h3>
                <ul>
                    <li>Your complaint has been automatically forwarded to the {complaint_data.get('department', 'concerned')} department</li>
                    <li>Department officials will review and take appropriate action</li>
                    <li>You will receive SMS updates on your registered mobile number</li>
                    <li>You can track progress by logging into your CityZen account</li>
                </ul>
                
                <div class="info-box">
                    <h4>📱 Track Your Complaint:</h4>
                    <p>Login to your CityZen account anytime to check the status of your complaint using ID: <strong>#{complaint_id}</strong></p>
                </div>
                
                <p>Thank you for being an active citizen and helping us build a better community!</p>
            </div>
            
            <div class="footer">
                <p><strong>CityZen - Digital Governance Platform</strong></p>
                <p>Making governance accessible, transparent, and efficient</p>
            </div>
        </div>
    </body>
    </html>
    """
    return template