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
	return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():

	user = get_current_user()

	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()
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

	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		#hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()
		query = 'select id, name, password from users where name = ?'
		user_login_cur = db.execute(query, [name])
		user_result = user_login_cur.fetchone()
		
		if check_password_hash(user_result['password'], password):
			session['user'] = user_result['name']
			return redirect(url_for('index'))
			#return '<h2>The password is correct,</h2>'
		else:
			return '<h2>The password is INcorrect,</h2>'



	return render_template('login.html', user=user)

@app.route('/question')
def question():

	user = get_current_user()
	
	return render_template('question.html', user=user)


@app.route('/ask',  methods=['GET', 'POST'])
def ask():
	
	user = get_current_user()
	db = get_db()

	if request.method == 'POST':
		db.execute('insert into questions (question_text, asked_by_id, expert_id) values (?, ?, ?)', [request.form['question'], user['id'], request.form['expert'] ])
		db.commit()

		#return f"Question: {request.form['question']}, Expert: {request.form['expert']}"
		return redirect(url_for('index'))
	

	
	expert_cur = db.execute('select id, name from users where expert = 1')
	expert_results = expert_cur.fetchall()
	
	return render_template('ask.html', user=user, experts=expert_results)


@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
	
	user = get_current_user()

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
	#print(user['id'])

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
	print(len(questions_results))

	return render_template('unanswered.html', user=user, questions=questions_results)

@app.route('/users')
def users():

	user = get_current_user()

	db = get_db()
	users_cur = db.execute('select id, name, expert, admin from users')
	users_results = users_cur.fetchall()

	return render_template('users.html', user=user, users=users_results)

@app.route('/logout')
def logout():
	session.pop('user', None)
	return redirect(url_for('index'))

@app.route('/promote/<user_id>')
def promote(user_id):
	db = get_db()
	db.execute('update users set expert = 1 where id = ?', [user_id])
	db.commit()

	return redirect(url_for('users'))

if __name__ == '__main__':
	app.run(debug=True)