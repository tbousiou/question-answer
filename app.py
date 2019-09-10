from flask import Flask, render_template

app = Flask(__name__)




#App Routes
@app.route('/')
def index():
	return render_template('index.html')

@app.route('/register')
def register():
	return render_template('register.html')


@app.route('/login')
def login():
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