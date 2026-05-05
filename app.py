import os
import re
import json
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "replace-this-in-production"),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///hr_payroll_crm.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    UPLOAD_FOLDER=UPLOAD_DIR,
    MAX_CONTENT_LENGTH=10 * 1024 * 1024,
)

db = SQLAlchemy(app)

ROLES = ("Admin", "HR", "Manager", "Employee")
EMPLOYEE_TYPES = ("SM", "Labour", "ANL")
AADHAAR_RE = re.compile(r"^[2-9]{1}[0-9]{11}$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")


def role_required(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in allowed_roles:
                flash("You are not authorized for this action.", "danger")
                return redirect(url_for("dashboard"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="Employee")
    employee = db.relationship("Employee", back_populates="user", uselist=False)


class Shift(TimestampMixin, db.Model):
    __tablename__ = "shifts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)


class SalaryTemplate(TimestampMixin, db.Model):
    __tablename__ = "salary_templates"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    basic = db.Column(db.Numeric(12, 2), default=0)
    hra = db.Column(db.Numeric(12, 2), default=0)
    da = db.Column(db.Numeric(12, 2), default=0)
    special_allowance = db.Column(db.Numeric(12, 2), default=0)
    bonus = db.Column(db.Numeric(12, 2), default=0)
    gratuity = db.Column(db.Numeric(12, 2), default=0)


class Employee(TimestampMixin, db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(30), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    aadhaar = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(120), nullable=False)
    designation = db.Column(db.String(120), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), nullable=True)
    employee_type = db.Column(db.String(20), nullable=False)
    fixed_salary = db.Column(db.Numeric(12, 2), default=0)
    per_day_rate = db.Column(db.Numeric(12, 2), default=0)
    lwf = db.Column(db.Numeric(12, 2), default=0)
    esic_applicable = db.Column(db.Boolean, default=False)
    esic_amount = db.Column(db.Numeric(12, 2), default=0)
    other_deductions = db.Column(db.Numeric(12, 2), default=0)
    overtime_pay_allowed = db.Column(db.Boolean, default=False)
    bank_name = db.Column(db.String(120), default="")
    bank_account_number = db.Column(db.String(40), default="")
    bank_ifsc = db.Column(db.String(20), default="")
    account_holder_name = db.Column(db.String(120), default="")
    salary_components = db.Column(db.Text, default="{}")
    component_toggles = db.Column(db.Text, default="{}")

    user = db.relationship("User", back_populates="employee")
    shift = db.relationship("Shift")


class EmployeeCustomField(TimestampMixin, db.Model):
    __tablename__ = "employee_custom_fields"
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(120), nullable=False, unique=True)
    field_type = db.Column(db.String(30), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    options_json = db.Column(db.Text, default="[]")


class EmployeeCustomValue(TimestampMixin, db.Model):
    __tablename__ = "employee_custom_values"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey("employee_custom_fields.id"), nullable=False)
    value = db.Column(db.Text, nullable=True)


class Attendance(TimestampMixin, db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    worked_shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), nullable=True)
    overtime_hours = db.Column(db.Numeric(6, 2), default=0)


class Leave(TimestampMixin, db.Model):
    __tablename__ = "leaves"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days = db.Column(db.Numeric(6, 2), nullable=False)
    reason = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="Pending")
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class Payroll(TimestampMixin, db.Model):
    __tablename__ = "payroll"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    cycle_start = db.Column(db.Date, nullable=False)
    cycle_end = db.Column(db.Date, nullable=False)
    gross_salary = db.Column(db.Numeric(12, 2), nullable=False)
    total_deductions = db.Column(db.Numeric(12, 2), nullable=False)
    net_salary = db.Column(db.Numeric(12, 2), nullable=False)
    breakdown_json = db.Column(db.Text, default="{}")


class Announcement(TimestampMixin, db.Model):
    __tablename__ = "announcements"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


