from flask import Flask, request, render_template,  redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import db,  connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "ILessThan3You"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)


@app.route('/')
def home_page():
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register_user():

    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(
            username, password, email, first_name, last_name)
        # db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append(
                'Username is taken. Please pick another')
            return render_template('register.html', form=form)
        session['username'] = new_user.username

        flash('Welcome! Successfully created your account!', 'success')
        return redirect(f'/users/{username}')
    return render_template('register.html', form=form)


@app.route('/users/<username>' methods=['GET', 'POST'])
def show_user_page(username):
    # How might I capture and use this logic so that i could just call it instead of rewriting
    current_user = session['username']
    if 'username' not in session:
        flash("Please login first!", 'danger')
        return redirect('/login')
    elif current_user != username:
        flash("You don't have permission to do that!", 'danger')
        return redirect(f'/users/{current_user}')
    user = User.query.get({"username": username})
    feedbacks = Feedback.query.all()
    return render_template('user_page.html', user=user, feedbacks=feedbacks)


@ app.route('/login', methods=['GET', 'POST'])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            flash(f"Welcome Back, {user.first_name}", 'primary')
            session['username'] = user.username
            return redirect(f'/users/{username}')
        else:
            form.username.errors = ['Invalid username/password.']
            return render_template('login.html', form=form)

    return render_template('login.html', form=form)


@ app.route('/logout')
def logout_user():
    session.pop('username')
    flash('Goodbye!', "info")
    return redirect('/')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback_form(username):
    form = FeedbackForm()
    current_user = session['username']
    if 'username' not in session:
        flash("Please login first!", 'danger')
        return redirect('/login')
    elif current_user != username:
        flash("You don't have permission to do that!", 'danger')
        return redirect(f'/users/{current_user}')
    user = User.query.get({"username": username})
    feedbacks = Feedback.query.all()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(
            title=title, content=content, username=current_user)
        db.session.add(new_feedback)
        db.session.commit()
        flash("Your feedback has been created!", 'success')
        return redirect(f'/users/{username}')
    return render_template('add_feedback.html', user=user, form=form)


@app.route('/feedback/<int:id>/update', methods=['GET', 'POST'])
def update_feedback_form(id):

    feedback = Feedback.query.get_or_404(id)

    current_user = session['username']
    if 'username' not in session:
        flash("Please login first!", 'danger')
        return redirect('/login')
    elif current_user != feedback.username:
        flash("You don't have permission to do that!", 'danger')
        return redirect(f'/users/{current_user}')

    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template('edit_feedback.html', feedback=feedback, form=form)


@app.route('/feedback/<int:id>/delete', methods=['POST'])
def delete_feedback(id):

    feedback = Feedback.query.get_or_404(id)
    current_user = session['username']
    if 'username' not in session:
        flash("Please login first!", 'danger')
        return redirect('/login')
    elif current_user != feedback.username:
        flash("You don't have permission to do that!", 'danger')
        return redirect(f'/users/{current_user}')

    else:
        db.session.delete(feedback)
        db.session.commit()
        flash('Your feedback has been put into the soul stone!', 'danger')
        return redirect(f'/users/{current_user}')
