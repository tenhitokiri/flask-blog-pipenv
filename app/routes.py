from flask import flash, redirect, render_template, url_for, request
from app import app, db, bcrypt
from app.forms import LoginForm, RegistrationForm
from app.models import Post, User
from flask_login import login_user, current_user, logout_user, login_required

# seguir en video 7

posts = [
    {
        'author': 'thk',
        'title': 'prueba de blog',
        'content': 'asldfkj aslñdfkj salñfkj sladñfkj dsañ',
        'date_posted': '2019-01-25'
    },
    {
        'author': 'thk',
        'title': 'mas pruebas',
        'content': 'asldfkj adfg dfg dfslñdfkj salñfkj sladñfkj dsañ',
        'date_posted': '2019-01-22'
    },
    {
        'author': 'thk',
        'title': 'seguimos con pruebas',
        'content': ' sdfs asldfkj aslñdfkj ssadf sadf alñfkj sladñfkj dsañ',
        'date_posted': '2020-01-25'
    }
]


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html', posts=posts)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account created for {form.username.data}, you can now log in!', 'success')
        return redirect(url_for('login_page'))

    return render_template('register.html', form=form, title='Register')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back! {user.username}', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home_page'))
        else:
            flash(f'Login Invalid, please check credentials!', 'danger')

    return render_template('login.html', form=form, title='Login')


@app.route('/logout')
def logout_page():
    logout_user()
    return redirect(url_for('home_page'))


@app.route('/posts')
def posts_page():
    return "post go here"


@app.route('/account')
@login_required
def account_page():
    return render_template('account.html', title='My Account')
