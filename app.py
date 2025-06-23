from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# In-memory storage for savings
savings = []

@app.route('/')
def index():
    return render_template('index.html', savings=savings)

@app.route('/add', methods=['POST'])
def add_saving():
    amount = request.form.get('amount')
    if amount:
        savings.append(amount)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)