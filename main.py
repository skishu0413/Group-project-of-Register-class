import csv
import xlrd, os
import urllib.request
from flask import render_template, flash, redirect, url_for, request, Flask
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import Form, StringField, IntegerField, SelectField, TextField, PasswordField, validators, SubmitField
from wtforms.validators import ValidationError, DataRequired, EqualTo, Required
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
import getpass, pymysql, sys
from flask_mail import Mail, Message

# Login form (subclassed from FlaskForm)
class LoginForm(FlaskForm):
    username = TextField('Username', validators=[DataRequired()])
    password = TextField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')
class AddUserForm(FlaskForm):
    username = TextField('Username', validators=[DataRequired()])
    password = TextField('Password', validators=[DataRequired()])
    role = TextField('Role')
    first_name = TextField('First Name', validators=[DataRequired()])
    last_name = TextField('Last Name', validators=[DataRequired()])
    grade  = TextField('Grade', validators=[DataRequired()])
    email_address = TextField('E-mail Address', validators=[DataRequired()])
    submit = SubmitField('Add User')
class ClassRegisterForm(FlaskForm):
    subjects  = [('1', 'ACC'), ('2', 'ANT'), ('3', 'ART'), ('4', 'BIO'), ('5', 'CHE'), ('6', 'CHI'), ('7', 'CMD'), ('8', 'COM'), ('9', 'CSC'), ('10', 'CSP'), ('11', 'CTR'), ('12', 'DSC'), ('13', 'ECO'), ('14', 'EDF'), ('15', 'EDL'), ('16', 'EDU'), ('17', 'EGR'), ('18', 'ENG'), ('19', 'ENV'), ('20', 'ESC'), ('21', 'ESL'), ('22', 'EVE'), ('23', 'EXS'), ('24', 'FIN'), ('25', 'FRE'), ('26', 'GEO'), ('27', 'GER'), ('28', 'HIS'), ('29', 'HLS'), ('30', 'HON'), ('31', 'HSC'), ('32', 'IDS'), ('33', 'ILS'), ('34', 'INQ'), ('35', 'ITA'), ('36', 'JRN'), ('37', 'JST'), ('38', 'LAT'), ('39', 'LIT'), ('40', 'MAR'), ('41', 'MAT'), ('42', 'MBA'), ('43', 'MDS'), ('44', 'MFT'), ('45', 'MGT'), ('46', 'MIS'), ('47', 'MKT'), ('48', 'MUS'), ('49', 'NUR'), ('50', 'PCH'), ('51', 'PHI'), ('52', 'PHY'), ('53', 'PSC'), ('54', 'PSY'), ('55', 'RDG'), ('56', 'REC'), ('57', 'RSP'), ('58', 'SCE'), ('59', 'SED'), ('60', 'SHE'), ('61', 'SMT'), ('62', 'SOC'), ('63', 'SPA'), ('64', 'SWK'), ('65', 'THR'), ('66', 'TSL'), ('67', 'WDBL'), ('68', 'WLL'), ('69', 'WMS')]
    subject  = SelectField('Select the subject', choices = subjects, validators=[DataRequired()])
    course_number = TextField('Enter the course number', validators=[DataRequired()])
    submit = SubmitField('Search')

# User class, subclassed from UserMixin for convenience.  UserMixin
# provides attributes to manage user (e.g. authenticated).  The User
# class defines a "role" attribute that represents the user role (e.g.  Regular
# user or admin)
class User(UserMixin):
    def __init__(self, username, password, role):
        self.id = username
        self.classes = []
        self.waitlists = []
        self.waitlistsDict = {}
        self.classesDict = {}
        # hash the password and output it to stderr
        self.pass_hash = generate_password_hash(password)
        print(self.pass_hash, file=sys.stderr)
        self.role = role
