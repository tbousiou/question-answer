from flask import Flask, render_template, g, request
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


# Required to close the database connection after every request
@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()


#App Routes
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()
		query = 'insert into users (name, password, expert, admin) values (?, ?, ?, ?)'
		db.execute(query, [name, hashed_password, 0, 0])
		db.commit()
		return f'<h2>User {name} created with password {password}<h2>'

	return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		#hashed_password = generate_password_hash(password, method='sha256')

		db = get_db()
		query = 'select id, name, password from users where name = ?'
		user_login_cur = db.execute(query, [name])
		user_result = user_login_cur.fetchone()
		
		if user_result and check_password_hash(user_result['password'], password):
			return 'Success'
		else:
			return 'Fail'



	return render_template('login.html')

@app.route('/question')
def question():
	return render_template('question.html')


@app.route('/ask')
def ask():
	return render_template('ask.html')


@app.route('/answer')
def answer():
	return render_template('answer.html')

@app.route('/unanswered')
def unanswered():
	return render_template('unanswered.html')

@app.route('/users')
def users():
	return render_template('users.html')

if __name__ == '__main__':
	app.run(debug=True)