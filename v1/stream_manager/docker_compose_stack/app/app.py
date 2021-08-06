import json
import time

import requests
from datetime import datetime
from flask import Flask, Response, render_template

app = Flask(__name__, template_folder=".")
app.debug = True
app.testing = True


@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/chart-data")
def chart_data():
    def get_sensor_data():
        while True:
            # Read latest 5 computed values from stream_aggregator Lambda
            r = json.loads(requests.get("http://greengrass:8181/api/v1/aggregate").text)
            json_data = json.dumps(
                {
                    "time": datetime.fromtimestamp(r["timestamp"]).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "temperature": r["avg_temperature"],
                    "hertz": r["avg_hertz"],
                }
            )
            yield f"data:{json_data}\n\n"
            time.sleep(5)

    return Response(get_sensor_data(), mimetype="text/event-stream")


if __name__ == "__main__":
    # port mapped via Docker compose
    app.run(host="0.0.0.0", port=5000, debug=True)
