import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, ConversationHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuração de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(_name_)

# Estados da conversa
NOME, EMAIL, TELEFONE, IDADE, TESTE = range(5)

# Perguntas do teste
PERGUNTAS = [
    {
        "numero": 1,
        "pergunta": "Na escola você prefere/preferia assuntos ligados a:",
        "opcoes": [
            "a) Arte, esportes e atividades extracurriculares",
            "b) Biologia e genética",
            "c) Ciências humanas e idiomas",
            "d) Ciências exatas"
        ]
    },
    {
        "numero": 2,
        "pergunta": "Você prefere levar sua vida:",
        "opcoes": [
            "a) Com pouca rotina e poucas regras",
            "b) Com regras e disciplinas",
            "c) Interagindo com todo tipo de pessoa",
            "d) Com muita autonomia: 'na sua'"
        ]
    },
    {
        "numero": 3,
        "pergunta": "Você se descreveria como uma pessoa:",
        "opcoes": [
            "a) Impulsiva e um tanto aventureira",
            "b) Cautelosa e responsável",
            "c) Entusiasmada e muito amiga",
            "d) Calma e diferente da maioria"
        ]
    },
    {
        "numero": 4,
        "pergunta": "Você se considera uma pessoa:",
        "opcoes": [
            "a) Prática e hábil para improvisar",
            "b) Batalhadora que sabe o que quer",
            "c) Preocupada com questões humanas",
            "d) Capacitada para criar e inventar"
        ]
    },
    {
        "numero": 5,
        "pergunta": "De quais características você sente orgulho:",
        "opcoes": [
            "a) Audácia e facilidade para lidar com o inesperado",
            "b) Senso de dever e capacidade de dar exemplo",
            "c) Idealismo e disposição para compreender os outros",
            "d) Engenhosidade e rapidez mental"
        ]
    },
    {
        "numero": 6,
        "pergunta": "Costuma confiar mais em:",
        "opcoes": [
            "a) Percepção imediata",
            "b) Costumes e tradições",
            "c) Intuição",
            "d) Razão e lógica"
        ]
    },
    {
        "numero": 7,
        "pergunta": "Quase sempre você gosta de:",
        "opcoes": [
            "a) Causar impacto: os holofotes o atraem",
            "b) Ser visto como um membro valioso de um grupo",
            "c) Sonhar em transformar o mundo",
            "d) Desvendar um enigma ou inventar algo útil"
        ]
    },
    {
        "numero": 8,
        "pergunta": "A vida é mais interessante quando você tem:",
        "opcoes": [
            "a) Desafios e situações que mudam com o tempo",
            "b) Segurança, emprego garantido, integração social",
            "c) Possibilidade de fazer algo para mudar o mundo",
            "d) Possibilidade de ir além do que já é conhecido"
        ]
    },
    {
        "numero": 9,
        "pergunta": "Você gostaria de ser:",
        "opcoes": [
            "a) Um craque na profissão que escolher",
            "b) Um executivo bem-sucedido",
            "c) Um profissional de prestígio",
            "d) Um especialista ou cientista"
        ]
    },
    {
        "numero": 10,
        "pergunta": "Você é muito bom(boa) lidando com:",
        "opcoes": [
            "a) Ferramentas, instrumentos, equipamentos",
            "b) Controle do tempo, comando e execução",
            "c) Pessoas de todos os níveis culturais e sociais",
            "d) Sistemas de construção (material ou mental)"
        ]
    },
    {
        "numero": 11,
        "pergunta": "Antes de agir, você analisa:",
        "opcoes": [
            "a) Vantagens imediatas",
            "b) Experiências já vividas",
            "c) As possibilidades futuras",
            "d) As condições e consequências"
        ]
    },
    {
        "numero": 12,
        "pergunta": "Gosta quando as pessoas:",
        "opcoes": [
            "a) O surpreendem com um presente",
            "b) Expressam gratidão por algo que fez",
            "c) Reconhecem sua personalidade singular",
            "d) Reconhecem sua inteligência"
        ]
    },
    {
        "numero": 13,
        "pergunta": "Você costuma abraçar um novo projeto:",
        "opcoes": [
            "a) Com a cara e a coragem",
            "b) Guiado pela experiência",
            "c) Confiando na intuição e na criatividade",
            "d) Depois de verificar todas as variáveis"
        ]
    },
    {
        "numero": 14,
        "pergunta": "Geralmente você prefere agir:",
        "opcoes": [
            "a) No calor do momento",
            "b) Com segurança e conforme o costume",
            "c) Quando está inspirado",
            "d) Quando um problema o desafia"
        ]
    },
    {
        "numero": 15,
        "pergunta": "Você fica motivado(a) quando:",
        "opcoes": [
            "a) Tem a oportunidade de superar obstáculos",
            "b) Experimenta estabilidade na vida profissional",
            "c) Harmonia e inspiração guiam a atividade",
            "d) Há liberdade para projetar o futuro"
        ]
    },
    {
        "numero": 16,
        "pergunta": "Em atividades de grupos, você prefere:",
        "opcoes": [
            "a) As desafiadoras, que exigem ação rápida",
            "b) Administrar os recursos disponíveis",
            "c) Motivar as pessoas para darem o melhor de si",
            "d) Descartar logo o que não funciona"
        ]
    },
    {
        "numero": 17,
        "pergunta": "Liderar é uma atividade que gosta de exercer:",
        "opcoes": [
            "a) Por pouco tempo e dependendo da situação",
            "b) Quando pode comandar do começo ao fim",
            "c) Quando é preciso identificar e reunir talentos",
            "d) Quando o raciocínio estratégico é necessário"
        ]
    },
    {
        "numero": 18,
        "pergunta": "Em uma escola você gostaria de ser:",
        "opcoes": [
            "a) Professor de educação física",
            "b) Diretor",
            "c) Professor de literatura",
            "d) Professor de matemática ou física"
        ]
    },
    {
        "numero": 19,
        "pergunta": "É um elogio quando se referem a você como:",
        "opcoes": [
            "a) Corajoso, otimista e divertido",
            "b) Cauteloso, responsável e aplicado",
            "c) Harmonioso, íntegro e sábio",
            "d) Uma mente brilhante"
        ]
    },
    {
        "numero": 20,
        "pergunta": "Frases que têm a ver com você:",
        "opcoes": [
            "a) 'Deixo a vida me levar'",
            "b) 'Manda quem pode, obedece quem tem juízo'",
            "c) 'Para seu próprio interesse, seja verdadeiro'",
            "d) 'Penso, logo existo'"
        ]
    }
]

