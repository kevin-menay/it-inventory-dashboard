#!/usr/bin/env python3
"""
IT Inventory Dashboard - Flask web application for tracking hardware and software assets
"""
import csv
import io
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///inventory.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ── Models ────────────────────────────────────────────────────────────────────

class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_tag = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=False)   # Hardware / Software / License
    asset_type = db.Column(db.String(80))                  # Laptop, Desktop, Switch, etc.
    manufacturer = db.Column(db.String(80))
    model = db.Column(db.String(80))
    serial_number = db.Column(db.String(100))
    status = db.Column(db.String(30), default="Active")    # Active, Retired, In Repair, In Storage
    assigned_to = db.Column(db.String(100))
    location = db.Column(db.String(120))
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "asset_tag": self.asset_tag,
            "name": self.name,
            "category": self.category,
            "asset_type": self.asset_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "location": self.location,
            "purchase_date": str(self.purchase_date) if self.purchase_date else "",
            "warranty_expiry": str(self.warranty_expiry) if self.warranty_expiry else "",
            "cost": self.cost or "",
            "notes": self.notes or "",
        }


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    total = Asset.query.count()
    by_status = db.session.query(Asset.status, db.func.count()).group_by(Asset.status).all()
    by_category = db.session.query(Asset.category, db.func.count()).group_by(Asset.category).all()

    # Expiring warranties (next 90 days)
    today = datetime.utcnow().date()
    expiring = Asset.query.filter(
        Asset.warranty_expiry != None,  # noqa
        Asset.warranty_expiry <= datetime(today.year, today.month, today.day).__class__(
            today.year, today.month, today.day
        ).__class__.today().__class__.today().__class__(2099, 12, 31),
    ).count()

    total_cost = db.session.query(db.func.sum(Asset.cost)).scalar() or 0

    return render_template("dashboard.html",
                           total=total,
                           by_status=dict(by_status),
                           by_category=dict(by_category),
                           total_cost=total_cost)


@app.route("/assets")
def list_assets():
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    status = request.args.get("status", "")

    query = Asset.query
    if search:
        query = query.filter(
            db.or_(
                Asset.name.ilike(f"%{search}%"),
                Asset.asset_tag.ilike(f"%{search}%"),
                Asset.assigned_to.ilike(f"%{search}%"),
                Asset.serial_number.ilike(f"%{search}%"),
            )
        )
    if category:
        query = query.filter(Asset.category == category)
    if status:
        query = query.filter(Asset.status == status)

    assets = query.order_by(Asset.updated_at.desc()).all()
    categories = db.session.query(Asset.category).distinct().all()
    statuses = ["Active", "Retired", "In Repair", "In Storage"]

    return render_template("assets.html", assets=assets,
                           categories=[c[0] for c in categories],
                           statuses=statuses, search=search,
                           filter_category=category, filter_status=status)


@app.route("/assets/new", methods=["GET", "POST"])
def new_asset():
    if request.method == "POST":
        data = request.form

        def parse_date(val):
            if val:
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        asset = Asset(
            asset_tag=data["asset_tag"],
            name=data["name"],
            category=data["category"],
            asset_type=data.get("asset_type"),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            serial_number=data.get("serial_number"),
            status=data.get("status", "Active"),
            assigned_to=data.get("assigned_to"),
            location=data.get("location"),
            purchase_date=parse_date(data.get("purchase_date")),
            warranty_expiry=parse_date(data.get("warranty_expiry")),
            cost=float(data["cost"]) if data.get("cost") else None,
            notes=data.get("notes"),
        )
        db.session.add(asset)
        db.session.commit()
        flash(f"Asset '{asset.name}' created successfully!", "success")
        return redirect(url_for("list_assets"))

    return render_template("asset_form.html", asset=None)


@app.route("/assets/<int:asset_id>/edit", methods=["GET", "POST"])
def edit_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)

    if request.method == "POST":
        data = request.form

        def parse_date(val):
            if val:
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        asset.name = data["name"]
        asset.category = data["category"]
        asset.asset_type = data.get("asset_type")
        asset.manufacturer = data.get("manufacturer")
        asset.model = data.get("model")
        asset.serial_number = data.get("serial_number")
        asset.status = data.get("status", "Active")
        asset.assigned_to = data.get("assigned_to")
        asset.location = data.get("location")
        asset.purchase_date = parse_date(data.get("purchase_date"))
        asset.warranty_expiry = parse_date(data.get("warranty_expiry"))
        asset.cost = float(data["cost"]) if data.get("cost") else None
        asset.notes = data.get("notes")
        asset.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f"Asset '{asset.name}' updated!", "success")
        return redirect(url_for("list_assets"))

    return render_template("asset_form.html", asset=asset)


