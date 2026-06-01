import pytest

from app import app, tickets


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False

    with app.test_client() as client:
        client.post("/test/reset")
        yield client


def test_home_page_opens(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "LogDesk Lab".encode("utf-8") in response.data


def test_create_ticket_success(client):
    response = client.post(
        "/tickets",
        data={
            "title": "Ошибка входа",
            "category": "Авторизация",
            "priority": "high"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert len(tickets) == 1
    assert tickets[0]["title"] == "Ошибка входа"


def test_create_ticket_without_title_shows_error(client):
    response = client.post(
        "/tickets",
        data={
            "title": "",
            "category": "Интерфейс",
            "priority": "medium"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert "Название заявки не может быть пустым.".encode("utf-8") in response.data
    assert len(tickets) == 0


def test_api_returns_ticket_list(client):
    client.post(
        "/tickets",
        data={
            "title": "Проверить API",
            "category": "API",
            "priority": "low"
        }
    )

    response = client.get("/api/tickets")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "success"
    assert data["count"] == 1
    assert data["tickets"][0]["title"] == "Проверить API"


def test_debug_crash_returns_500(client):
    response = client.get("/debug/crash")

    assert response.status_code == 500
    assert "Ошибка сервера".encode("utf-8") in response.data