# Resultados dos perfis
PERFIS = {
    'A': {
        'titulo': '🎯 PERFIL A - Dinâmico e Enérgico',
        'descricao': 'A principal característica das pessoas do tipo A é sua energia e dinamismo. Elas têm predileção por atividades e novidades, demonstrando habilidades físicas e uma ótima comunicação corporal. Geralmente evitam a monotonia e encaram o trabalho como uma grande fonte de satisfação e alegria.',
        'carreiras': ['Anestesista', 'Ator', 'Cineasta', 'Chefe de cozinha', 'Cirurgião', 'Coreógrafo', 'Dançarino', 'Dermatologista', 'Estilista', 'Esportista', 'Guia de turismo', 'Instrumentador cirúrgico', 'Jornalista', 'Médico clínico', 'Músico', 'Paisagista', 'Personal trainer', 'Personal stylist', 'Piloto', 'Publicitário', 'Roteirista']
    },
    'B': {
        'titulo': '💼 PERFIL B - Organizado e Responsável',
        'descricao': 'Comando e responsabilidades são duas palavras que definem as pessoas do tipo B. Elas gostam de lidar com fatos, quantidades, análises, organização e planejamento. O tipo B trabalha duro e prefere profissões que lhes proporcione status e possibilidade de crescimento.',
        'carreiras': ['Administração', 'Advogado', 'Assistente social', 'Bibliotecário', 'Delegado', 'Engenheiro mecânico/químico', 'Juiz de direito', 'Pastor/Padre/Rabino', 'Policial', 'Promotor público', 'Defensor público']
    },
    'C': {
        'titulo': '❤️ PERFIL C - Humanista e Intuitivo',
        'descricao': 'Facilmente reconhecidos por seu entusiasmo e interesse nas relações humanas, as pessoas do tipo C têm a intuição como seu ponto forte. Muitas endereçam seus esforços e talentos para o desenvolvimento intelectual de alunos e colegas de trabalho.',
        'carreiras': ['Artista plástico', 'Dramaturgo', 'Educador', 'Escritor', 'Filósofo', 'Jornalista', 'Pedagogo', 'Tradutor', 'Professor', 'Psicólogo', 'Psiquiatra', 'Sociólogo', 'Terapeuta ocupacional']
    },
    'D': {
        'titulo': '🧠 PERFIL D - Analítico e Estratégico',
        'descricao': 'São intuitivos, mas em vez de se preocupar com as pessoas, costumam focar seus interesses em grandes áreas do conhecimento como a ciência e tecnologia. Apresentam notável capacidade para identificar problemas concretos e resolvê-los, bem como para o raciocínio abstrato.',
        'carreiras': ['Analista de sistemas', 'Antropólogo', 'Arquiteto', 'Astrônomo', 'Criador de software', 'Designer industrial', 'Economista', 'Engenheiro', 'Físico', 'CEO', 'Matemático', 'Militar', 'Oceanógrafo', 'Pesquisador', 'Químico', 'Maestro', 'Urbanista', 'Zoólogo']
    }
}

