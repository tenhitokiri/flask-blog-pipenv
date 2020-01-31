from flask import flash, redirect, render_template, url_for, request, abort
from app import app, db, bcrypt
from app.forms import LoginForm, RegistrationForm, ProfileForm, PostForm, RequestResetForm, ResetPasswordForm
from app.models import Post, User
from flask_login import login_user, current_user, logout_user, login_required
from PIL import Image
import secrets
import os

# seguir en https://youtu.be/vutyTx7IaAI?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH&t=1008


@app.route('/')
@app.route('/home')
def home_page():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(per_page=4)
    return render_template('home.html', posts=posts, page=page)


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


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/user_pics', picture_fn)
    out_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(out_size)
    i.save(picture_path)

    return picture_fn


@app.route('/account', methods=['POST', 'GET'])
@login_required
def account_page():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        # db.session.add(current_user)
        db.session.commit()
        flash(f'Account info updated for {current_user.username} !', 'success')
        return redirect(url_for('account_page'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='user_pics/' +
                         current_user.image_file)
    return render_template('account.html', title='My Account', image_file=image_file, form=form)


@app.route('/post/new', methods=['POST', 'GET'])
@login_required
def new_post_page():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(f'Your post has been created!', 'success')
        return redirect(url_for('home_page'))

    return render_template('new_post.html', title='New Post', form=form, legend='New Post')


@app.route('/post/<int:post_id>')
@login_required
def post_page(post_id):
    post = Post.query.get_or_404(post_id)
    if post:
        return render_template('post.html', title=post.title, post=post)
    else:
        flash(f'Post not found !', 'danger')
        return redirect(url_for('home_page'))


@app.route('/post/update/<int:post_id>', methods=['POST', 'GET'])
@login_required
def edit_post_page(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.title.data
        db.session.commit()
        flash(f'Your post has been updated!', 'success')
        return redirect(url_for('post_page', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('new_post.html', title='New Post', form=form, legend='Update Post')


@app.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post_page(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash(f'Your post has been deleted!', 'success')
    return redirect(url_for('home_page'))


@app.route('/user/<string:username>')
def user_posts_page(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(
        Post.date_posted.desc()).paginate(per_page=4)
    return render_template('user_posts.html', posts=posts, page=page, user=user)


@app.route('/forgot_password', methods=['POST', 'GET'])
def forgot_password_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = RequestResetForm()
    if form.validate_on_submit():
        flash(f'Email sent!', 'success')
        return redirect(url_for('home_page'))

    return render_template('forgot_pw.html', title='Reset Password', form=form)


@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password_page():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        flash(f'Your password has been reset!', 'success')
        return redirect(url_for('home_page'))

    return render_template('reset_pw.html', title='Reset Password', form=form)
