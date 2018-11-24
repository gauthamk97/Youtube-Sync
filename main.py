from flask import Flask, url_for, render_template
app = Flask(__name__)

@app.route('/hello')
@app.route('/hello/<name>')
def helloworld(name=None):
    return render_template('hello.html', name=name)

with app.test_request_context():
    print("Hello There")
    print(url_for('helloworld', name='gautham'))