from flask import Flask, request, render_template, redirect, url_for, session, Response
import csv
from flask import Flask, request, render_template, redirect, url_for, session
import requests, os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "Tg4#vLp!1sWq8@Zy")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend-service")

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("token"):
        return render_template("index.html", title="Todos", todos=[])
    headers = {"Authorization": f"Bearer {session['token']}"}
    if request.method == "POST":
        task = request.form["task"]
        r = requests.post(f"{BACKEND_URL}/todos", json={"task": task}, headers=headers, timeout=5)
        r.raise_for_status()
    r = requests.get(f"{BACKEND_URL}/todos", headers=headers, timeout=5)
    r.raise_for_status()
    todos = r.json()
    return render_template("index.html", title="Todos", todos=todos)

# Export todos as CSV
@app.route("/export")
def export():
    if not session.get("token"):
        return redirect(url_for("login"))
    headers = {"Authorization": f"Bearer {session['token']}"}
    r = requests.get(f"{BACKEND_URL}/todos", headers=headers, timeout=5)
    r.raise_for_status()
    todos = r.json()
    def generate():
        data = ["ID", "Task"]
        yield ','.join(data) + '\n'
        for todo in todos:
            yield f'{todo["id"]},{todo["task"]}\n'
    return Response(generate(), mimetype='text/csv', headers={
        "Content-Disposition": "attachment; filename=todos.csv"
    })
@app.route("/signup", methods=["GET", "POST"])
def signup():
    msg = ""
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        r = requests.post(f"{BACKEND_URL}/signup", json={"email": email, "password": password}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            session["token"] = data["token"]
            session["email"] = email
            return redirect(url_for("index"))
        msg = f"Error: {r.text}"
    return render_template("auth.html", title="Sign up", mode="signup", btn="Create account", msg=msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        r = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            session["token"] = data["token"]
            session["email"] = email
            return redirect(url_for("index"))
        msg = "Invalid email or password"
    return render_template("auth.html", title="Log in", mode="login", btn="Log in", msg=msg)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
