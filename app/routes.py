import csv
import io
import os
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.utils import secure_filename

from . import db
from .models import Appointment, AppointmentStatus, Role, User

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
    Image = None


main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Credenciais inválidas", "danger")
        elif not user.active:
            flash("Usuário desativado", "danger")
        else:
            login_user(user)
            flash(f"Bem-vindo, {user.full_name.split()[0]}!", "success")
            next_page = request.args.get("next") or url_for("main.dashboard")
            return redirect(next_page)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("auth.login"))


@main_bp.before_request
def require_login():
    if request.endpoint and request.blueprint == "main" and not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.url))


@admin_bp.before_request
def require_admin():
    if request.blueprint == "admin" and (not current_user.is_authenticated or not current_user.is_admin):
        flash("Acesso restrito aos administradores.", "danger")
        return redirect(url_for("main.dashboard"))


@main_bp.route("/")
@login_required
def dashboard():
    total = Appointment.query.count()
    pending = Appointment.query.filter_by(status=AppointmentStatus.PENDING).count()
    confirmed = Appointment.query.filter_by(status=AppointmentStatus.CONFIRMED).count()
    completed = Appointment.query.filter_by(status=AppointmentStatus.COMPLETED).count()

    appointments_by_reason = (
        db.session.query(Appointment.reason, func.count(Appointment.id))
        .group_by(Appointment.reason)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        confirmed=confirmed,
        completed=completed,
        appointments_by_reason=appointments_by_reason,
    )


@main_bp.route("/agendamentos")
@login_required
def appointments_list():
    query = Appointment.query

    status = request.args.get("status")
    reason = request.args.get("reason")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if status and status in {item.value for item in AppointmentStatus}:
        query = query.filter_by(status=AppointmentStatus(status))
    if reason:
        query = query.filter_by(reason=reason)
    start_dt = _parse_iso_datetime(start_date)
    end_dt = _parse_iso_datetime(end_date)
    if start_dt:
        query = query.filter(Appointment.created_at >= start_dt)
    if end_dt:
        query = query.filter(Appointment.created_at <= end_dt)

    appointments = query.order_by(Appointment.created_at.desc()).all()
    reasons = sorted({appointment.reason for appointment in Appointment.query.all()})
    return render_template(
        "appointments/list.html",
        appointments=appointments,
        reasons=reasons,
        statuses=AppointmentStatus,
    )


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None



