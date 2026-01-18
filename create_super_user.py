from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # 1. Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Admin user already exists!")
    else:
        # 2. Create the Super User
        new_admin = User(username='admin', role='ADMIN')
        new_admin.set_password('atomicadmin0987') # <--- CHANGE THIS PASSWORD LATER
        
        db.session.add(new_admin)
        db.session.commit()
        print("Success! Created user: 'admin' with password: 'atomicadmin0987'")