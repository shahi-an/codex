from __future__ import annotations

import os
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///maids.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Maid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    current_address = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    id_verified = db.Column(db.Boolean, nullable=False, default=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    call_requests = db.relationship("CallRequest", backref="maid", lazy=True, cascade="all, delete-orphan")


class CallRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    maid_id = db.Column(db.Integer, db.ForeignKey("maid.id"), nullable=False)
    requester_name = db.Column(db.String(120), nullable=False)
    requester_phone = db.Column(db.String(20), nullable=False)
    requester_area = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def current_maid() -> Maid | None:
    maid_id = session.get("maid_id")
    if not maid_id:
        return None
    return Maid.query.get(maid_id)


@app.get("/")
def index():
    area = request.args.get("area", "").strip()
    query = Maid.query.order_by(Maid.created_at.desc())

    if area:
        query = query.filter(Maid.current_address.ilike(f"%{area}%"))

    maids = query.all()
    return render_template("index.html", maids=maids, area=area)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        age = request.form.get("age", "").strip()
        experience_years = request.form.get("experience_years", "").strip()
        current_address = request.form.get("current_address", "").strip()
        phone_number = request.form.get("phone_number", "").strip()
        id_verified = request.form.get("id_verified") == "yes"
        password = request.form.get("password", "")

        if not all([name, email, age, experience_years, current_address, phone_number, password]):
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if Maid.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "danger")
            return redirect(url_for("register"))

        maid = Maid(
            name=name,
            email=email,
            age=int(age),
            experience_years=int(experience_years),
            current_address=current_address,
            phone_number=phone_number,
            id_verified=id_verified,
            password_hash=generate_password_hash(password),
        )
        db.session.add(maid)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        maid = Maid.query.filter_by(email=email).first()
        if not maid or not check_password_hash(maid.password_hash, password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        session["maid_id"] = maid.id
        flash("Logged in successfully.", "success")
        return redirect(url_for("maid_dashboard"))

    return render_template("login.html")


@app.get("/logout")
def logout():
    session.pop("maid_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.post("/maids/<int:maid_id>/request-call")
def request_call(maid_id: int):
    maid = Maid.query.get_or_404(maid_id)

    requester_name = request.form.get("requester_name", "").strip()
    requester_phone = request.form.get("requester_phone", "").strip()
    requester_area = request.form.get("requester_area", "").strip()
    notes = request.form.get("notes", "").strip() or None

    if not requester_name or not requester_phone or not requester_area:
        flash("Please enter your name, phone number, and area.", "danger")
        return redirect(url_for("index"))

    call_request = CallRequest(
        maid=maid,
        requester_name=requester_name,
        requester_phone=requester_phone,
        requester_area=requester_area,
        notes=notes,
    )
    db.session.add(call_request)
    db.session.commit()

    flash(f"Call request sent to {maid.name}.", "success")
    return redirect(url_for("index"))


@app.get("/maid/dashboard")
def maid_dashboard():
    maid = current_maid()
    if not maid:
        flash("Please login to view your dashboard.", "warning")
        return redirect(url_for("login"))

    requests = (
        CallRequest.query.filter_by(maid_id=maid.id)
        .order_by(CallRequest.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", maid=maid, requests=requests)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