class CrmLead(TimestampMixin, db.Model):
    __tablename__ = "crm_leads"
    id = db.Column(db.Integer, primary_key=True)
    lead_name = db.Column(db.String(140), nullable=False)
    client_company = db.Column(db.String(140), nullable=False)
    contact = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(40), default="New")
    follow_up_date = db.Column(db.Date, nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notes = db.Column(db.Text, default="")


def generate_employee_code():
    latest = Employee.query.order_by(Employee.id.desc()).first()
    next_id = 1 if not latest else latest.id + 1
    return f"EMP{next_id:05d}"


def payroll_cycle_for(date_obj: date):
    if date_obj.day >= 26:
        start = date(date_obj.year, date_obj.month, 26)
        next_month = date_obj.replace(day=1) + timedelta(days=32)
        end = date(next_month.year, next_month.month, 25)
    else:
        prev = date_obj.replace(day=1) - timedelta(days=1)
        start = date(prev.year, prev.month, 26)
        end = date(date_obj.year, date_obj.month, 25)
    return start, end


def calc_payroll(employee: Employee, cycle_start: date, cycle_end: date):
    attendances = Attendance.query.filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date >= cycle_start,
        Attendance.attendance_date <= cycle_end,
    ).all()
    present_days = sum(1 for x in attendances if x.status == "Present")
    half_days = sum(1 for x in attendances if x.status == "Half-day")
    working_days = Decimal(present_days) + (Decimal(half_days) / Decimal(2))

    breakdown = {"working_days": float(working_days), "employee_type": employee.employee_type}
    deductions = Decimal(employee.lwf or 0) + Decimal(employee.other_deductions or 0)
    gross = Decimal(0)

    if employee.employee_type == "SM":
        gross = Decimal(employee.fixed_salary or 0)
    elif employee.employee_type == "Labour":
        gross = Decimal(employee.per_day_rate or 0) * working_days
    else:
        components = json.loads(employee.salary_components or "{}")
        toggles = json.loads(employee.component_toggles or "{}")
        for key in ["basic", "hra", "da", "special_allowance", "bonus", "gratuity"]:
            if toggles.get(key, True):
                gross += Decimal(str(components.get(key, 0)))
        pf = Decimal(str(components.get("basic", 0))) * Decimal("0.12") if toggles.get("basic", True) else Decimal(0)
        deductions += pf
        breakdown["pf"] = float(pf)
        if employee.esic_applicable:
            deductions += Decimal(employee.esic_amount or 0)

    net = gross - deductions
    breakdown.update({"gross": float(gross), "deductions": float(deductions), "net": float(net)})
    return gross, deductions, net, breakdown


@app.template_filter("from_json")
def from_json(value):
    try:
        return json.loads(value or "[]")
    except Exception:
        return []



@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["role"] = user.role
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@role_required("Admin", "HR", "Manager", "Employee")
def dashboard():
    total_employees = Employee.query.count()
    total_leaves = Leave.query.count()
    total_payroll = Payroll.query.count()
    total_attendance = Attendance.query.count()
    return render_template("dashboard.html", **locals())


@app.route("/employees", methods=["GET", "POST"])
@role_required("Admin", "HR")
def employees():
    if request.method == "POST":
        aadhaar = request.form["aadhaar"].strip()
        if not AADHAAR_RE.match(aadhaar):
            flash("Invalid Aadhaar format", "danger")
            return redirect(url_for("employees"))
        ifsc = request.form.get("bank_ifsc", "").upper().strip()
        if ifsc and not IFSC_RE.match(ifsc):
            flash("Invalid IFSC format", "danger")
            return redirect(url_for("employees"))
        emp = Employee(
            employee_code=generate_employee_code(),
            name=request.form["name"],
            phone=request.form["phone"],
            aadhaar=aadhaar,
            address=request.form["address"],
            department=request.form["department"],
            designation=request.form["designation"],
            shift_id=request.form.get("shift_id") or None,
            employee_type=request.form["employee_type"],
            fixed_salary=request.form.get("fixed_salary") or 0,
            per_day_rate=request.form.get("per_day_rate") or 0,
            lwf=request.form.get("lwf") or 0,
            esic_applicable=bool(request.form.get("esic_applicable")),
            esic_amount=request.form.get("esic_amount") or 0,
            other_deductions=request.form.get("other_deductions") or 0,
            overtime_pay_allowed=bool(request.form.get("overtime_pay_allowed")),
            bank_name=request.form.get("bank_name", ""),
            bank_account_number=request.form.get("bank_account_number", ""),
            bank_ifsc=ifsc,
            account_holder_name=request.form.get("account_holder_name", ""),
            salary_components=json.dumps({k: request.form.get(k) or 0 for k in ["basic", "hra", "da", "special_allowance", "bonus", "gratuity"]}),
            component_toggles=json.dumps({k: bool(request.form.get(f"enable_{k}")) for k in ["basic", "hra", "da", "special_allowance", "bonus", "gratuity"]}),
        )
        db.session.add(emp)
        db.session.flush()

        for field in EmployeeCustomField.query.all():
            val = request.form.get(f"custom_{field.id}", "")
            if field.is_required and not val:
                flash(f"{field.field_name} is required", "danger")
                db.session.rollback()
                return redirect(url_for("employees"))
            if field.field_type == "file" and field.field_name in request.files:
                file = request.files[field.field_name]
                if file and file.filename:
                    filename = secure_filename(f"{emp.employee_code}_{field.field_name}_{file.filename}")
                    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(filepath)
                    val = filepath
            if val:
                db.session.add(EmployeeCustomValue(employee_id=emp.id, field_id=field.id, value=str(val)))

        db.session.commit()
        flash("Employee created", "success")
        return redirect(url_for("employees"))

    employees = Employee.query.order_by(Employee.created_at.desc()).all()
    shifts = Shift.query.all()
    custom_fields = EmployeeCustomField.query.all()
    return render_template("employees.html", employees=employees, shifts=shifts, custom_fields=custom_fields)


