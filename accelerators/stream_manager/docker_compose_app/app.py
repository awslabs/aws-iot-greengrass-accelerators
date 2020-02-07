from flask import Flask

app = Flask(__name__)

counter = 0

@app.route('/')
def hello():
    global counter
    counter += 1
    return 'Hello World! I have been seen {} times.\n'.format(counter)
