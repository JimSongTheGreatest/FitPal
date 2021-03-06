from __future__ import print_function
from flask import redirect, url_for, render_template, flash, request, session, make_response
from fitness import app, db, bcrypt
from fitness.forms import SignInForm, SignUpForm, itemForm, calorieForm, CalorieWorkoutForm
from fitness.database import User, Post, load_user, UserData, Todo
from flask_login import current_user, login_user, current_user, logout_user, login_required
from fitness import nix
from fitness.createplan import *
from time import time
from datetime import date
import json
import sys
import os


# Get the user database for routes
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}


# Default route
@app.route("/")
def index():
    db.create_all()
    posts = Post.query.all()
    return render_template('index.html', posts=posts)


# Protected route for user id and user consumed
@app.route("/protected")
def protected():
    return str(current_user.id)
    return str(current_user.consumed)


# Route for home page
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

# Route for log out direction which is home page
@app.route("/logout")
@login_required
def logout():
    session.pop('fname')
    session.pop('id')
    logout_user()
    return redirect(url_for("home"))


# Route of user after they logged in
@app.route("/user")
@login_required
def user():
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('user_dashboard.html', total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Route for cardio workout
@app.route("/cardio", methods=['GET', 'POST'])
@login_required
def cardio():
    form = CalorieWorkoutForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=session['id']).first()
        user_data = UserData(cardio=int(form.cardio_wo.data), user_id=session['id'])
        db.session.add(user_data)
        db.session.commit()
        return redirect(url_for('cardio'))
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('cardio.html', form=form, total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Route for strength workout
@app.route("/strength")
@login_required
def strength():
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('strength.html', total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Route for clothes shopping
@app.route("/clothes")
@login_required
def clothes():
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('clothes.html', total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Route for equipment shopping
@app.route("/equipment")
@login_required
def gift():
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('equipment.html', total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Route for supplement shopping
@app.route("/supplement")
@login_required
def supplement():
    total, monthly_calories, perk, achivement = calculate_workout()
    return render_template('supplement.html', total=total, monthly_calories=monthly_calories, perk=perk,
                           achivement=achivement)


# Sign up function for user with fields
# and store them database
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(fname=form.first_name.data, lname=form.last_name.data, email=form.email.data,
                    password=hash_password, user_perk=250, consumed=0, burned=0, calories=0)
        db.session.add(user)
        db.session.commit()
        flash(f'Thank you for signing up with us', 'success')
        return redirect(url_for('signin'))
    return render_template('signup.html', title='Register', form=form)


# Sign up function for user with fields
# and query input information to database
# if the input match, the user will log in.
# Otherwise, error message will display
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SignInForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            session['id'] = user.id
            session['fname'] = user.fname
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('signin.html', form=form)


@login_required
def calculate_workout():
    achivement_max = 1500
    get_all = UserData.query.filter_by(user_id=session['id']).all()
    total_cardio = 0
    total_strength = 0
    total_cardio_m = 0
    total_strength_m = 0
    now = date.today()
    day = now.strftime("%d")
    month = now.strftime("%m")
    for item in get_all:
        # Get the daily calories
        day1 = item.date.strftime("%d")
        if item.cardio is not None and day == day1:
            total_cardio = total_cardio + item.cardio
        if item.strength is not None and day == day1:
            total_strength = total_strength + item.strength
        # Get the monthly calories
        month1 = item.date.strftime("%m")
        if item.cardio is not None and month == month1:
            total_cardio_m = total_cardio_m + item.cardio
        if item.strength is not None and month == month1:
            total_strength_m = total_strength_m + item.strength
    total = total_strength + total_cardio
    monthly_calories = total_strength_m + total_cardio_m
    user = User.query.filter_by(id=session['id']).first()
    perk = user.user_perk
    achivement = int((total / achivement_max) * 100)
    if achivement > 100:
        achivement = 100
        perk += 50
    user.user_perk += perk
    return total, monthly_calories, perk, achivement

@app.route('/pomodoroTimer')
@login_required
def pomodoroTimer():
    title = 'Workout Timer'
    return render_template("pomodoroTimer.html", title=title)

@app.route("/delete")
@login_required
def delete():
    session.pop('fname')
    session.pop('id')
    logout_user()
    flash('Your account is deleted', 'error')
    return redirect("/signin")


@app.route("/todolist")
@login_required
def todoList():
    todo_list = Todo.query.all()
    return render_template("todolist.html", todo_list=todo_list)

@app.route("/add", methods=["POST"])
@login_required
def add():   
    title = request.form.get("title")
    new_todo = Todo(title=title, complete=False)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("todoList"))

@app.route("/update/<int:todo_id>")
@login_required
def update(todo_id):   
    todo = Todo.query.filter_by(id=todo_id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("todoList"))

@app.route("/delete/<int:todo_id>")
@login_required
def deletetodo(todo_id):   
    todo = Todo.query.filter_by(id=todo_id).first()
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("todoList"))

@app.route("/admin")
def workoutplan():
    return render_template("index.html")