@app.route("/assets/<int:asset_id>/delete", methods=["POST"])
def delete_asset(asset_id):
    asset = Asset.query.get_or_404(asset_id)
    name = asset.name
    db.session.delete(asset)
    db.session.commit()
    flash(f"Asset '{name}' deleted.", "warning")
    return redirect(url_for("list_assets"))


@app.route("/export/csv")
def export_csv():
    assets = Asset.query.order_by(Asset.asset_tag).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "asset_tag", "name", "category", "asset_type",
        "manufacturer", "model", "serial_number", "status",
        "assigned_to", "location", "purchase_date", "warranty_expiry",
        "cost", "notes"
    ])
    writer.writeheader()
    for asset in assets:
        writer.writerow(asset.to_dict())

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=inventory_{datetime.now().strftime('%Y%m%d')}.csv"}
    )


@app.route("/import/csv", methods=["POST"])
def import_csv():
    if "file" not in request.files:
        flash("No file selected", "error")
        return redirect(url_for("list_assets"))

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        flash("Please upload a CSV file", "error")
        return redirect(url_for("list_assets"))

    stream = io.StringIO(file.stream.read().decode("utf-8"))
    reader = csv.DictReader(stream)

    imported = 0
    skipped = 0

    for row in reader:
        if Asset.query.filter_by(asset_tag=row.get("asset_tag", "")).first():
            skipped += 1
            continue

        def parse_date(val):
            if val:
                try:
                    return datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        asset = Asset(
            asset_tag=row.get("asset_tag", f"IMP-{imported}"),
            name=row.get("name", "Unknown"),
            category=row.get("category", "Hardware"),
            asset_type=row.get("asset_type"),
            manufacturer=row.get("manufacturer"),
            model=row.get("model"),
            serial_number=row.get("serial_number"),
            status=row.get("status", "Active"),
            assigned_to=row.get("assigned_to"),
            location=row.get("location"),
            purchase_date=parse_date(row.get("purchase_date")),
            warranty_expiry=parse_date(row.get("warranty_expiry")),
            cost=float(row["cost"]) if row.get("cost") else None,
            notes=row.get("notes"),
        )
        db.session.add(asset)
        imported += 1

    db.session.commit()
    flash(f"Imported {imported} assets ({skipped} skipped - duplicate tags)", "success")
    return redirect(url_for("list_assets"))


# ── Startup ───────────────────────────────────────────────────────────────────

def seed_sample_data():
    """Add sample assets for demonstration."""
    if Asset.query.count() > 0:
        return

    samples = [
        Asset(asset_tag="HW-001", name="Dell Latitude 5540", category="Hardware",
              asset_type="Laptop", manufacturer="Dell", model="Latitude 5540",
              serial_number="SN-DELL-001", status="Active", assigned_to="Jane Smith",
              location="Building A - Floor 2", cost=1299.99),
        Asset(asset_tag="HW-002", name="HP EliteDesk 800 G9", category="Hardware",
              asset_type="Desktop", manufacturer="HP", model="EliteDesk 800 G9",
              serial_number="SN-HP-002", status="Active", assigned_to="Mike Johnson",
              location="Building B - IT Dept", cost=899.00),
        Asset(asset_tag="NET-001", name="Cisco Catalyst 2960", category="Hardware",
              asset_type="Network Switch", manufacturer="Cisco", model="Catalyst 2960-48PS-L",
              serial_number="SN-CISCO-001", status="Active",
              location="Server Room - Rack A", cost=2450.00),
        Asset(asset_tag="SW-001", name="Microsoft Office 365 Business", category="Software",
              asset_type="Productivity Suite", manufacturer="Microsoft",
              status="Active", assigned_to="IT Department",
              location="Cloud/All Users", cost=150.00),
        Asset(asset_tag="HW-003", name="Lenovo ThinkPad X1 Carbon", category="Hardware",
              asset_type="Laptop", manufacturer="Lenovo", model="ThinkPad X1 Carbon Gen 11",
              serial_number="SN-LEN-003", status="In Repair",
              location="IT Repair Bench", cost=1599.99),
    ]
    db.session.bulk_save_objects(samples)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_sample_data()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
