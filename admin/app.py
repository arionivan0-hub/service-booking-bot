import logging
import secrets
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import asyncpg
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

PG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
PG_USER, rest = PG_URL.split("@")[0], PG_URL.split("@")[1]
PG_PASSWORD = PG_USER.split(":")[1]
PG_USER = PG_USER.split(":")[0]
PG_HOST, PG_PORT_DB = rest.split(":")
PG_HOST, PG_PORT = PG_HOST, PG_PORT_DB.split("/")[0]
PG_DB = PG_PORT_DB.split("/")[1]

pool = None
security = HTTPBasic()

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTHS_RU = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
             "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = await asyncpg.create_pool(
        user=PG_USER, password=PG_PASSWORD,
        host=PG_HOST, port=int(PG_PORT), database=PG_DB,
        min_size=2, max_size=5,
    )
    yield
    await pool.close()


app = FastAPI(title="AutoPro Admin", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_user and correct_pass):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Unauthorized",
                            headers={"WWW-Authenticate": "Basic"})
    return credentials.username


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, tab: str = "appointments", status: str = "all",
                username: str = Depends(check_auth)):
    try:
        async with pool.acquire() as conn:
            users = await conn.fetch("SELECT id, telegram_id, name, phone FROM users ORDER BY id")
            services = await conn.fetch("SELECT id, name, price, duration FROM services ORDER BY id")

            status_filter = ""
            params = []
            if status and status != "all":
                status_filter = "WHERE a.status = $1"
                params.append(status)

            query = (
                "SELECT a.id, u.name AS user_name, u.phone, sv.name AS service_name, "
                "sv.price::int AS price, a.date, a.time_slot, a.status, "
                "a.created_at, a.cancelled_at, a.completed_at "
                "FROM appointments a "
                "JOIN users u ON a.user_id = u.id "
                "JOIN services sv ON a.service_id = sv.id "
                f"{status_filter} "
                "ORDER BY a.date DESC, a.time_slot DESC"
            )
            if params:
                appointments = await conn.fetch(query, *params)
            else:
                appointments = await conn.fetch(query)

            active_count = (await conn.fetchval("SELECT count(*) FROM appointments WHERE status='active'")) or 0
            total_count = (await conn.fetchval("SELECT count(*) FROM appointments")) or 0
            cancelled_count = (await conn.fetchval("SELECT count(*) FROM appointments WHERE status='cancelled'")) or 0
            completed_count = (await conn.fetchval("SELECT count(*) FROM appointments WHERE status='completed'")) or 0
            total_revenue = (await conn.fetchval(
                "SELECT COALESCE(sum(sv.price), 0) FROM appointments a "
                "JOIN services sv ON a.service_id = sv.id WHERE a.status = 'completed'"
            )) or 0

        return templates.TemplateResponse(request, "index.html", {
            "users": users, "services": services, "appointments": appointments,
            "active_count": active_count, "total_count": total_count,
            "cancelled_count": cancelled_count, "completed_count": completed_count,
            "total_revenue": total_revenue, "tab": tab, "status": status, "username": username,
        })
    except Exception as e:
        logger.exception("Admin error")
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>", status_code=500)


@app.get("/calendar", response_class=HTMLResponse)
async def calendar_view(request: Request, year: int = None, month: int = None,
                        day: int = None, username: str = Depends(check_auth)):
    now = datetime.utcnow()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    if day:
        date_str = f"{year}-{month:02d}-{day:02d}"
        return RedirectResponse(f"/calendar/day?date={date_str}", status_code=303)

    try:
        first_day = datetime(year, month, 1)
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - first_day).days

        start_weekday = first_day.weekday()

        async with pool.acquire() as conn:
            month_start = f"{year}-{month:02d}-01"
            month_end = f"{year}-{month:02d}-{days_in_month:02d}"
            booked = await conn.fetch(
                "SELECT a.date, count(*) as cnt "
                "FROM appointments a WHERE a.status = 'active' "
                "AND a.date >= $1 AND a.date <= $2 "
                "GROUP BY a.date", month_start, month_end
            )
            booked_map = {r["date"]: r["cnt"] for r in booked}

        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month_num = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1

        return templates.TemplateResponse(request, "calendar.html", {
            "year": year, "month": month,
            "month_name": MONTHS_RU[month],
            "weekdays": WEEKDAYS_RU,
            "days_in_month": days_in_month,
            "start_weekday": start_weekday,
            "booked_map": booked_map,
            "prev_year": prev_year, "prev_month": prev_month,
            "next_year": next_year, "next_month": next_month_num,
            "now": now, "username": username,
        })
    except Exception as e:
        logger.exception("Calendar error")
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>", status_code=500)


@app.get("/calendar/day", response_class=HTMLResponse)
async def calendar_day(request: Request, date: str, username: str = Depends(check_auth)):
    try:
        async with pool.acquire() as conn:
            appointments = await conn.fetch(
                "SELECT a.id, u.name AS user_name, u.phone, sv.name AS service_name, "
                "sv.price::int AS price, a.time_slot, a.status, a.created_at, a.cancelled_at "
                "FROM appointments a "
                "JOIN users u ON a.user_id = u.id "
                "JOIN services sv ON a.service_id = sv.id "
                "WHERE a.date = $1 "
                "ORDER BY a.time_slot", date
            )

        dt = datetime.strptime(date, "%Y-%m-%d")
        day_name = WEEKDAYS_RU[dt.weekday()]

        return templates.TemplateResponse(request, "calendar_day.html", {
            "date": date, "day_name": day_name,
            "appointments": appointments, "username": username,
        })
    except Exception as e:
        logger.exception("Calendar day error")
        return HTMLResponse(f"<h1>Error</h1><pre>{e}</pre>", status_code=500)


@app.post("/appointments/{appt_id}/cancel")
async def cancel_appointment(appt_id: int, username: str = Depends(check_auth)):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE appointments SET status='cancelled', cancelled_at=NOW() WHERE id=$1", appt_id
        )
    return RedirectResponse("/", status_code=303)


@app.post("/appointments/{appt_id}/complete")
async def complete_appointment(appt_id: int, username: str = Depends(check_auth)):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE appointments SET status='completed', completed_at=NOW() WHERE id=$1", appt_id
        )
    return RedirectResponse("/", status_code=303)


@app.post("/appointments/cleanup")
async def cleanup_appointments(status: str = Form("cancelled"), username: str = Depends(check_auth)):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM appointments WHERE status=$1", status)
    return RedirectResponse("/", status_code=303)


@app.post("/services/add")
async def add_service(name: str = Form(...), price: float = Form(...), duration: int = Form(...),
                       username: str = Depends(check_auth)):
    if name.strip() and price > 0 and duration > 0:
        async with pool.acquire() as conn:
            await conn.execute("INSERT INTO services (name, price, duration) VALUES ($1, $2, $3)",
                               name.strip(), price, duration)
    return RedirectResponse("/", status_code=303)


@app.post("/services/{svc_id}/edit")
async def edit_service(svc_id: int, name: str = Form(...), price: float = Form(...),
                        duration: int = Form(...), username: str = Depends(check_auth)):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE services SET name=$1, price=$2, duration=$3 WHERE id=$4",
                           name.strip(), price, duration, svc_id)
    return RedirectResponse("/", status_code=303)


@app.post("/services/{svc_id}/delete")
async def delete_service(svc_id: int, username: str = Depends(check_auth)):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM services WHERE id=$1", svc_id)
    return RedirectResponse("/", status_code=303)
