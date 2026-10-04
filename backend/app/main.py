from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import services

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
router = APIRouter()


async def _optional_user(request: Request) -> dict | None:
    from server import current_user

    try:
        return await current_user(request)
    except HTTPException as error:
        if error.status_code == 401:
            return None
        raise


def _auth_page(request: Request, mode: str, error: str = "", form: dict | None = None):
    return templates.TemplateResponse(
        request=request,
        name="pages/auth.html",
        context={
            "request": request,
            "current_user": None,
            "mode": mode,
            "error": error,
            "form": form or {},
            "notice": request.query_params.get("notice", ""),
        },
    )


@router.get("/")
async def home(request: Request):
    user = await _optional_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={
            "request": request,
            "current_user": user,
            "active_page": "discover",
            "notice": request.query_params.get("notice", ""),
        },
    )


@router.get("/login")
async def login_page(request: Request):
    if await _optional_user(request):
        return RedirectResponse("/", status_code=303)
    return _auth_page(request, "login")


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    from server import LoginInput, db, set_auth_cookie

    form = {"username": username}
    try:
        data = LoginInput(username=username, password=password)
    except ValidationError as error:
        message = "; ".join(item["msg"] for item in error.errors())
        return _auth_page(request, "login", message, form)

    user = await services.authenticate_user(db, data.username, data.password)
    if not user:
        return _auth_page(request, "login", "That username or password is not right", form)
    response = RedirectResponse("/?notice=Signed%20in", status_code=303)
    set_auth_cookie(response, user)
    return response


@router.get("/register")
async def register_page(request: Request):
    if await _optional_user(request):
        return RedirectResponse("/", status_code=303)
    return _auth_page(request, "register")


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
    skills: str = Form("Python, Design"),
):
    from server import RegisterInput, db, set_auth_cookie

    form = {
        "username": username,
        "name": name,
        "role": role,
        "department": department,
        "skills": skills,
    }
    try:
        data = RegisterInput(
            username=username,
            password=password,
            name=name,
            role=role,
            department=department,
            skills=[item.strip() for item in skills.split(",") if item.strip()],
        )
    except ValidationError as error:
        message = "; ".join(item["msg"] for item in error.errors())
        return _auth_page(request, "register", message, form)

    user = await services.register_user(
        db,
        username=data.username,
        password=data.password,
        name=data.name,
        role=data.role,
        department=data.department,
        skills=data.skills,
    )
    if not user:
        return _auth_page(request, "register", "That username is already taken", form)
    response = RedirectResponse("/?notice=Profile%20created", status_code=303)
    set_auth_cookie(response, user)
    return response


@router.post("/logout")
async def logout():
    from server import clear_auth_cookie

    response = RedirectResponse("/login?notice=Signed%20out", status_code=303)
    clear_auth_cookie(response)
    return response