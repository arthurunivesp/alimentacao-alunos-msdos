from flask import Blueprint, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

alunos = {}
grupos_alimentos = {
    "LEITE": ["Leite puro", "Achocolatado", "Vitamina", "Iogurte"],
    "LEGUMES": ["Abóbora", "Abobrinha", "Quiabo", "Berinjela", "Tomate", "Pepino", "Brócolis", "Couve-flor"],
    "VERDURAS": ["Acelga", "Agrião", "Alface", "Espinafre", "Repolho"],
    "TUBÉRCULOS": ["Batata", "Mandioquinha"],
    "PROTEÍNA": ["Carne bovina", "Suína", "Aves", "Peixes", "Ovos"],
    "CEREAIS": ["Arroz", "Pão", "Bolacha"],
    "GRÃOS": ["Feijão"],
    "FRUTAS": ["Banana", "Maçã", "Mamão", "Melancia"],
    "SUCO DE FRUTAS": ["Sucos diversos"],
    
}

USUARIOS = {
    'admin': {'senha': 'senha', 'role': 'admin'},
    'responsavel1': {'senha': 'alimentacao1', 'role': 'alimentacao'},
    'responsavel2': {'senha': 'alimentacao2', 'role': 'alimentacao'}
}

calendario_alimentacao = {}

@main_bp.route('/admin', methods=['GET', 'POST'])
def admin():
    print(f"Usuário na página admin (role na sessão): {session.get('role')}")
    if request.method == 'POST':
        aluno_nome = request.form.get('aluno_nome')
        restricoes = request.form.getlist('restricoes')
        if aluno_nome and aluno_nome not in alunos:
            alunos[aluno_nome] = restricoes
            return redirect(url_for('main.admin'))
    return render_template('admin.html', alunos=alunos, grupos_alimentos=grupos_alimentos)

@main_bp.route('/alimentacao', methods=['GET'])
def alimentacao():
    print(f"Usuário na página alimentacao (role na sessão): {session.get('role')}")
    aluno_selecionado = request.args.get('aluno_nome')
    eventos_aluno = []
    for data, eventos in calendario_alimentacao.items():
        for evento in eventos:
            if evento['aluno'] == aluno_selecionado:
                eventos_aluno.append({'data': data, 'evento': evento})
    return render_template('alimentacao.html', alunos=alunos, aluno_selecionado=aluno_selecionado, eventos_aluno=eventos_aluno)

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USUARIOS and USUARIOS[username]['senha'] == password:
            user_role = USUARIOS[username]['role']
            session['role'] = user_role
            print(f"Usuário '{username}' logado com sucesso como '{user_role}'. Role salva na sessão.")
            if user_role == 'admin':
                return redirect(url_for('main.admin'))
            elif user_role == 'alimentacao':
                return redirect(url_for('main.alimentacao'))
        else:
            error = 'Usuário ou senha inválidos.'
    return render_template('login.html', error=error)

@main_bp.route('/logout')
def logout():
    session.pop('role', None)
    return redirect(url_for('main.login'))

@main_bp.route('/calendario')
def calendario():
    return render_template('calendario.html', calendario=calendario_alimentacao)

@main_bp.route('/adicionar_evento', methods=['GET', 'POST'])
def adicionar_evento():
    if request.method == 'POST':
        aluno_existente = request.form.get('aluno_existente')
        novo_aluno = request.form.get('novo_aluno')
        data_str = request.form.get('data')
        refeicao = request.form.get('refeicao')
        alimentos = request.form.getlist('alimentos')
        observacoes = request.form.get('observacoes')

        aluno_nome = aluno_existente if aluno_existente else novo_aluno

        if aluno_nome:
            try:
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                return "Formato de data inválido."

            if data not in calendario_alimentacao:
                calendario_alimentacao[data] = []

            calendario_alimentacao[data].append({
                'aluno': aluno_nome,
                'refeicao': refeicao,
                'alimentos': alimentos,
                'observacoes': observacoes
            })

            if novo_aluno and novo_aluno not in alunos:
                alunos[novo_aluno] = []

            return redirect(url_for('main.calendario'))
        else:
            return "Por favor, selecione um aluno existente ou digite o nome de um novo aluno."
    else:
        return render_template('adicionar_evento.html', alunos=alunos, grupos_alimentos=grupos_alimentos)