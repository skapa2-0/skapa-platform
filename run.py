from app import create_app, db
from app.models import User, ApiKey, EmailToken, UserPreferences, Notification, ActivityLog, SupportTicket, ApiUsageStats

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'ApiKey': ApiKey, 
        'EmailToken': EmailToken,
        'UserPreferences': UserPreferences,
        'Notification': Notification,
        'ActivityLog': ActivityLog,
        'SupportTicket': SupportTicket,
        'ApiUsageStats': ApiUsageStats
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 