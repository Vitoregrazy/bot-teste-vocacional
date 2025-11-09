# Sistema de Agendamento de Visitas - CRAS

Este projeto implementa um site completo para gestão de agendamentos de visitas domiciliares do CRAS, com dashboard, cadastro de agendamentos, relatórios, gerenciamento de usuários e funcionalidade de OCR para preenchimento automático de dados.

## Principais recursos

- **Dashboard** com indicadores rápidos sobre os agendamentos.
- **Cadastro e edição** de agendamentos com todos os campos solicitados.
- **Visualização detalhada**, impressão e atualização do status das visitas.
- Campo dedicado para registrar o cadastrador que realizou a visita e a data correspondente.
- **Módulo de relatórios** com filtros por data, motivo, cadastrador e equipamento, além de exportação em CSV e PDF.
- **Gestão de usuários** com perfis de administrador e cadastrador, controle de acesso e fluxo de autenticação seguro.
- **Funcionalidade de OCR** que extrai dados (nome, CPF e data de nascimento) a partir de uma imagem enviada.

## Configuração do ambiente

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # No Windows use .venv\\Scripts\\activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure a base de dados e crie um usuário administrador:
   ```bash
   flask --app manage.py init-db  # cria o banco de dados SQLite
   flask --app manage.py create-admin
   ```

> **Observação:** para utilizar o OCR é necessário ter o mecanismo `Tesseract OCR` instalado no sistema operacional.

## Execução

Execute o servidor em modo desenvolvimento:

```bash
flask --app run.py run
```

O site estará disponível em `http://localhost:5000`.

## Estrutura de diretórios

- `app/` – código principal da aplicação Flask (modelos, rotas e templates).
- `app/templates/` – páginas HTML estruturadas com Bootstrap 5.
- `app/static/` – arquivos estáticos (CSS e scripts auxiliares).
- `manage.py` – utilitários de linha de comando para gerenciar o banco de dados e usuários.
- `run.py` – ponto de entrada para executar o aplicativo Flask.

## Dependências adicionais

Além das bibliotecas Flask, o projeto utiliza:

- `pytesseract` e `Pillow` para OCR.
- `reportlab` para geração de relatórios em PDF.
- `Flask-Login`, `Flask-Migrate` e `Flask-WTF` para autenticação, migrações de banco e proteção CSRF.

## Licença

Este projeto pode ser adaptado e utilizado livremente conforme a necessidade da equipe do CRAS.
