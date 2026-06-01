import logging
import os
import time
import uuid
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "logdesk-lab-secret"

# В учебном проекте данные хранятся в памяти.
# После перезапуска приложения заявки очищаются.
tickets = []
next_id = 1


def setup_logging():
    """Настройка логирования в файл и консоль."""
    log_file = os.path.join(LOG_DIR, "app.log")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler_exists = any(
        isinstance(handler, RotatingFileHandler) for handler in app.logger.handlers
    )

    if not file_handler_exists:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    console_handler_exists = any(
        isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler)
        for handler in app.logger.handlers
    )

    if not console_handler_exists:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.INFO)


setup_logging()


@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())[:8]
    g.start_time = time.time()

    app.logger.info(
        "REQUEST START | id=%s | method=%s | path=%s | ip=%s",
        g.request_id,
        request.method,
        request.path,
        request.remote_addr
    )


@app.after_request
def after_request(response):
    start_time = getattr(g, "start_time", time.time())
    duration = round((time.time() - start_time) * 1000, 2)
    request_id = getattr(g, "request_id", "unknown")

    app.logger.info(
        "REQUEST END | id=%s | method=%s | path=%s | status=%s | duration_ms=%s",
        request_id,
        request.method,
        request.path,
        response.status_code,
        duration
    )

    return response


@app.errorhandler(Exception)
def handle_exception(error):
    request_id = getattr(g, "request_id", "unknown")

    app.logger.exception(
        "SERVER ERROR | id=%s | path=%s | error=%s",
        request_id,
        request.path,
        str(error)
    )

    return render_template(
        "error.html",
        request_id=request_id,
        error_message="Произошла внутренняя ошибка сервера."
    ), 500


@app.route("/")
def index():
    app.logger.info("PAGE OPENED | Главная страница открыта")
    return render_template("index.html", tickets=tickets)


@app.route("/tickets", methods=["POST"])
def create_ticket():
    global next_id

    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    priority = request.form.get("priority", "").strip()

    app.logger.info(
        "CREATE TICKET ATTEMPT | title=%s | category=%s | priority=%s",
        title,
        category,
        priority
    )

    if not title:
        app.logger.warning("VALIDATION ERROR | Попытка создать заявку без названия")
        flash("Название заявки не может быть пустым.", "error")
        return redirect(url_for("index"))

    if priority not in ["low", "medium", "high"]:
        app.logger.warning(
            "VALIDATION ERROR | Некорректный приоритет заявки: %s",
            priority
        )
        flash("Некорректный приоритет заявки.", "error")
        return redirect(url_for("index"))

    ticket = {
        "id": next_id,
        "title": title,
        "category": category or "Без категории",
        "priority": priority,
        "status": "new"
    }

    tickets.append(ticket)
    next_id += 1

    app.logger.info(
        "TICKET CREATED | id=%s | title=%s | priority=%s",
        ticket["id"],
        ticket["title"],
        ticket["priority"]
    )

    flash("Заявка успешно создана.", "success")
    return redirect(url_for("index"))


@app.route("/tickets/<int:ticket_id>/status", methods=["POST"])
def change_status(ticket_id):
    new_status = request.form.get("status", "").strip()

    app.logger.info(
        "STATUS CHANGE ATTEMPT | ticket_id=%s | new_status=%s",
        ticket_id,
        new_status
    )

    if new_status not in ["new", "in_progress", "done"]:
        app.logger.warning(
            "VALIDATION ERROR | Некорректный статус: %s",
            new_status
        )
        flash("Некорректный статус заявки.", "error")
        return redirect(url_for("index"))

    for ticket in tickets:
        if ticket["id"] == ticket_id:
            old_status = ticket["status"]
            ticket["status"] = new_status

            app.logger.info(
                "STATUS CHANGED | ticket_id=%s | old_status=%s | new_status=%s",
                ticket_id,
                old_status,
                new_status
            )

            flash("Статус заявки изменён.", "success")
            return redirect(url_for("index"))

    app.logger.warning("NOT FOUND | Заявка не найдена: %s", ticket_id)
    flash("Заявка не найдена.", "error")
    return redirect(url_for("index"))


@app.route("/tickets/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id):
    app.logger.info("DELETE ATTEMPT | ticket_id=%s", ticket_id)

    for ticket in list(tickets):
        if ticket["id"] == ticket_id:
            tickets.remove(ticket)
            app.logger.info("TICKET DELETED | ticket_id=%s", ticket_id)
            flash("Заявка удалена.", "success")
            return redirect(url_for("index"))

    app.logger.warning("DELETE FAILED | Заявка не найдена: %s", ticket_id)
    flash("Заявка не найдена.", "error")
    return redirect(url_for("index"))


@app.route("/debug/crash")
def debug_crash():
    app.logger.error("DEBUG CRASH | Пользователь вызвал учебную ошибку")
    raise RuntimeError("Учебная ошибка для демонстрации логирования и отладки")


@app.route("/debug/slow")
def debug_slow():
    app.logger.warning("DEBUG SLOW | Запущен медленный запрос")
    time.sleep(2)
    flash("Медленный запрос выполнен.", "success")
    return redirect(url_for("index"))


@app.route("/api/tickets", methods=["GET"])
def api_get_tickets():
    app.logger.info("API GET TICKETS | count=%s", len(tickets))

    return jsonify({
        "status": "success",
        "count": len(tickets),
        "tickets": tickets
    }), 200


@app.route("/test/reset", methods=["POST"])
def test_reset():
    global next_id

    tickets.clear()
    next_id = 1

    app.logger.info("TEST RESET | Данные очищены для тестов")

    return jsonify({
        "status": "success",
        "message": "Данные очищены"
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