def _parse_iso_datetime(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


@main_bp.route("/agendamentos/novo", methods=["GET", "POST"])
@login_required
def appointment_new():
    if request.method == "POST":
        birth_date = _parse_date(request.form.get("birth_date"))

        appointment = Appointment(
            full_name=request.form.get("full_name"),
            cpf=request.form.get("cpf"),
            birth_date=birth_date,
            phone=request.form.get("phone"),
            address=request.form.get("address"),
            neighborhood=request.form.get("neighborhood"),
            zipcode=request.form.get("zipcode"),
            reference_point=request.form.get("reference_point"),
            notes=request.form.get("notes"),
            reason=request.form.get("reason"),
            equipment=request.form.get("equipment"),
            registrant_name=request.form.get("registrant_name"),
            registrant_cpf=request.form.get("registrant_cpf"),
            assigned_user=current_user,
        )
        db.session.add(appointment)
        db.session.commit()

        flash("Agendamento criado com sucesso!", "success")
        return redirect(url_for("main.appointments_list"))

    return render_template(
        "appointments/form.html",
        appointment=None,
        reasons=_appointment_reasons(),
    )


def _appointment_reasons():
    return [
        "INCLUSÃO PBF",
        "ATUALIZAÇÃO PBF",
        "ATUALIZAÇÃO BPC LOAS",
        "INCLUSÃO PARA O LOAS",
        "APENAS ATUALIZAÇÃO",
        "MUDANÇA DE RESP. FAMILIAR",
        "CONTRADIÇÃO NO DISCURSO",
        "DENÚNCIA",
    ]


@main_bp.route("/agendamentos/<int:appointment_id>", methods=["GET", "POST"])
@login_required
def appointment_detail(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        abort(404)

    if request.method == "POST":
        appointment.full_name = request.form.get("full_name")
        appointment.cpf = request.form.get("cpf")
        appointment.birth_date = _parse_date(request.form.get("birth_date"))
        appointment.phone = request.form.get("phone")
        appointment.address = request.form.get("address")
        appointment.neighborhood = request.form.get("neighborhood")
        appointment.zipcode = request.form.get("zipcode")
        appointment.reference_point = request.form.get("reference_point")
        appointment.notes = request.form.get("notes")
        appointment.reason = request.form.get("reason")
        appointment.equipment = request.form.get("equipment")
        appointment.registrant_name = request.form.get("registrant_name")
        appointment.registrant_cpf = request.form.get("registrant_cpf")
        status_value = request.form.get("status")
        if status_value and status_value in {item.value for item in AppointmentStatus}:
            appointment.status = AppointmentStatus(status_value)
        appointment.visit_cadastrador = request.form.get("visit_cadastrador")
        appointment.visit_date = _parse_date(request.form.get("visit_date"))

        if current_user.is_admin:
            assigned_user_id = request.form.get("assigned_user_id")
            appointment.assigned_user_id = int(assigned_user_id) if assigned_user_id else None

        db.session.commit()
        flash("Agendamento atualizado com sucesso!", "success")
        return redirect(url_for("main.appointment_detail", appointment_id=appointment.id))

    users = User.query.order_by(User.full_name).all()
    return render_template(
        "appointments/detail.html",
        appointment=appointment,
        reasons=_appointment_reasons(),
        statuses=AppointmentStatus,
        users=users,
    )


@main_bp.route("/agendamentos/<int:appointment_id>/imprimir")
@login_required
def appointment_print(appointment_id):
    appointment = db.session.get(Appointment, appointment_id)
    if not appointment:
        abort(404)
    return render_template("appointments/print.html", appointment=appointment)


@main_bp.route("/relatorios", methods=["GET", "POST"])
@login_required
def reports():
    query = Appointment.query
    filters = {}
    reasons = _appointment_reasons()

    if request.method == "POST":
        filters = {
            "start_date": request.form.get("start_date"),
            "end_date": request.form.get("end_date"),
            "reason": request.form.get("reason"),
            "cadastrador": request.form.get("cadastrador"),
            "equipment": request.form.get("equipment"),
            "export": request.form.get("export"),
        }
    else:
        filters = {
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date"),
            "reason": request.args.get("reason"),
            "cadastrador": request.args.get("cadastrador"),
            "equipment": request.args.get("equipment"),
            "export": request.args.get("export"),
        }

    start_dt = _parse_iso_datetime(filters["start_date"])
    end_dt = _parse_iso_datetime(filters["end_date"])
    if start_dt:
        query = query.filter(Appointment.created_at >= start_dt)
    if end_dt:
        query = query.filter(Appointment.created_at <= end_dt)
    if filters["reason"] in reasons:
        query = query.filter_by(reason=filters["reason"])
    if filters["cadastrador"]:
        query = query.filter(Appointment.registrant_name.ilike(f"%{filters['cadastrador']}%"))
    if filters["equipment"]:
        query = query.filter(Appointment.equipment.ilike(f"%{filters['equipment']}%"))

    appointments = query.order_by(Appointment.created_at.desc()).all()

    if filters.get("export") == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "ID",
                "Nome Completo",
                "CPF",
                "Data Nascimento",
                "Telefone",
                "Endereço",
                "Bairro",
                "CEP",
                "Ponto de Referência",
                "Motivo",
                "Status",
                "Cadastrador",
                "Equipamento",
                "Data Criação",
                "Data Visita",
            ]
        )
        for appt in appointments:
            writer.writerow(
                [
                    appt.id,
                    appt.full_name,
                    appt.cpf,
                    appt.birth_date.strftime("%d/%m/%Y") if appt.birth_date else "",
                    appt.phone,
                    appt.address,
                    appt.neighborhood,
                    appt.zipcode,
                    appt.reference_point,
                    appt.reason,
                    appt.status.name,
                    appt.registrant_name,
                    appt.equipment,
                    appt.created_at.strftime("%d/%m/%Y"),
                    appt.visit_date.strftime("%d/%m/%Y") if appt.visit_date else "",
                ]
            )
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="relatorio_agendamentos.csv",
        )

    if filters.get("export") == "pdf":
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except ImportError:
            flash("Biblioteca ReportLab não instalada para geração de PDF.", "danger")
        else:
            buffer = io.BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            y = height - 50
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, y, "Relatório de Agendamentos")
            y -= 30
            pdf.setFont("Helvetica", 10)
            for appt in appointments:
                if y < 50:
                    pdf.showPage()
                    y = height - 50
                    pdf.setFont("Helvetica", 10)
                pdf.drawString(50, y, f"#{appt.id} - {appt.full_name} - {appt.reason} - {appt.status.name}")
                y -= 15
            pdf.save()
            buffer.seek(0)
            return send_file(
                buffer,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="relatorio_agendamentos.pdf",
            )

    cadastradores = [row[0] for row in db.session.query(Appointment.registrant_name).distinct() if row[0]]
    equipments = [row[0] for row in db.session.query(Appointment.equipment).distinct() if row[0]]

    return render_template(
        "reports.html",
        appointments=appointments,
        filters=filters,
        reasons=reasons,
        cadastradores=cadastradores,
        equipments=equipments,
    )


