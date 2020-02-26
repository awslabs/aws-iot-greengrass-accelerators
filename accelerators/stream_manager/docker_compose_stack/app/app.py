from flask import Flask

counter = 0


@app.route('/')
def hello():
    global counter
    counter += 1
    return 'Hello World! I have been seen {} times.\n'.format(counter)
