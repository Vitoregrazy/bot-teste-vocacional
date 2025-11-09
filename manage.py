import getpass

from app import create_app, db
from app.models import Role, User

app = create_app()


@app.cli.command("init-db")
def init_db_command():
    """Cria as tabelas do banco de dados."""
    with app.app_context():
        db.create_all()
    print("Banco de dados criado/atualizado.")


@app.cli.command("create-admin")
def create_admin():
    """Cria um usuário administrador interativo."""
    username = input("Usuário: ")
    full_name = input("Nome completo: ")
    cpf = input("CPF: ")
    password = getpass.getpass("Senha: ")

    with app.app_context():
        if User.query.filter((User.username == username) | (User.cpf == cpf)).first():
            print("Usuário ou CPF já cadastrado.")
            return
        user = User(
            username=username,
            full_name=full_name,
            cpf=cpf,
            role=Role.ADMIN,
            active=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Usuário administrador criado com sucesso!")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Banco de dados atualizado.")