@main_bp.route("/configuracoes")
@login_required
def settings():
    return render_template("settings.html")


@main_bp.route("/ocr", methods=["POST"])
@login_required
def ocr_extract():
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Arquivo inválido."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return jsonify({"error": "Formato não suportado."}), 400

    filename = secure_filename(file.filename)
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(upload_path)

    if not pytesseract or not Image:
        return jsonify({"error": "Serviço de OCR indisponível no momento."}), 500

    try:
        image = Image.open(upload_path)
    except Exception as exc:
        return jsonify({"error": f"Não foi possível ler o arquivo: {exc}"}), 400

    try:
        text = pytesseract.image_to_string(image, lang="por")
    finally:
        try:
            os.remove(upload_path)
        except OSError:
            pass

    extracted = {
        "full_name": _extract_field(text, ["nome", "nome completo"]),
        "cpf": _extract_cpf(text),
        "birth_date": _extract_date(text),
    }

    return jsonify({"text": text, "fields": extracted})


def _extract_field(text: str, keywords: list[str]):
    lines = text.splitlines()
    for line in lines:
        for keyword in keywords:
            if keyword.lower() in line.lower():
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[1].strip()
                return line.replace(keyword, "", 1).strip()
    return None


def _extract_cpf(text: str):
    import re

    match = re.search(r"(\d{3}[\.\s]?\d{3}[\.\s]?\d{3}[-\s]?\d{2})", text)
    return match.group(1) if match else None


def _extract_date(text: str):
    import re

    match = re.search(r"(\d{2}[\/.-]\d{2}[\/.-]\d{4})", text)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date().isoformat()
        except ValueError:
            pass
    return None


@admin_bp.route("/usuarios")
@login_required
def users_list():
    users = User.query.order_by(User.full_name).all()
    return render_template("admin/users/list.html", users=users, roles=Role)


@admin_bp.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
def user_new():
    if not current_user.is_admin:
        abort(403)

    if request.method == "POST":
        username = request.form.get("username")
        cpf = request.form.get("cpf")

        if User.query.filter((User.username == username) | (User.cpf == cpf)).first():
            flash("Usuário já cadastrado.", "danger")
        else:
            user = User(
                username=username,
                full_name=request.form.get("full_name"),
                cpf=cpf,
                role=Role(request.form.get("role")),
                active=True,
            )
            user.set_password(request.form.get("password"))
            db.session.add(user)
            db.session.commit()
            flash("Usuário criado com sucesso!", "success")
            return redirect(url_for("admin.users_list"))

    return render_template("admin/users/form.html", user=None, roles=Role)


@admin_bp.route("/usuarios/<int:user_id>", methods=["GET", "POST"])
@login_required
def user_edit(user_id):
    if not current_user.is_admin:
        abort(403)

    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    if request.method == "POST":
        user.username = request.form.get("username")
        user.full_name = request.form.get("full_name")
        user.cpf = request.form.get("cpf")
        user.role = Role(request.form.get("role"))
        user.active = bool(request.form.get("active"))
        password = request.form.get("password")
        if password:
            user.set_password(password)
        db.session.commit()
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("admin.users_list"))

    return render_template("admin/users/form.html", user=user, roles=Role)


@admin_bp.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
@login_required
def user_delete(user_id):
    if not current_user.is_admin:
        abort(403)

    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    if user.id == current_user.id:
        flash("Você não pode excluir o seu próprio usuário.", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Usuário excluído com sucesso!", "success")
    return redirect(url_for("admin.users_list"))
