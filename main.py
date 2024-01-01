from flask import Flask,render_template,request,flash,redirect,url_for,session,send_file
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import secrets

app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'SECRETKEY'
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER']='D:\\Projects\\File_Sharing\\static\\uploaded_files'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email=db.Column(db.String(100),unique=True,nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


class Files(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    filename=db.Column(db.String(100),nullable=False)
    staticname=db.Column(db.String(100),unique=True,nullable=False)
    token=db.Column(db.String(100),unique=True,nullable=False)
    username=db.Column(db.String(100),nullable=False)

    def __repr__(self):
        return f'<Files {self.username}'

def login_required(fx):
    @wraps(fx)
    def new_method_instead_of_fx(*args,**kwargs):
        if(session.get('is_logged_in')):
            return fx(*args,**kwargs)
        else:
            return render_template('prompt.html',message="Access Denied")
    return new_method_instead_of_fx


def hash_string(text):
    hash_object = hashlib.sha256(text.encode())
    hashed_text = hash_object.hexdigest()[:6]  # Take first 6 characters of the hash
    return hashed_text

@app.route('/')
def index():
    return render_template('download.html')


@app.route('/upload',methods=["GET","POST"])
@login_required
def upload():
    if(request.method=="POST"):
        f=request.files['file']
        filename = secure_filename(f.filename)
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        staticname=f"{session['username']}_{current_datetime}.{filename.split('.')[-1]}"
        f.save(os.path.join('D:\\Projects\\File_Sharing\\static\\uploaded_files', staticname))
        token=secrets.token_urlsafe(6)
        print(token)
        file=Files(filename=filename,staticname=staticname,token=token,username=session['username'])
        db.session.add(file)
        db.session.commit()
    allFiles=Files.query.filter_by(username=session['username']).all()
    return render_template('upload.html',username=session['username'],allFiles=allFiles)
   


@app.route('/register',methods=["GET","POST"])
def register():
    if(request.method=="POST"):
        user=User(username=request.form['username'],email=request.form['email'],password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        return render_template('prompt.html',message="Successfully Registered")
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect('/login')

@app.route('/login',methods=["GET","POST"])
def login():
    if(request.method=="POST"):
        user=User.query.filter_by(username=request.form['username']).first()
        if(user==None):
            return render_template('prompt.html',message="User not found")
        elif(user.password!=request.form['password']):
            return render_template('prompt.html',message="Incorrect Password")
        else:
            session['is_logged_in']=True
            session['username']=user.username
            session['email']=user.email
            return redirect('/upload')
    return render_template('login.html')


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    file=Files.query.filter_by(id=id).first()
    os.remove(f"{app.config['UPLOAD_FOLDER']}//{file.staticname}")
    db.session.delete(file)
    db.session.commit()
    return redirect("/upload")

@app.route('/generatetoken/<int:id>')
@login_required
def generate_token(id):
    file=Files.query.filter_by(id=id).first()
    file.token=secrets.token_urlsafe(6)
    db.session.add(file)
    db.session.commit()
    return redirect("/upload")

@app.route('/download',methods=["GET","POST"])
def download():
    if(request.method=="POST"):
        file=Files.query.filter_by(token=request.form['token']).first()
        if(file==None):
            return render_template('prompt.html',message="Token Does Not Exist")
        filepath=f"{app.config['UPLOAD_FOLDER']}\\{file.staticname}"
        return send_file(filepath, as_attachment=True,download_name=file.filename)
    return render_template('download.html')


if __name__=='__main__':
    app.run(debug=True,port=8000)