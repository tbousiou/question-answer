from flask import Flask, render_template, g, request, session, redirect, url_for
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

def get_current_user():
	user_result = None
	if 'user' in session:
		user = session['user']

		db = get_db()
		query = 'select id, name, password, expert, admin from users where name = ?'
		user_cur = db.execute(query, [user])
		user_result = user_cur.fetchone()
		#print(user_result['id'])

	return user_result


# Required to close the database connection after every request
@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()


#App Routes
@app.route('/')
def index():
	
	user = get_current_user()

	db = get_db()
	query = """
			select questions.id as id, questions.question_text as question_text, askers.name as asker, experts.name as expert
			from questions
			join users as askers on questions.asked_by_id = askers.id
			join users as experts on questions.expert_id = experts.id
			where questions.answer_text is not NULL
			"""
	questions_cur = db.execute(query)
	questions_results = questions_cur.fetchall()


	return render_template('index.html', user=user, questions=questions_results)

@app.route('/register', methods=['GET', 'POST'])
def register():

	user = get_current_user()

	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()

		query = 'select name from users where name = ?'
		existing_user_cur = db.execute(query, [name])
		existing_user = existing_user_cur.fetchone()
		if existing_user:
			print("user already exists")
			return render_template('register.html', user=user, error="User already exists")

		query = 'insert into users (name, password, expert, admin) values (?, ?, ?, ?)'
		db.execute(query, [name, hashed_password, 0, 0])
		db.commit()

		session['user'] = name
		return redirect(url_for('index'))
		#return f'<h2>User {name} created with password {password}<h2>'

	return render_template('register.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():

	user = get_current_user()
	error = None
	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		#hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()
		query = 'select id, name, password from users where name = ?'
		user_login_cur = db.execute(query, [name])
		user_result = user_login_cur.fetchone()
		
		if user_result and check_password_hash(user_result['password'], password):
			session['user'] = user_result['name']
			return redirect(url_for('index'))
		else:
			error = "Username or passowrd are incorrect"


	return render_template('login.html', user=user, error=error)


@app.route('/logout')
def logout():

	session.pop('user', None)
	
	return redirect(url_for('index'))


@app.route('/question/<question_id>')
def question(question_id):

	user = get_current_user()
	
	db = get_db()
	query = """
			select questions.question_text as question_text, questions.answer_text as answer_text, askers.name as asker, experts.name as expert
			from questions
			join users as askers on questions.asked_by_id = askers.id
			join users as experts on questions.expert_id = experts.id
			where questions.id = ?
			"""
	question_cur = db.execute(query, [question_id])
	question = question_cur.fetchone()

	return render_template('question.html', user=user, question=question)


@app.route('/ask',  methods=['GET', 'POST'])
def ask():
	
	user = get_current_user()

	if not user:
		return redirect(url_for('login'))

	db = get_db()

	if request.method == 'POST':
		query = 'insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)'
		db.execute(query, [request.form['question'], user['id'], request.form['expert'] ])
		db.commit()

		return redirect(url_for('index'))
	

	
	expert_cur = db.execute('select id, name from users where expert = 1')
	expert_results = expert_cur.fetchall()
	
	return render_template('ask.html', user=user, experts=expert_results)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
	
	user = get_current_user()

	if not user:
		return redirect(url_for('login'))

	if user['expert'] == 0:
		return redirect(url_for('index'))

	db = get_db()

	if request.method == 'POST':
		db.execute('update questions set answer_text = ? where id = ?', [request.form['answer_text'], question_id ])
		db.commit()
		return redirect(url_for('unanswered'))

	query = 'select id, question_text from questions where id = ?'
	question_cur = db.execute(query, [question_id])
	question = question_cur.fetchone()

	return render_template('answer.html', user=user, question=question)

@app.route('/unanswered')
def unanswered():

	user = get_current_user()

	if not user:
		return redirect(url_for('login'))

	if user['expert'] == 0:
		return redirect(url_for('index'))

	db = get_db()
	query = """
			select questions.id as id, questions.question_text as question_text, users.name as username
			from questions
			join users
			on questions.asked_by_id = users.id
			where questions.expert_id = ? and questions.answer_text is null
			"""
	questions_cur = db.execute(query, [ user['id'] ])
	questions_results = questions_cur.fetchall()
	#print(len(questions_results))

	return render_template('unanswered.html', user=user, questions=questions_results)

@app.route('/users')
def users():

	user = get_current_user()

	if not user:
		return redirect(url_for('login'))

	if user['admin'] == 0:
		return redirect(url_for('index'))

	db = get_db()
	users_cur = db.execute('select id, name, expert, admin from users')
	users_results = users_cur.fetchall()

	return render_template('users.html', user=user, users=users_results)



@app.route('/promote/<user_id>')
def promote(user_id):

	user = get_current_user()
	
	if not user:
		return redirect(url_for('login'))

	if user['admin'] == 0:
		return redirect(url_for('index'))

	db = get_db()
	db.execute('update users set expert = 1 where id = ?', [user_id])
	db.commit()

	return redirect(url_for('users'))

if __name__ == '__main__':
	app.run(debug=True)