from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from process import Process
from analyze import Analyze

app= Flask(__name__)

error=False

bootstrap = Bootstrap(app)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route("/", methods=['GET', 'POST'])
def home():
	return render_template("home.html")

@app.route('/results', methods=['POST'])
def results():
   link = request.form['address']
   des, dia = Process(link)
   if len(des)==0 or len(dia)==0:
   	error=True
   	return redirect(url_for('home', error=error))
   timestamp = Analyze(des, dia)
   print(timestamp)
   return render_template("results.html", timestamp=timestamp)

if __name__ == '__main__':
	app.run(debug=True)