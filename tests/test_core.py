from datetime import date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, payroll_cycle_for


def test_payroll_cycle_before_26():
    start, end = payroll_cycle_for(date(2026, 5, 5))
    assert start == date(2026, 4, 26)
    assert end == date(2026, 5, 25)


def test_payroll_cycle_after_26():
    start, end = payroll_cycle_for(date(2026, 5, 26))
    assert start == date(2026, 5, 26)
    assert end == date(2026, 6, 25)


def test_login_page_loads():
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code == 200
