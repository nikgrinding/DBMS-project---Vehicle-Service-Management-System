from flask import Flask
from models import db
from routes import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Nik123%40chennai@127.0.0.1:3306/vehicle_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']= 'thisisasecretkey'

db.init_app(app)

# Create the database tables if they don't exist
with app.app_context():
    #db.drop_all()
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
