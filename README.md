# HR + Payroll + CRM (Flask)

## Folder Structure

```
employee-payroll-system/
├── app.py
├── requirements.txt
├── uploads/
├── static/
│   ├── style.css
│   └── js/app.js
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── employees.html
    ├── attendance.html
    ├── leaves.html
    ├── payroll.html
    ├── crm.html
    ├── announcements.html
    ├── custom_fields.html
    └── settings.html
```

## Setup
1. `python -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. Login with `admin / Admin@123`

## Notes
- SQLite-first schema with normalized entities and MySQL-friendly naming.
- Payroll cycle is 26th → 25th.
- Dynamic employee fields are stored in `employee_custom_fields` and `employee_custom_values`.
- Document uploads are saved into `uploads/` with secure file names.

## API/Feature coverage
- Auth + roles: Admin, HR, Manager, Employee
- Employee CRUD scaffold + salary composition
- Attendance, leave, payroll, CRM, announcements, settings scaffolds
- Payroll calculation rules for SM, Labour, ANL in `calc_payroll()`