# Função para conectar ao Google Sheets
def conectar_google_sheets():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open('Teste Vocacional - Respostas').sheet1
        return sheet
    except Exception as e:
        logger.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    mensagem_boas_vindas = (
        "🎓 BEM-VINDO AO TESTE VOCACIONAL! 🎓\n\n"
        "Esse teste não tem respostas certas ou erradas, ele serve para te ajudar "
        "a se conhecer melhor, descobrir o que você gosta de fazer, suas habilidades "
        "e qual tipo de trabalho combina mais com você.\n\n"
        "🌟 Lembre-se: o primeiro emprego é uma oportunidade de aprendizado e crescimento. "
        "O mais importante é identificar áreas onde você pode se sentir bem, desenvolver "
        "seus talentos e abrir portas para o futuro.\n\n"
        "✍️ Responda com sinceridade, pense em você, no que realmente gosta e acredita.\n\n"
        "Vamos começar! Primeiro, preciso de algumas informações suas.\n\n"
        "📝 Qual é o seu nome completo?"
    )
    await update.message.reply_text(mensagem_boas_vindas, parse_mode='Markdown')
    return NOME

# Coletar nome
async def coletar_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['nome'] = update.message.text
    await update.message.reply_text("📧 Qual é o seu e-mail?", parse_mode='Markdown')
    return EMAIL

# Coletar email
async def coletar_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("📱 Qual é o seu telefone?", parse_mode='Markdown')
    return TELEFONE

# Coletar telefone
async def coletar_telefone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['telefone'] = update.message.text
    await update.message.reply_text("🎂 Qual é a sua idade?", parse_mode='Markdown')
    return IDADE

# Coletar idade e iniciar teste
async def coletar_idade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['idade'] = update.message.text
    context.user_data['respostas'] = {}
    context.user_data['pontuacao'] = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
    context.user_data['pergunta_atual'] = 0
    
    await update.message.reply_text(
        "✅ Ótimo! Agora vamos começar o teste.\n\n"
        "São 20 perguntas. Para cada pergunta, escolha a alternativa que mais combina com você.\n\n"
        "Vamos lá! 🚀",
        parse_mode='Markdown'
    )
    
    return await enviar_pergunta(update, context)