# creating the Flask app object and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a hard to guess string'
bootstrap = Bootstrap(app)
moment = Moment(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'



app.config.update(
        MAIL_SERVER = 'smtp.gmail.com',
        MAIL_PORT = 465,
        MAIL_USE_TLS = False,
        MAIL_USE_SSL = True, 
        MAIL_USERNAME = 'timross330@gmail.com',
        MAIL_PASSWORD = 'venice72',
        MAIL_DEFAULT_SENDER = ('Tim Ross', 'timross330@gmail.com'),
        SECRET_KEY = 'some secret key for CSRF')
mail = Mail(app)
moment = Moment(app)

# Our mock database of user objects, stored as a dictionary, where the
# key is the user id, and the value is the User object.  Typically, these
# would need
user_db = {'u': User('u', 'u', 'user'), 'a': User('a', 'a', 'admin')}
# Returns True if logged in user has "admin" role, False otherwise.
def is_admin():
    if current_user:
        if current_user.role == 'Admin':
            return True
        else:
            return False
    else:
        print('User not authenticated.', file=sys.stderr)
# Login manager uses this function to manage user sessions.
# Function does a lookup by id and returns the User object if
# it exists, None otherwise.
@login_manager.user_loader
def load_user(id):
    user_data = getUserData(id)
    user = User(user_data[0][0], user_data[0][1], user_data[0][2])
    return user
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', name=current_user.id)
# This mimics a situation where a non-admin user attempts to access
# an admin-only area.  @login_required ensures that only authenticated
# users may access this route.
@app.route('/admin_only')
@login_required
def admin_only():
    # determine if current user is admin
    if is_admin():
        return render_template('admin.html', message="I am admin.")
    else:
        return render_template('unauthorized.html')
g = [1,2,3,4,5,6,7,8,9]
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    app.db = None
    if not app.db:
        app.db = pymysql.connect('35.231.242.89', 'project', 'a' , 'classes_list')
    c = app.db.cursor()

    users_directory = []
    c.execute('SELECT * FROM users')
    users_directory=c.fetchall()
    print('users: ' + str(users_directory))
    global g
    if is_admin():
        form = AddUserForm()
        print('yo', file=sys.stderr)
    else:
        return render_template('unauthorized.html')
    if form.validate_on_submit():
        user_db[form.username.data] = User(form.username.data, form.password.data, form.role.data)
        username = form.username.data
        password = form.password.data
        role = form.role.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        grade = form.grade.data
        email_address = form.email_address.data
        app.db = None
        if not app.db:
            app.db = pymysql.connect('35.231.242.89', 'project', 'a' , 'classes_list')
        c = app.db.cursor()
        print('INSERT INTO users (username, password, role, first_name, last_name, grade, email_address) VALUES (\'' + username + '\', \'' + password + '\', \'' + role + '\', \'' + first_name + '\', \'' + last_name + '\', \'' + grade + '\', \'' + email_address + '\')')
        c.execute('INSERT INTO users (username, password, role, first_name, last_name, grade, email_address) VALUES (\'' + username + '\', \'' + password + '\', \'' + role + '\', \'' + first_name + '\', \'' + last_name + '\', \'' + grade + '\', \'' + email_address + '\')')
        app.db.commit()
    return render_template('adduser.html', form=form, users_directory=users_directory)





    return render_template('adduser.html', form=form)

@app.route('/success')
def success():
    return render_template('success.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    # display the login form
    form = LoginForm()
    if form.validate_on_submit():
        print(form.username.data)
        user_data = getUserData(form.username.data)
        if user_data == False:
            return redirect(url_for('index'))
        #user = user_db[form.username.data]
        user = User(user_data[0][0], user_data[0][1], user_data[0][2])
        # validate user
        # valid_password = check_password_hash(user_data[0][1], form.password.data)
        if user is None or user_data[0][1] != form.password.data:
            print('Invalid username or password', file=sys.stderr)
            redirect(url_for('index'))
        else:
            login_user(user)
            return redirect("/success")
    return render_template('login.html', title='Sign In', form=form)
# logging out is managed by login manager
# Log out option appears on the navbar only after a user logs on
# successfully (see lines 25-29 of templates/base.html )
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

class sClass(UserMixin):
    def __init__(self, className, currentEnrollment, maxEnrollment, currentWaitlist, maxWaitlist):
        self.className = className
        self.currentEnrollment = currentEnrollment
        self.maxEnrollment = maxEnrollment
        self.currentWaitlist = currentWaitlist
        self.maxWaitlist = maxWaitlist
class_db = {'1': sClass('Anthroplogy', 0, 3, 0, 5), '2': sClass('History', 0, 3, 0, 5), '3': sClass('Calculus', 0, 3, 0, 5)}

g = [[1,2,3,4,5,6,7,8,9],[1,2,3,4,5,6,7,8,9]]

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = ClassRegisterForm()
    if form.validate_on_submit():
        desired_course_number = form.course_number.data
        desired_subject = dict(form.subject.choices).get(form.subject.data)
        print(desired_subject, desired_course_number)
        results = get_matches(desired_subject, desired_course_number)
        return render_template('search.html', classes_result = results,  form=ClassRegisterForm())
    return render_template('search.html', form=form)
@app.route('/class-register', methods=['GET', 'POST'])
@login_required
def classregister():
    global g
    if not app.db:
        connect_db()
    c = app.db.cursor()
    username = current_user.id
    c.execute('SELECT class_1, class_2, class_3 FROM users WHERE username = \'' + username + '\'')
    current_waitlists = c.fetchall()[0]
    c.execute('SELECT watchlist_1, watchlist_2, watchlist_3 from users WHERE username = \'' + username + '\'')
    current_watchlists = c.fetchall()[0]
    list_of_watchlists = []
    for i in current_watchlists:
        if i == None or i == 'NULL':
            pass
        else:
            c.execute('SELECT * FROM classes WHERE crn = \'' + i + '\'')
            watchlist_single = list(c.fetchall()[0])
            list_of_watchlists.append(watchlist_single)
    print("watchlists:" + str(list_of_watchlists))
    g = []
    for i in current_waitlists:
        print(i)
        if i == None or i == 'NULL':
            pass
        else:
            c.execute('SELECT * from classes WHERE crn = \'' + i + '\'')
            wait_single = list(c.fetchall()[0])
            c.execute('SELECT student_1, student_2, student_3 from classes where crn = \'' + i + '\'')
            students = c.fetchall()
            m = 0
            for i in list(students[0]):
                m = m + 1
                if i == username:
                    print(m)
                    wait_single.append(m)
                    print(wait_single)
            g.append(wait_single)

    if is_student():
        form = ClassRegisterForm()
    if is_admin():
        return redirect("/search")
    print(current_waitlists)

    if form.validate_on_submit():
        desired_course_number = form.course_number.data
        desired_subject = dict(form.subject.choices).get(form.subject.data)
        print(desired_subject, desired_course_number)
        results = get_matches(desired_subject, desired_course_number)
    else:
        return render_template('class-register.html',  current_waitlists = g, list_of_watchlists = list_of_watchlists, form=form)
    return render_template('class-register.html', list_of_watchlists = list_of_watchlists, current_waitlists = g, classes_result = results,  form=form)

def is_student():
    g = [[1,2,3,4,5,6,7,8,9],[1,2,3,4,5,6,7,8,9]]
    if current_user:
        if current_user.role == 'Student':
            return True
        else:
            return False
    else:
        print('User not authenticated.', file=sys.stderr)

app.db = None
def connect_db():
    if not app.db:
        app.db = pymysql.connect('35.231.242.89', 'project', 'a' , 'classes_list')
    else:
        print('Connected!', file=sys.stderr)

@app.route('/view')
def view():
    get_subjects()
    if not app.db:
        connect_db()
    c = app.db.cursor()
    c.execute('SELECT DISTINCT subject from classes')
    cities_list = c.fetchall()
    return render_template('view.html', cities_result = cities_list)

def get_matches(sub, num):
    if not app.db:
        connect_db()
    c = app.db.cursor()
    print('SELECT * FROM classes WHERE subject = \'' + sub + ' \' AND number = \'' + num+ '\'')
    c.execute('SELECT * FROM classes WHERE subject = \'' + sub + '\' AND number = \'' + num+ '\'')
    matches = c.fetchall()
    return matches

@app.route("/test", methods=['GET', 'POST'])
def test():
    print(request.method)
    if request.method == 'POST':
        class_to_add = list(request.form.keys())[0][:5]
        username = current_user.id
        app.db = None
        if not app.db:
            app.db = pymysql.connect('35.231.242.89', 'project', 'a' , 'classes_list')
        c = app.db.cursor()
        c.execute('SELECT class_amount from users WHERE username = \'' + username + '\'')
        class_amount = c.fetchall()[0][0]
        c.execute('SELECT class_1, class_2, class_3 FROM users WHERE username = \'' + username + '\'')
        current_classes = c.fetchall()[0]
        c.execute('SELECT wait_current from classes WHERE crn = \'' + class_to_add + '\'')
        current_wait = c.fetchall()[0][0]
        c.execute('SELECT current_enrollment from classes where crn = \'' + class_to_add + '\'')
        current_enrollment = c.fetchall()[0][0]
        c.execute('SELECT max_enrollment from classes where crn = \'' + class_to_add + '\'')
        max_enrollment = c.fetchall()[0][0]
        print(max_enrollment, current_enrollment)
        if current_enrollment >= max_enrollment and class_amount < 3 and class_to_add not in current_classes and current_wait < 3:
            c.execute('SELECT grade from users where username = \'' + username + '\'')
            current_user_grade = list(c.fetchall()[0])[0]
            print(current_user_grade)
            if current_user_grade == 'Senior':
                current_user_grade = 1
            elif current_user_grade == 'Junior':
                current_user_grade = 2
            elif current_user_grade == 'Sophomore' or 'Sophmore':
                current_user_grade = 3
            elif current_user_grade == 'Freshman':
                current_user_grade = 4
            print(current_user_grade)
            c.execute('SELECT student_1, student_2, student_3 from classes where crn = \'' + class_to_add + '\'')
            students = c.fetchall()
            m = 0
            p = 0
            for i in list(students[0]):
                m = m + 1
                print(i)
                if i != 'NULL' and m < 3 and i != None:
                    c.execute('SELECT grade from users where username = \'' + i + '\'')
                    student_grade = list(c.fetchall()[0])[0]
                    if student_grade == 'Senior':
                        student_grade = 1 
                    elif student_grade == 'Junior':
                        student_grade = 2 
                    elif student_grade == 'Sophomore' or 'Sophmore':
                        student_grade = 3
                    elif student_grade == 'Freshman':
                         student_grade = 4
                    print(student_grade)
                    if int(current_user_grade) < student_grade:
                        print("Current user is higher than " +  i)
                        c.execute('UPDATE classes SET student_' + str(m+1) + ' = \'' + i + '\' WHERE crn = \'' + class_to_add + '\'') 
                        c.execute('UPDATE classes SET student_' + str(m) + ' = \'' + username + '\' WHERE crn = \'' + class_to_add + '\'')
                        app.db.commit()
                        p = 1
                        m = 3 

            class_amount = class_amount + 1
            current_wait = current_wait + 1
            slot  = 'class_' + str(class_amount)
            print('UPDATE users SET \'' + slot + '\' = \'' + class_to_add + '\' WHERE username = \'' + username + '\'')
            c.execute('UPDATE users SET ' + slot + ' = \'' + class_to_add + '\' WHERE username = \'' + username + '\'')
            c.execute('UPDATE users SET class_amount = ' + str(class_amount) + ' WHERE username = \'' + username + '\'')
            if p == 0:
                c.execute('UPDATE classes SET student_' + str(current_wait) + ' = \'' + username + '\' WHERE crn = \'' + class_to_add + '\'')
                print('hey')
            c.execute('UPDATE classes SET wait_current = ' + str(current_wait) + ' WHERE crn = \'' + class_to_add + '\'')
            app.db.commit()
            cities_list = c.fetchall()
            message_text = "You have successfully joined this waitlist"
            return render_template('success.html', message=message_text)
        elif current_enrollment < max_enrollment:
            message_text = "Error: This class is not full"
            return render_template('error.html', message=message_text) 
        elif class_amount >= 3:
            message_text = "Error: You have reached the waitlist limit"
            return render_template('error.html', message=message_text) 
        elif class_to_add in current_classes:
            message_text = "Error: You are already on this waitlist"
            return render_template('error.html', message=message_text) 
        elif current_wait >= 3:
            message_text = "Error: This waitlist is full"
            return render_template('error.html', message=message_text) 

def getUserData(username):
    if not app.db:
        connect_db()
    c = app.db.cursor()
    print('SELECT * FROM users WHERE username = \'' + username + '\'')
    c.execute('SELECT * FROM users WHERE username = \'' + username + '\'')
    match = c.fetchall()
    print(len(match))
    if len(match) > 0:
        return match
    else:
        return False

@app.route('/drive', methods=['GET', 'POST'])
@login_required
def drive():
    if not app.db:
        connect_db()
    c = app.db.cursor()
    username = current_user.id
    c.execute('SELECT class_1, class_2, class_3, class_4, class_5, class_6, class_7, class_8, class_9  FROM users WHERE username = \'' + username + '\'')
    current_waitlists = c.fetchall()[0]
    g = []
    for i in current_waitlists:
        print(i)
        if i == None:
            pass
        else:
            c.execute('SELECT * from classes WHERE crn = \'' + i + '\'')
            g.append(list(c.fetchall()[0]))
    y = [1, 2, 3]
    if is_student():
        form = ClassRegisterForm()
    else:
        return render_template('unauthorized.html')
    print(current_waitlists)
    if form.validate_on_submit():
        desired_course_number = form.course_number.data
        desired_subject = dict(form.subject.choices).get(form.subject.data)
        print(desired_subject, desired_course_number)
        results = get_matches(desired_subject, desired_course_number)
    else:
        return render_template('class-register.html',  form=form)
    return render_template('drive.html', cities_result = g, form=form)

@app.route('/changes', methods=['GET', 'POST'])
def changes():
    url = 'https://docs.google.com/spreadsheets/d/1rAnb2fzjpapSPKePSe2SWYPxZsIFDhrv/export?format=xlsx'
    urllib.request.urlretrieve(url,'schedule.xlsx')
    wb = xlrd.open_workbook('schedule.xlsx')
    sheet = wb.sheet_by_index(0)
    app.db = None
    if not app.db:
        connect_db()
    c = app.db.cursor()
    c.execute('SELECT crn, subject, number, section, class_name, days, time, professor_name, class_type, current_enrollment, max_enrollment from classes')
    all_classes = c.fetchall()
    print(all_classes)
    courses_to_add = []
    courses_to_remove = []
    x = []
    for i in range(len(all_classes)):
        if all_classes[i][0] not in x:
            x.append(all_classes[i][0])
    w = []
    for i in range(1, sheet.nrows):
        if sheet.row_values(i)[0] not in w:
            u = str(int(sheet.row_values(i)[0]))
            w.append(u)
    for i in w:
        if i in x:
            pass
        if i not in x:
            courses_to_add.append(i)
    for i in x:
        if i in w:
            pass
        if i not in w:
            courses_to_remove.append(i)
    print(courses_to_add)
    for i in courses_to_add:
        for j in range(sheet.nrows):
            if type(sheet.row_values(j)[0]) == float:
                u = str(int(sheet.row_values(j)[0]))
            else:
                u = str(sheet.row_values(j)[0])
            if u == i:
                h = sheet.row_values(j)
                if not h[5]:
                    h[5] = 'NULL'
        if not app.db:
            connect_db()
        c = app.db.cursor()
        c.execute('INSERT INTO classes (crn, subject, number, section, class_name, days, time, professor_name, class_type, max_enrollment, current_enrollment, wait_max, wait_current, student_1, student_2, student_3) VALUES (' + str(int(h[0])) + ', \'' + h[1] + '\', \'' + str(int(h[2])) + '\', \'' + h[3] + '\', \'' + h[4][:16] + '\', \'' + str(h[5]) + '\', \'' + h[6] + '\', \'' + h[7] + '\', \'' + str(h[8]) + '\', \'' + str(int(h[9])) + '\', \'' + str(int(h[10])) + '\', 30, 0, NULL, NULL, NULL)')
        app.db.commit()
    for i in courses_to_remove:
        if not app.db:
            connect_db()
        c = app.db.cursor()
        c.execute('DELETE FROM classes WHERE crn = \'' + i + '\'')
        app.db.commit()
    c = app.db.cursor()
    c.execute('SELECT DISTINCT crn from classes')
    all_crn = c.fetchall()
    f = []
    for i in all_crn:
        f.append(i[0])
    for i in f:
        c.execute('SELECT current_enrollment from classes WHERE crn = \'' + i + '\'')
        old_enrollment = int(c.fetchall()[0][0])
        c.execute('SELECT max_enrollment from classes WHERE crn = \'' + i + '\'')
        max_enrollment = int(c.fetchall()[0][0])
        for j in range(1, sheet.nrows):
            new_enrollment = int(sheet.row_values(j)[10]) 
            if sheet.row_values(j)[0] == i:
                if new_enrollment == old_enrollment:
                    pass
                else:
                    print("DIFFERENT*************")
                    print("Old enrollment is " + str(old_enrollment))
                    print("New enrollment is " + str(new_enrollment))
                    print("Max enrollment is " + str(max_enrollment))
                    if old_enrollment >= max_enrollment and new_enrollment < max_enrollment:
                        open_spots = max_enrollment - new_enrollment
                        if open_spots >= 1:
                            print(1)
                            c.execute('SELECT student_1, student_2, student_3 FROM classes WHERE crn = \'' + i + '\'')
                            students_on_waitlist = c.fetchall()[0]
                            student_1 = students_on_waitlist[0]
                            print(student_1)
                            if student_1 == None or student_1 == 'NULL':
                                break
                            c.execute('SELECT email_address FROM users WHERE username = \'' + student_1 + '\'')
                            student_1_email = c.fetchall()[0][0]
                            print(student_1_email)
                            recipient = student_1_email
                            message = 'Hello! The class with a CRN of \'' + i + '\' has an opening for you. Use code 123456 to enroll on BannerWeb'
                            subject = 'Waitlist System Notification'
                            msg = Message(subject, recipients=[recipient], body = message)
                            mail.send(msg)




                        if open_spots >= 2:
                            student_2 = students_on_waitlist[1]
                            print(student_2)
                            if student_2 == None or student_2 == 'NULL':
                                break
                            c.execute('SELECT email_address FROM users WHERE username = \'' + student_2 + '\'')
                            student_2_email = c.fetchall()[0][0]
                            print(student_2_email)
                            recipient = student_2_email
                            message = 'Hello! The class with a CRN of \'' + i + '\' has an opening for you. Use code 123456 to enroll on BannerWeb'
                            subject = 'Waitlist System Notification'
                            msg = Message(subject, recipients=[recipient], body = message)
                            mail.send(msg)

                              
                        if open_spots == 3:
                            student_3 = students_on_waitlist[2]
                            print(student_3)
                            if student_3 == None or student_3 == 'NULL':
                                break
                            c.execute('SELECT email_address FROM users WHERE username = \'' + student_3 + '\'')
                            student_3_email = c.fetchall()[0][0]
                            print(student_3_email)
                            recipient = student_3_email
                            message = 'Hello! The class with a CRN of \'' + i + '\' has an opening for you. Use code 123456 to enroll on BannerWeb'
                            subject = 'Waitlist System Notification'
                            msg = Message(subject, recipients=[recipient], body = message)
                            mail.send(msg)
                    c.execute('UPDATE classes SET current_enrollment = \'' + str(int(sheet.row_values(j)[10])) + '\'  WHERE crn = \'' + i + '\'')
                    app.db.commit()

                if new_enrollment <= 10:
                    c.execute('SELECT email_address from users where watchlist_1 = \'' + i + '\'  OR watchlist_2 = \'' + i + '\' OR watchlist_3 = \'' + i + '\'')
                    email_addresses = list(c.fetchall())
                    if len(email_addresses) > 0:
                        for r in email_addresses[0]:
                            print(r)
                            recipient = r
                            message = 'Hello! The class with a CRN of \'' + i + '\' is currently under-enrolled. The class could be cancelled, so make alternative plans!'
                            subject = 'Under-enrollment Warning'
                            msg = Message(subject, recipients=[recipient], body = message)
                            mail.send(msg)
    return render_template('success.html')


@app.route("/remove", methods=['GET', 'POST'])
def remove():
    username = current_user.id
    print(request.method)
    if request.method == 'POST':
        class_to_remove = list(request.form.keys())[0][:5]
        print(class_to_remove)
        if not app.db:
            connect_db()
        c = app.db.cursor()
        c.execute('SELECT class_amount from users WHERE username = \'' + username + '\'')
        class_amount = c.fetchall()[0][0]
        class_amount = class_amount - 1
        c.execute('UPDATE users SET class_amount = \'' + str(class_amount) + '\' where username = \'' + username + '\'')
        c.execute('SELECT class_1, class_2, class_3 FROM users WHERE username = \'' + username + '\'')
        current_classes = list(c.fetchall()[0])
        class_to_remove_number = current_classes.index(class_to_remove) + 1
        for i in range(len(current_classes)):
            if current_classes[i] == None:
                current_classes[i] = 'NULL'
        empty = None
        if class_to_remove_number == 1:
            c.execute('UPDATE users SET class_1 = \'' + current_classes[1] + '\' WHERE username = \'' + username + '\'')
            c.execute('UPDATE users SET class_2 = \'' + current_classes[2] + '\' WHERE username = \'' + username + '\'')
            c.execute('UPDATE users SET class_3 = \'NULL\' WHERE username = \'' + username + '\'')
        if class_to_remove_number == 2:
            c.execute('UPDATE users SET class_2 = \'' + current_classes[2] + '\' WHERE username = \'' + username + '\'')
            c.execute('UPDATE users SET class_3 = \'NULL\' WHERE username = \'' + username + '\'')
        if class_to_remove_number == 3:
            c.execute('UPDATE users SET class_3 = \'NULL\' WHERE username = \'' + username + '\'')
        print(class_to_remove_number)

        c.execute('SELECT wait_current from classes WHERE crn = \'' + class_to_remove + '\'')
        wait_current = c.fetchall()[0][0]
        wait_current = wait_current - 1
        c.execute('UPDATE classes SET wait_current = \'' + str(wait_current) + '\' where crn = \'' + class_to_remove + '\'')
        c.execute('SELECT student_1, student_2, student_3 FROM classes WHERE crn = \'' + class_to_remove + '\'')
        current_students = list(c.fetchall()[0])
        student_to_remove_number = current_students.index(username) + 1
        for i in range(len(current_students)):
            if current_students[i] == None:
                current_students[i] = 'NULL'
        empty = None
        if student_to_remove_number == 1:
            c.execute('UPDATE classes SET student_1 = \'' + current_students[1] + '\' WHERE crn = \'' + class_to_remove + '\'')
            c.execute('UPDATE classes SET student_2 = \'' + current_students[2] + '\' WHERE crn = \'' + class_to_remove + '\'')
            c.execute('UPDATE classes SET student_3 = \'NULL\' WHERE crn = \'' + class_to_remove + '\'')
        if student_to_remove_number == 2:
            c.execute('UPDATE classes SET student_2 = \'' + current_students[2] + '\' WHERE crn = \'' + class_to_remove + '\'')
            c.execute('UPDATE classes SET student_3 = \'NULL\' WHERE crn = \'' + class_to_remove + '\'')
        if student_to_remove_number == 3:
            c.execute('UPDATE classes SET student_3 = \'NULL\' WHERE crn = \'' + class_to_remove + '\'')
        app.db.commit()
    return render_template('success.html', message = "Successfully Removed")


@app.route("/watch", methods=['GET', 'POST'])
def watch():
    username = current_user.id
    print(request.method)
    if request.method == 'POST':
        watch_to_add = list(request.form.keys())[0][:5]
        print(watch_to_add)
        if not app.db:
            connect_db()
        c = app.db.cursor()
        c.execute('SELECT watch_amount from users WHERE username = \'' + username + '\'')
        watch_amount = c.fetchall()[0][0]
        watch_amount = watch_amount + 1
        print(watch_amount)
        c.execute('UPDATE users SET watch_amount = ' + str(watch_amount)  + ' where username = \'' + username + '\'')
        if watch_amount < 4:
            print('UPDATE users set watchlist_' + str(watch_amount) + '\' = \'' + watch_to_add + '\' where username = \'' + username + '\'')
            c.execute('UPDATE users set watchlist_' + str(watch_amount) + ' = \'' + watch_to_add + '\' where username = \'' + username + '\'')
            app.db.commit()
        else:
            return render_template('success.html', message = "You have reached your watchlist limit")


    return render_template('success.html', message = "Successfully added to watchlist")


