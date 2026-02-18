from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///vulnerabilities.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

VALID_STATUSES = [
    "Open",
    "Work in Progress",
    "Closed",
    "Awaiting Further Information",
]


class Vulnerability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(120), nullable=True)
    server_name = db.Column(db.String(255), nullable=True)
    vulnerability_type = db.Column(db.String(255), nullable=True)
    severity = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(80), nullable=False, default="Open")
    assigned_individual = db.Column(db.String(255), nullable=True)
    assigned_team = db.Column(db.String(255), nullable=True)
    imported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class AssignmentRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vulnerability_type = db.Column(db.String(255), unique=True, nullable=False)
    assigned_individual = db.Column(db.String(255), nullable=True)
    assigned_team = db.Column(db.String(255), nullable=True)


def normalize_headers(columns: list[str]) -> dict[str, str]:
    return {c.strip().lower().replace(" ", "_"): c for c in columns}


def value_for(row: pd.Series, headers: dict[str, str], *candidates: str) -> Any:
    for candidate in candidates:
        key = candidate.strip().lower().replace(" ", "_")
        if key in headers:
            value = row[headers[key]]
            if pd.isna(value):
                return None
            return str(value).strip()
    return None


def apply_assignment(vulnerability: Vulnerability) -> None:
    if not vulnerability.vulnerability_type:
        return

    rule = AssignmentRule.query.filter_by(
        vulnerability_type=vulnerability.vulnerability_type
    ).first()
    if rule:
        vulnerability.assigned_individual = rule.assigned_individual
        vulnerability.assigned_team = rule.assigned_team


@app.get("/")
def index():
    status = request.args.get("status")
    vuln_type = request.args.get("type")

    query = Vulnerability.query.order_by(Vulnerability.imported_at.desc())
    if status:
        query = query.filter_by(status=status)
    if vuln_type:
        query = query.filter_by(vulnerability_type=vuln_type)

    vulnerabilities = query.all()
    types = [
        t[0]
        for t in db.session.query(Vulnerability.vulnerability_type)
        .distinct()
        .order_by(Vulnerability.vulnerability_type.asc())
        .all()
        if t[0]
    ]

    return render_template(
        "index.html",
        vulnerabilities=vulnerabilities,
        statuses=VALID_STATUSES,
        selected_status=status,
        selected_type=vuln_type,
        vulnerability_types=types,
    )


@app.route("/import", methods=["GET", "POST"])
def import_excel():
    if request.method == "POST":
        file = request.files.get("excel_file")
        if not file or not file.filename:
            flash("Please upload an Excel file.", "danger")
            return redirect(url_for("import_excel"))

        try:
            dataframe = pd.read_excel(file)
        except Exception as exc:  # noqa: BLE001
            flash(f"Could not read Excel file: {exc}", "danger")
            return redirect(url_for("import_excel"))

        if dataframe.empty:
            flash("The uploaded report has no rows.", "warning")
            return redirect(url_for("import_excel"))

        headers = normalize_headers(list(dataframe.columns))
        imported_count = 0

        for _, row in dataframe.iterrows():
            vulnerability = Vulnerability(
                external_id=value_for(row, headers, "id", "vulnerability_id", "ticket"),
                server_name=value_for(row, headers, "server", "server_name", "hostname"),
                vulnerability_type=value_for(
                    row, headers, "vulnerability_type", "type", "category"
                ),
                severity=value_for(row, headers, "severity", "risk"),
                description=value_for(row, headers, "description", "details"),
                status=value_for(row, headers, "status") or "Open",
            )

            if vulnerability.status not in VALID_STATUSES:
                vulnerability.status = "Open"

            apply_assignment(vulnerability)
            db.session.add(vulnerability)
            imported_count += 1

        db.session.commit()
        flash(f"Imported {imported_count} vulnerabilities.", "success")
        return redirect(url_for("index"))

    return render_template("import.html")


@app.route("/vulnerabilities/<int:vulnerability_id>", methods=["GET", "POST"])
def vulnerability_detail(vulnerability_id: int):
    vulnerability = Vulnerability.query.get_or_404(vulnerability_id)

    if request.method == "POST":
        new_status = request.form.get("status")
        assigned_individual = request.form.get("assigned_individual")
        assigned_team = request.form.get("assigned_team")

        if new_status in VALID_STATUSES:
            vulnerability.status = new_status

        vulnerability.assigned_individual = assigned_individual
        vulnerability.assigned_team = assigned_team

        db.session.commit()
        flash("Vulnerability updated.", "success")
        return redirect(url_for("vulnerability_detail", vulnerability_id=vulnerability.id))

    return render_template(
        "detail.html",
        vulnerability=vulnerability,
        statuses=VALID_STATUSES,
    )


@app.route("/assignment-rules", methods=["GET", "POST"])
def assignment_rules():
    if request.method == "POST":
        vulnerability_type = request.form.get("vulnerability_type", "").strip()
        assigned_individual = request.form.get("assigned_individual", "").strip() or None
        assigned_team = request.form.get("assigned_team", "").strip() or None

        if not vulnerability_type:
            flash("Vulnerability type is required.", "danger")
            return redirect(url_for("assignment_rules"))

        rule = AssignmentRule.query.filter_by(vulnerability_type=vulnerability_type).first()
        if not rule:
            rule = AssignmentRule(vulnerability_type=vulnerability_type)

        rule.assigned_individual = assigned_individual
        rule.assigned_team = assigned_team
        db.session.add(rule)
        db.session.commit()

        flash("Assignment rule saved.", "success")
        return redirect(url_for("assignment_rules"))

    rules = AssignmentRule.query.order_by(AssignmentRule.vulnerability_type.asc()).all()
    return render_template("rules.html", rules=rules)


@app.post("/assignment-rules/<int:rule_id>/delete")
def delete_rule(rule_id: int):
    rule = AssignmentRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    flash("Rule deleted.", "success")
    return redirect(url_for("assignment_rules"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