# Enviar pergunta
async def enviar_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pergunta_num = context.user_data['pergunta_atual']
    
    if pergunta_num >= len(PERGUNTAS):
        return await finalizar_teste(update, context)
    
    pergunta = PERGUNTAS[pergunta_num]
    
    keyboard = []
    for opcao in pergunta['opcoes']:
        letra = opcao[0].upper()
        keyboard.append([InlineKeyboardButton(opcao, callback_data=f"resp_{letra}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    texto = f"Pergunta {pergunta['numero']}/20\n\n{pergunta['pergunta']}"
    
    if update.callback_query:
        await update.callback_query.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
    
    return TESTE

# Processar resposta
async def processar_resposta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    resposta = query.data.split('_')[1]
    pergunta_num = context.user_data['pergunta_atual']
    
    context.user_data['respostas'][pergunta_num] = resposta
    context.user_data['pontuacao'][resposta] += 1
    context.user_data['pergunta_atual'] += 1
    
    await query.edit_message_text(f"✅ Resposta registrada: {resposta}")
    
    return await enviar_pergunta(update, context)

# Finalizar teste
async def finalizar_teste(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pontuacao = context.user_data['pontuacao']
    perfil_resultado = max(pontuacao, key=pontuacao.get)
    
    perfil = PERFIS[perfil_resultado]
    
    # Salvar dados no Google Sheets
    sheet = conectar_google_sheets()
    if sheet:
        try:
            dados = [
                datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                context.user_data['nome'],
                context.user_data['email'],
                context.user_data['telefone'],
                context.user_data['idade'],
                perfil_resultado,
                pontuacao['A'],
                pontuacao['B'],
                pontuacao['C'],
                pontuacao['D'],
                ', '.join([f"Q{k+1}:{v}" for k, v in context.user_data['respostas'].items()])
            ]
            sheet.append_row(dados)
        except Exception as e:
            logger.error(f"Erro ao salvar no Google Sheets: {e}")
    
    # Montar mensagem de resultado
    resultado_msg = (
        f"🎉 TESTE CONCLUÍDO! 🎉\n\n"
        f"{perfil['titulo']}\n\n"
        f"📊 Sua pontuação:\n"
        f"A: {pontuacao['A']} | B: {pontuacao['B']} | C: {pontuacao['C']} | D: {pontuacao['D']}\n\n"
        f"📝 Descrição do seu perfil:\n{perfil['descricao']}\n\n"
        f"💼 Carreiras sugeridas:\n"
    )
    
    for i, carreira in enumerate(perfil['carreiras'], 1):
        resultado_msg += f"{i}. {carreira}\n"
    
    resultado_msg += (
        f"\n✨ Lembre-se: Este é apenas um guia! Você pode explorar diferentes áreas "
        f"e descobrir novos interesses ao longo da sua jornada profissional.\n\n"
        f"Obrigado por participar! 🚀"
    )
    
    if update.callback_query:
        await update.callback_query.message.reply_text(resultado_msg, parse_mode='Markdown')
    else:
        await update.message.reply_text(resultado_msg, parse_mode='Markdown')
    
    return ConversationHandler.END

# Cancelar
async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Teste cancelado. Use /start para começar novamente.")
    return ConversationHandler.END

def main():
    # Token do bot (você vai colocar o seu)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, coletar_nome)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, coletar_email)],
            TELEFONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, coletar_telefone)],
            IDADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, coletar_idade)],
            TESTE: [CallbackQueryHandler(processar_resposta)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
    )
    
    application.add_handler(conv_handler)
    
    application.run_polling()

if _name_ == '_main_':
    main()