@app.route("/custom-fields", methods=["GET", "POST"])
@role_required("Admin", "HR")
def custom_fields():
    if request.method == "POST":
        field = EmployeeCustomField(
            field_name=request.form["field_name"],
            field_type=request.form["field_type"],
            is_required=bool(request.form.get("is_required")),
            options_json=json.dumps([x.strip() for x in request.form.get("options", "").split(",") if x.strip()]),
        )
        db.session.add(field)
        db.session.commit()
        flash("Custom field added", "success")
    fields = EmployeeCustomField.query.all()
    return render_template("custom_fields.html", fields=fields)


@app.route("/attendance", methods=["GET", "POST"])
@role_required("Admin", "HR", "Manager")
def attendance():
    if request.method == "POST":
        db.session.add(
            Attendance(
                employee_id=request.form["employee_id"],
                attendance_date=datetime.strptime(request.form["attendance_date"], "%Y-%m-%d").date(),
                status=request.form["status"],
                worked_shift_id=request.form.get("worked_shift_id") or None,
                overtime_hours=request.form.get("overtime_hours") or 0,
            )
        )
        db.session.commit()
        flash("Attendance saved", "success")
    return render_template("attendance.html", employees=Employee.query.all(), shifts=Shift.query.all(), records=Attendance.query.order_by(Attendance.attendance_date.desc()).limit(50).all())


@app.route("/payroll/run", methods=["POST"])
@role_required("Admin", "HR")
def payroll_run():
    cycle_start, cycle_end = payroll_cycle_for(date.today())
    for emp in Employee.query.all():
        gross, deductions, net, breakdown = calc_payroll(emp, cycle_start, cycle_end)
        row = Payroll(employee_id=emp.id, cycle_start=cycle_start, cycle_end=cycle_end, gross_salary=gross, total_deductions=deductions, net_salary=net, breakdown_json=json.dumps(breakdown))
        db.session.add(row)
    db.session.commit()
    flash("Payroll processed", "success")
    return redirect(url_for("payroll_view"))


@app.route("/payroll")
@role_required("Admin", "HR", "Employee")
def payroll_view():
    records = Payroll.query.order_by(Payroll.created_at.desc()).limit(100).all()
    employees_map = {e.id: e for e in Employee.query.all()}
    return render_template("payroll.html", records=records, employees_map=employees_map)


@app.route("/leaves", methods=["GET", "POST"])
@role_required("Admin", "HR", "Manager", "Employee")
def leaves():
    if request.method == "POST":
        db.session.add(Leave(employee_id=request.form["employee_id"], leave_type=request.form["leave_type"], start_date=datetime.strptime(request.form["start_date"], "%Y-%m-%d").date(), end_date=datetime.strptime(request.form["end_date"], "%Y-%m-%d").date(), days=request.form["days"], reason=request.form.get("reason", "")))
        db.session.commit()
        flash("Leave request submitted", "success")
    return render_template("leaves.html", records=Leave.query.order_by(Leave.created_at.desc()).all(), employees=Employee.query.all())


@app.route("/crm", methods=["GET", "POST"])
@role_required("Admin", "HR", "Manager")
def crm():
    if request.method == "POST":
        db.session.add(CrmLead(lead_name=request.form["lead_name"], client_company=request.form["client_company"], contact=request.form["contact"], status=request.form["status"], follow_up_date=datetime.strptime(request.form["follow_up_date"], "%Y-%m-%d").date() if request.form.get("follow_up_date") else None, notes=request.form.get("notes", "")))
        db.session.commit()
        flash("Lead saved", "success")
    return render_template("crm.html", leads=CrmLead.query.order_by(CrmLead.created_at.desc()).all())


@app.route("/announcements", methods=["GET", "POST"])
@role_required("Admin", "HR")
def announcements():
    if request.method == "POST":
        db.session.add(Announcement(title=request.form["title"], message=request.form["message"], posted_by=session["user_id"]))
        db.session.commit()
        flash("Announcement posted", "success")
    return render_template("announcements.html", rows=Announcement.query.order_by(Announcement.created_at.desc()).all())


@app.route("/settings", methods=["GET", "POST"])
@role_required("Admin")
def settings():
    if request.method == "POST":
        db.session.add(Shift(name=request.form["name"], start_time=request.form["start_time"], end_time=request.form["end_time"]))
        db.session.commit()
    return render_template("settings.html", shifts=Shift.query.all(), templates=SalaryTemplate.query.all())


def seed_data():
    if User.query.count() == 0:
        admin = User(username="admin", email="admin@company.local", password_hash=generate_password_hash("Admin@123"), role="Admin")
        hr = User(username="hr", email="hr@company.local", password_hash=generate_password_hash("Hr@12345"), role="HR")
        db.session.add_all([admin, hr])
    if Shift.query.count() == 0:
        db.session.add_all([
            Shift(name="General", start_time="09:00", end_time="17:00"),
            Shift(name="Evening", start_time="14:00", end_time="22:00"),
        ])
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)
