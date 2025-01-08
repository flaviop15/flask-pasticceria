from app import app, db, User
from datetime import date

# Admin credentials
admin_credentials = {
    "username": "admin",
    "password": "12345678"
}

# Function to create and populate the database with initial data
def create_db():
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username=admin_credentials['username']).first():
        admin = User(username=admin_credentials['username'], password=admin_credentials['password'])
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        create_db()
    print("Database initialized successfully with admin user!")
