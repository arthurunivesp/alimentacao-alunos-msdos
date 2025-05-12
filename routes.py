from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash, send_file
from datetime import datetime, timedelta
from functools import wraps
from calendar import monthrange
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Define o backend para geração de gráficos sem interface gráfica
import matplotlib.pyplot as plt
import seaborn as sns  # Biblioteca para gráficos mais bonitos
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ================== CONFIGURAÇÃO INICIAL ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMP_DIR = "/tmp" if os.getenv("VERCEL") else STATIC_DIR  # Usa /tmp no Vercel, static localmente
PDF_DIR = os.path.join(TEMP_DIR, "pdfs")

if not os.getenv("VERCEL") and not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

main_bp = Blueprint('main', __name__)

TURMAS_DEFAULT = ["Turma A", "Turma B", "Turma C"]

def init_session():
    if 'alunos' not in session:
        session['alunos'] = {}
    if 'calendario_alimentacao' not in session:
        session['calendario_alimentacao'] = {}
    if 'grupos_alimentos' not in session:
        session['grupos_alimentos'] = {
            "LEITE": ["Leite puro", "Achocolatado", "Vitamina", "Iogurte"],
            "LEGUMES": ["Abóbora", "Abobrinha", "Quiabo", "Berinjela", "Tomate", "Pepino", "Brócolis", "Couve-flor"],
            "VERDURAS": ["Acelga", "Agrião", "Alface", "Espinafre", "Repolho"],
            "TUBÉRCULOS": ["Batata", "Mandioquinha"],
            "PROTEÍNA": ["Carne bovina", "Suína", "Aves", "Peixes", "Ovos"],
            "CEREAIS": ["Arroz", "Pão", "Bolacha"],
            "GRÃOS": ["Feijão"],
            "FRUTAS": ["Banana", "Maçã", "Mamão", "Melancia", "Suco de Frutas"],
        }
    if 'turmas' not in session:
        session['turmas'] = TURMAS_DEFAULT

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

USUARIOS = {
    'admin': {'senha': 'senha', 'role': 'admin'},
    'responsavel1': {'senha': 'alimentacao1', 'role': 'alimentacao'},
    'responsavel2': {'senha': 'alimentacao2', 'role': 'alimentacao'}
}

@main_bp.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin():
    init_session()
    print(f"Usuário na página admin (role na sessão): {session.get('role')}")
    if request.method == 'POST':
        aluno_nome = request.form.get('aluno_nome')
        turma = request.form.get('turma')
        restricoes = request.form.getlist('restricoes')
        print(f"Cadastrando aluno: {aluno_nome}, Turma: {turma}, Restrições: {restricoes}")
        if aluno_nome and turma and aluno_nome not in session['alunos']:
            session['alunos'][aluno_nome] = {'turma': turma, 'restricoes': restricoes}
            session.modified = True
            return redirect(url_for('main.admin'))
    print(f"Renderizando admin.html com alunos: {session['alunos']}, grupos_alimentos: {session['grupos_alimentos']}, turmas: {session['turmas']}")
    return render_template('admin.html', alunos=session['alunos'], grupos_alimentos=session['grupos_alimentos'], turmas=session['turmas'])

@main_bp.route('/add_turma', methods=['POST'])
@login_required
@admin_required
def add_turma():
    init_session()
    nova_turma = request.form.get('nova_turma')
    turmas = session.get('turmas', TURMAS_DEFAULT)
    if nova_turma and nova_turma not in turmas:
        turmas.append(nova_turma)
        session['turmas'] = turmas
        session.modified = True
        print(f"Nova turma adicionada: {nova_turma}")
    else:
        print("Erro ao adicionar turma: Turma já existe ou nome inválido.")
    return redirect(url_for('main.admin'))

@main_bp.route('/delete_turma', methods=['POST'])
@login_required
@admin_required
def delete_turma():
    init_session()
    turma_to_delete = request.form.get('turma_to_delete')
    turmas = session.get('turmas', TURMAS_DEFAULT)

    if not turma_to_delete or turma_to_delete not in turmas:
        print("Erro ao deletar turma: Turma não encontrada.")
        return redirect(url_for('main.admin'))

    for aluno, info in session['alunos'].items():
        if info['turma'] == turma_to_delete:
            print(f"Erro ao deletar turma: Turma {turma_to_delete} está sendo usada pelo aluno {aluno}.")
            return redirect(url_for('main.admin'))

    turmas.remove(turma_to_delete)
    session['turmas'] = turmas
    session.modified = True
    print(f"Turma deletada: {turma_to_delete}")
    return redirect(url_for('main.admin'))

@main_bp.route('/alimentacao', methods=['GET'])
@login_required
def alimentacao():
    init_session()
    print(f"Usuário na página alimentacao (role na sessão): {session.get('role')}")
    aluno_selecionado = request.args.get('aluno_nome')
    turma_selecionada = request.args.get('turma')
    eventos_aluno = []
    eventos_turma = {}

    print(f"aluno_selecionado: {aluno_selecionado}")
    print(f"turma_selecionada: {turma_selecionada}")
    print(f"alunos: {session['alunos']}")
    print(f"calendario_alimentacao: {session['calendario_alimentacao']}")

    if aluno_selecionado:
        for data, eventos in session['calendario_alimentacao'].items():
            for evento in eventos:
                if evento['aluno'] == aluno_selecionado:
                    eventos_aluno.append({'data': data, 'evento': evento})

    if turma_selecionada:
        for data, eventos in session['calendario_alimentacao'].items():
            for evento in eventos:
                aluno = evento['aluno']
                if aluno in session['alunos'] and session['alunos'][aluno]['turma'] == turma_selecionada:
                    if aluno not in eventos_turma:
                        eventos_turma[aluno] = []
                    eventos_turma[aluno].append({'data': data, 'evento': evento})

    print(f"eventos_aluno: {eventos_aluno}")
    print(f"eventos_turma: {eventos_turma}")

    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    return render_template('alimentacao.html', alunos=alunos_ativos, turmas=session['turmas'], aluno_selecionado=aluno_selecionado, turma_selecionada=turma_selecionada, eventos_aluno=eventos_aluno, eventos_turma=eventos_turma)

@main_bp.route('/', methods=['GET', 'POST'])
def login():
    init_session()
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
    init_session()

    calendario_organizado = {}
    for data_str, eventos in session.get("calendario_alimentacao", {}).items():
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        year = data.year
        month = data.month

        if year not in calendario_organizado:
            calendario_organizado[year] = {}
        if month not in calendario_organizado[year]:
            calendario_organizado[year][month] = []

        for evento in eventos:
            evento_dict = {
                'data': data,
                'aluno': evento['aluno'],
                'refeicao': evento['refeicao'],
                'alimentos': evento['alimentos'],
                'observacoes': evento['observacoes']
            }
            calendario_organizado[year][month].append(evento_dict)

    return render_template('calendario.html', calendario=calendario_organizado)

@main_bp.route('/adicionar_evento', methods=['GET', 'POST'])
def adicionar_evento():
    init_session()
    if request.method == 'POST':
        aluno_existente = request.form.get('aluno_existente')
        novo_aluno = request.form.get('novo_aluno')
        data_str = request.form.get('data')
        refeicao = request.form.get('refeicao')
        alimentos = request.form.getlist('alimentos')
        observacoes = request.form.get('observacoes', '').strip()

        aluno_nome = aluno_existente if aluno_existente else novo_aluno

        if aluno_nome:
            try:
                data = datetime.strptime(data_str, '%Y-%m-%d').date()
            except ValueError:
                return render_template('adicionar_evento.html',
                                       alunos=session['alunos'],
                                       grupos_alimentos=session['grupos_alimentos'],
                                       error="Formato de data inválido.")

            if aluno_nome in session['alunos'] and 'data_exclusao' in session['alunos'][aluno_nome]:
                data_exclusao = datetime.strptime(session['alunos'][aluno_nome]['data_exclusao'], '%Y-%m-%d').date()
                if data >= data_exclusao:
                    return render_template('adicionar_evento.html',
                                           alunos=session['alunos'],
                                           grupos_alimentos=session['grupos_alimentos'],
                                           error=f"O aluno {aluno_nome} foi excluído a partir de {data_exclusao.strftime('%Y-%m-%d')}. Não é possível adicionar eventos após essa data.")

            if aluno_existente in session['alunos']:
                restricoes = session['alunos'][aluno_existente].get('restricoes', [])
                alimentos_restritos_consumidos = [alimento for alimento in alimentos if alimento in restricoes]
                if alimentos_restritos_consumidos and not observacoes:
                    return render_template('adicionar_evento.html',
                                           alunos=session['alunos'],
                                           grupos_alimentos=session['grupos_alimentos'],
                                           error=f"O aluno {aluno_nome} consumiu alimentos restritos ({', '.join(alimentos_restritos_consumidos)}). O campo 'Observações' é obrigatório nesse caso.")

            data_str = data.strftime('%Y-%m-%d')
            if data_str not in session['calendario_alimentacao']:
                session['calendario_alimentacao'][data_str] = []

            session['calendario_alimentacao'][data_str].append({
                'aluno': aluno_nome,
                'refeicao': refeicao,
                'alimentos': alimentos,
                'observacoes': observacoes
            })

            if novo_aluno and novo_aluno not in session['alunos']:
                session['alunos'][novo_aluno] = {'turma': session['turmas'][0], 'restricoes': []}

            session.modified = True
            return redirect(url_for('main.calendario'))
        else:
            return render_template('adicionar_evento.html',
                                   alunos=session['alunos'],
                                   grupos_alimentos=session['grupos_alimentos'],
                                   error="Por favor, selecione um aluno existente ou digite o nome de um novo aluno.")
    else:
        alunos_ativos = {
            nome: dados for nome, dados in session['alunos'].items()
            if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
        }
        return render_template('adicionar_evento.html',
                               alunos=alunos_ativos,
                               grupos_alimentos=session['grupos_alimentos'],
                               alunos_restricoes={nome: dados.get('restricoes', []) for nome, dados in session['alunos'].items()})

@main_bp.route('/gerenciar_grupos', methods=['GET', 'POST'])
@login_required
def gerenciar_grupos():
    init_session()
    if session.get('role') != 'admin':
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        acao = request.form.get('acao')

        if acao == 'adicionar_grupo':
            novo_grupo = request.form.get('novo_grupo').upper()
            if novo_grupo and novo_grupo not in session['grupos_alimentos']:
                session['grupos_alimentos'][novo_grupo] = []

        elif acao == 'adicionar_alimento':
            grupo = request.form.get('grupo')
            novo_alimento = request.form.get('novo_alimento')
            if grupo in session['grupos_alimentos'] and novo_alimento and novo_alimento not in session['grupos_alimentos'][grupo]:
                session['grupos_alimentos'][grupo].append(novo_alimento)

        elif acao == 'excluir_grupo':
            grupo = request.form.get('grupo')
            if grupo in session['grupos_alimentos']:
                del session['grupos_alimentos'][grupo]

        elif acao == 'excluir_alimento':
            grupo = request.form.get('grupo')
            alimento = request.form.get('alimento')
            if grupo in session['grupos_alimentos'] and alimento in session['grupos_alimentos'][grupo]:
                session['grupos_alimentos'][grupo].remove(alimento)

        session.modified = True
        return redirect(url_for('main.gerenciar_grupos'))
    return render_template('gerenciar_grupos.html', grupos_alimentos=session['grupos_alimentos'])

@main_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    init_session()

    graf_grupos = graf_alimentos = False
    relatorio_mensal = {}
    porcentagem_grupos = {}
    porcentagem_alimentos_por_grupo = {}
    total_geral = 0

    aluno_selecionado = request.form.get('aluno', request.args.get('aluno', ''))
    if aluno_selecionado in session['alunos']:
        session['last_aluno'] = aluno_selecionado
        session.modified = True

    mes_selecionado = 4  # Abril
    ano_selecionado = 2025

    if request.method == 'POST':
        mes_selecionado = request.form.get('mes', '4').strip()
        ano_selecionado = request.form.get('ano', '2025').strip()
    else:
        mes_selecionado = request.args.get('mes', '4').strip()
        ano_selecionado = request.args.get('ano', '2025').strip()

    try:
        mes_selecionado = int(mes_selecionado) if mes_selecionado else 4
        ano_selecionado = int(ano_selecionado) if ano_selecionado else 2025
    except (ValueError, TypeError) as e:
        print(f"Erro na conversão: {str(e)}")
        mes_selecionado, ano_selecionado = 4, 2025

    print(f"""
    ========== DASHBOARD DEBUG ==========
    Aluno: {aluno_selecionado}
        → Válido: {aluno_selecionado in session['alunos']}
    Mês: {mes_selecionado}
        → Válido: {1 <= mes_selecionado <= 12}
    Ano: {ano_selecionado}
        → Válido: {2020 <= ano_selecionado <= 2030}
    ======================================
    """)

    if not session.get('calendario_alimentacao'):
        session['calendario_alimentacao'] = {}
        session['calendario_alimentacao']['2025-04-01'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Bolacha', 'Vitamina'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Banana', 'Ovos'], 'observacoes': ''},
        ]
        session['calendario_alimentacao']['2025-04-02'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Bolacha', 'Vitamina'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Banana', 'Maçã'], 'observacoes': ''},
        ]
        session['calendario_alimentacao']['2025-04-03'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Pão', 'Achocolatado'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Suco de Frutas', 'Feijão'], 'observacoes': ''},
        ]
        session['calendario_alimentacao']['2025-04-04'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Arroz', 'Tomate'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Melancia', 'Carne bovina'], 'observacoes': ''},
        ]
        session['calendario_alimentacao']['2025-04-05'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Bolacha', 'Alface'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Suco de Frutas', 'Mamão'], 'observacoes': ''},
        ]
        session.modified = True

    try:
        calendario = session.get('calendario_alimentacao', {})

        for data_str, eventos in calendario.items():
            data = datetime.strptime(data_str, "%Y-%m-%d").date()

            if data.month == mes_selecionado and data.year == ano_selecionado:
                for evento in eventos:
                    if evento.get('aluno') == aluno_selecionado:
                        if aluno_selecionado in session['alunos'] and 'data_exclusao' in session['alunos'][aluno_selecionado]:
                            data_exclusao = datetime.strptime(session['alunos'][aluno_selecionado]['data_exclusao'], '%Y-%m-%d').date()
                            if data >= data_exclusao:
                                continue
                        for alimento in evento.get('alimentos', []):
                            relatorio_mensal[alimento] = relatorio_mensal.get(alimento, 0) + 1

        if relatorio_mensal:
            total_geral = sum(relatorio_mensal.values())

            consumo_por_grupo = {}
            for grupo, alimentos in session['grupos_alimentos'].items():
                total_grupo = sum(relatorio_mensal.get(a, 0) for a in alimentos)
                if total_grupo > 0:
                    consumo_por_grupo[grupo] = total_grupo
                    porcentagem_grupos[grupo] = (total_grupo / total_geral) * 100
                    porcentagem_alimentos_por_grupo[grupo] = {
                        a: (relatorio_mensal[a] / total_grupo * 100)
                        for a in alimentos if a in relatorio_mensal
                    }

            try:
                grupos_ordenados = sorted(consumo_por_grupo.items(), key=lambda x: x[1], reverse=True)[:5]
                if grupos_ordenados:
                    plt.figure(figsize=(10, 6))
                    sns.set_theme(style="whitegrid")
                    ax = sns.barplot(
                        x=[v for k, v in grupos_ordenados],
                        y=[k for k, v in grupos_ordenados],
                        palette="Blues_d"
                    )
                    plt.title("Top 5 Grupos de Alimentos Mais Consumidos", fontsize=16, pad=20)
                    plt.xlabel("Quantidade Consumida", fontsize=14)
                    plt.ylabel("Grupo de Alimento", fontsize=14)
                    plt.xticks(fontsize=12)
                    plt.yticks(fontsize=12)

                    for p in ax.patches:
                        width = p.get_width()
                        ax.text(
                            width + 0.1,
                            p.get_y() + p.get_height()/2.,
                            f'{width} ({(width / total_geral):.1%})',
                            ha='left',
                            va='center',
                            fontsize=12
                        )

                    grupos_chart_path = os.path.join(TEMP_DIR, "grupos_mais_consumidos.png")
                    plt.savefig(grupos_chart_path, bbox_inches='tight', dpi=150)
                    plt.close()
                    graf_grupos = True
                    print(f"Gráfico de grupos gerado com sucesso: {grupos_chart_path}")
                else:
                    print("Nenhum dado disponível para o gráfico de grupos.")
            except Exception as e:
                print(f"Erro ao gerar o gráfico de grupos: {str(e)}")
                graf_grupos = False

            try:
                alimentos_ordenados = sorted(relatorio_mensal.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"Alimentos ordenados para o gráfico: {alimentos_ordenados}")
                if alimentos_ordenados:
                    plt.figure(figsize=(10, 6))
                    sns.set_theme(style="whitegrid")
                    ax = sns.barplot(
                        x=[v for k, v in alimentos_ordenados],
                        y=[k for k, v in alimentos_ordenados],
                        palette="Greens_d"
                    )
                    plt.title("Top 5 Alimentos Mais Consumidos", fontsize=16, pad=20)
                    plt.xlabel("Quantidade Consumida", fontsize=14)
                    plt.ylabel("Alimento", fontsize=14)
                    plt.xticks(fontsize=12)
                    plt.yticks(fontsize=12)

                    for p in ax.patches:
                        width = p.get_width()
                        ax.text(
                            width + 0.1,
                            p.get_y() + p.get_height()/2.,
                            f'{width} ({(width / total_geral):.1%})',
                            ha='left',
                            va='center',
                            fontsize=12
                        )

                    alimentos_chart_path = os.path.join(TEMP_DIR, "alimentos_mais_consumidos.png")
                    plt.savefig(alimentos_chart_path, bbox_inches='tight', dpi=150)
                    plt.close()
                    graf_alimentos = True
                    print(f"Gráfico de alimentos gerado com sucesso: {alimentos_chart_path}")
                else:
                    print("Nenhum dado disponível para o gráfico de alimentos.")
            except Exception as e:
                print(f"Erro ao gerar o gráfico de alimentos: {str(e)}")
                graf_alimentos = False

    except Exception as e:
        print(f"Erro crítico no processamento: {str(e)}")

    if aluno_selecionado in session['alunos']:
        session['last_aluno'] = aluno_selecionado
        session.modified = True

    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    user_role = session.get('role', '')
    restricoes_aluno = session['alunos'].get(aluno_selecionado, {}).get('restricoes', []) if aluno_selecionado in session['alunos'] else []

    return render_template(
        'dashboard.html',
        alunos=alunos_ativos,
        aluno_selecionado=aluno_selecionado,
        mes_selecionado=mes_selecionado,
        ano_selecionado=ano_selecionado,
        relatorio_mensal=relatorio_mensal,
        grupos_alimentos=session['grupos_alimentos'],
        meses=range(1, 13),
        anos=range(2020, 2030),
        grupos_mais_consumidos_exists=graf_grupos,
        alimentos_mais_consumidos_exists=graf_alimentos,
        porcentagem_grupos=porcentagem_grupos,
        porcentagem_alimentos_por_grupo=porcentagem_alimentos_por_grupo,
        total_geral=total_geral,
        user_role=user_role,
        restricoes_aluno=restricoes_aluno
    )

@main_bp.route('/temp/<filename>')
def serve_temp_file(filename):
    file_path = os.path.join(TEMP_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/png')
    else:
        abort(404)

@main_bp.route('/consulta_diaria', methods=['GET'])
@login_required
def consulta_diaria():
    init_session()
    mes_selecionado = request.args.get('mes')
    ano_selecionado = request.args.get('ano')
    data_selecionada = request.args.get('data')

    # Validação e definição do período
    try:
        mes_selecionado = int(mes_selecionado) if mes_selecionado else datetime.now().month
        ano_selecionado = int(ano_selecionado) if ano_selecionado else datetime.now().year
    except (ValueError, TypeError) as e:
        print(f"Erro na conversão de mês/ano: {str(e)}")
        mes_selecionado, ano_selecionado = datetime.now().month, datetime.now().year

    # Define o intervalo do mês
    primeiro_dia = datetime(ano_selecionado, mes_selecionado, 1).date()
    ultimo_dia = datetime(ano_selecionado, mes_selecionado, monthrange(ano_selecionado, mes_selecionado)[1]).date()

    # Organiza todos os eventos por aluno e data
    eventos_por_aluno = {}
    calendario_alimentacao = session.get("calendario_alimentacao", {})
    for data_str, eventos in calendario_alimentacao.items():
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        if primeiro_dia <= data <= ultimo_dia:
            for evento in eventos:
                aluno = evento['aluno']
                if aluno not in eventos_por_aluno:
                    eventos_por_aluno[aluno] = []
                # Verifica se o aluno está excluído na data do evento
                if aluno in session['alunos'] and 'data_exclusao' in session['alunos'][aluno]:
                    data_exclusao = datetime.strptime(session['alunos'][aluno]['data_exclusao'], '%Y-%m-%d').date()
                    if data >= data_exclusao:
                        continue
                eventos_por_aluno[aluno].append({
                    'data': data,
                    'evento': evento
                })

    # Ordena os eventos de cada aluno por data (do mais recente ao mais antigo)
    for aluno in eventos_por_aluno:
        eventos_por_aluno[aluno].sort(key=lambda x: x['data'], reverse=True)

    # Se uma data específica foi selecionada, filtra os eventos dessa data
    consulta_diaria = {}
    if data_selecionada:
        try:
            data = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
            for aluno, eventos in eventos_por_aluno.items():
                eventos_na_data = [e for e in eventos if e['data'] == data]
                if eventos_na_data:
                    consulta_diaria[aluno] = eventos_na_data
        except ValueError as e:
            print(f"Erro ao converter data {data_selecionada}: {e}")

    # Se nenhuma data foi selecionada, mostra o último evento de cada aluno
    else:
        for aluno, eventos in eventos_por_aluno.items():
            if eventos:
                ultima_data = eventos[0]['data']
                consulta_diaria[aluno] = [e for e in eventos if e['data'] == ultima_data]

    # Gera listas de datas disponíveis para navegação por aluno
    datas_por_aluno = {}
    for aluno, eventos in eventos_por_aluno.items():
        datas_por_aluno[aluno] = sorted({e['data'].strftime('%Y-%m-%d') for e in eventos}, reverse=True)

    # Obtém as restrições de cada aluno
    restricoes_por_aluno = {nome: session['alunos'][nome].get('restricoes', []) for nome in session['alunos'].keys()}

    print(f"Consulta Diária - Mês: {mes_selecionado}, Ano: {ano_selecionado}, Data Selecionada: {data_selecionada}, Resultado: {consulta_diaria}")

    # Dados para os gráficos (mantendo a lógica original)
    mais_consumidos = {}
    menos_consumidos = {}
    relatorio_mensal = {}
    for aluno, eventos in eventos_por_aluno.items():
        for evento_dict in eventos:
            for alimento in evento_dict['evento']['alimentos']:
                relatorio_mensal[alimento] = relatorio_mensal.get(alimento, 0) + 1

    if relatorio_mensal:
        ordenado = sorted(relatorio_mensal.items(), key=lambda x: x[1], reverse=True)
        mais_consumidos = dict(ordenado[:5])
        menos_consumidos = dict(ordenado[-5:])

        plt.figure(figsize=(8, 6))
        sns.barplot(x=list(mais_consumidos.values()), y=list(mais_consumidos.keys()), hue=list(mais_consumidos.keys()), palette="Blues_d", legend=False)
        plt.title("Alimentos Mais Consumidos", fontsize=14, pad=20)
        plt.xlabel("Quantidade", fontsize=12)
        plt.ylabel("Alimentos", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(TEMP_DIR, "mais_consumidos.png"))
        plt.close()

        plt.figure(figsize=(8, 6))
        sns.barplot(x=list(menos_consumidos.values()), y=list(menos_consumidos.keys()), hue=list(menos_consumidos.keys()), palette="Reds_d", legend=False)
        plt.title("Alimentos Menos Consumidos", fontsize=14, pad=20)
        plt.xlabel("Quantidade", fontsize=12)
        plt.ylabel("Alimentos", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(TEMP_DIR, "menos_consumidos.png"))
        plt.close()

    mais_consumidos_exists = os.path.exists(os.path.join(TEMP_DIR, "mais_consumidos.png"))
    menos_consumidos_exists = os.path.exists(os.path.join(TEMP_DIR, "menos_consumidos.png"))

    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    user_role = session.get('role', '')

    return render_template(
        'dashboard.html',
        consulta_diaria=consulta_diaria,
        consulta_data=data_selecionada,
        mes_selecionado=mes_selecionado,
        ano_selecionado=ano_selecionado,
        datas_por_aluno=datas_por_aluno,
        alunos=alunos_ativos,
        aluno_selecionado=None,  # Não usamos mais aluno_selecionado aqui
        mais_consumidos=mais_consumidos,
        menos_consumidos=menos_consumidos,
        relatorio_mensal=relatorio_mensal,
        grupos_alimentos=session.get('grupos_alimentos', {}),
        meses=range(1, 13),
        anos=range(2020, 2030),
        mais_consumidos_exists=mais_consumidos_exists,
        menos_consumidos_exists=menos_consumidos_exists,
        user_role=user_role,
        restricoes_por_aluno=restricoes_por_aluno
    )

@main_bp.route('/deletar_aluno', methods=['GET', 'POST'])
@login_required
def deletar_aluno():
    init_session()
    if session.get('role') != 'admin':
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        aluno_nome = request.form.get('aluno')
        mes_exclusao = request.form.get('mes_exclusao')
        ano_exclusao = request.form.get('ano_exclusao')

        if aluno_nome and mes_exclusao and ano_exclusao and aluno_nome in session['alunos']:
            try:
                data_exclusao = f"{ano_exclusao}-{mes_exclusao.zfill(2)}-01"
                session['alunos'][aluno_nome]['data_exclusao'] = data_exclusao
                session.modified = True
                print(f"Aluno {aluno_nome} marcado como excluído a partir de {data_exclusao}")
                return redirect(url_for('main.admin'))
            except Exception as e:
                print(f"Erro ao marcar aluno como excluído: {str(e)}")
                return "Erro ao processar a exclusão do aluno."

    return render_template('deletar_aluno.html', alunos=session['alunos'])

@main_bp.route('/selecionar_periodo_pdf', methods=['GET', 'POST'])
@login_required
def selecionar_periodo_pdf():
    init_session()
    aluno_pdf = request.args.get('aluno_pdf')
    if not aluno_pdf or aluno_pdf not in session['alunos']:
        flash('Aluno inválido para gerar o relatório.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        mes_inicio_str = request.form.get('mes_inicio')
        ano_inicio_str = request.form.get('ano_inicio')
        mes_fim_str = request.form.get('mes_fim')
        ano_fim_str = request.form.get('ano_fim')

        try:
            data_inicio = datetime(int(ano_inicio_str), int(mes_inicio_str), 1).date()
            _, ultimo_dia = monthrange(int(ano_fim_str), int(mes_fim_str))
            data_fim = datetime(int(ano_fim_str), int(mes_fim_str), ultimo_dia).date()

            return redirect(url_for('main.gerar_pdf', aluno=aluno_pdf, data_inicio=data_inicio.strftime('%Y-%m-%d'), data_fim=data_fim.strftime('%Y-%m-%d')))
        except ValueError:
            flash('Datas de período inválidas.', 'error')
            return render_template('selecionar_periodo_pdf.html', aluno=aluno_pdf, meses=range(1, 13), anos=range(2020, 2030))

    return render_template('selecionar_periodo_pdf.html', aluno=aluno_pdf, meses=range(1, 13), anos=range(2020, 2030))

@main_bp.route('/gerar_pdf', methods=['GET', 'POST'])
@login_required
def gerar_pdf():
    init_session()
    if request.method == 'POST':
        aluno_nome = request.form.get('aluno_nome_pdf')
        periodo = request.form.get('periodo')
        data_inicio_str = request.form.get('data_inicial')
        data_fim_str = request.form.get('data_final')

        print(f"Aluno Nome: {aluno_nome}")
        print(f"Período: {periodo}")
        print(f"Data Inicial: {data_inicio_str}")
        print(f"Data Final: {data_fim_str}")
        print(f"Alunos na Sessão: {session.get('alunos')}")

        if not aluno_nome or aluno_nome not in session['alunos']:
            flash('Parâmetros inválidos para gerar o relatório.', 'error')
            return redirect(url_for('main.dashboard'))

        today = datetime.now().date()
        if periodo == 'diario':
            data_inicio = today
            data_fim = today
        elif periodo == 'semanal':
            data_inicio = today - timedelta(days=today.weekday())
            data_fim = data_inicio + timedelta(days=6)
        elif periodo == 'mensal':
            data_inicio = today.replace(day=1)
            data_fim = data_inicio.replace(day=monthrange(today.year, today.month)[1])
        elif periodo == 'intervalo' and data_inicio_str and data_fim_str:
            try:
                data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
                data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Formato de data inválido.', 'error')
                return redirect(url_for('main.dashboard'))
        else:
            flash('Período ou datas inválidas.', 'error')
            return redirect(url_for('main.dashboard'))

        print(f"Data Início (obj): {data_inicio}")
        print(f"Data Fim (obj): {data_fim}")

        print("Iniciando a geração do PDF...")
        nome_arquivo_pdf = os.path.join(PDF_DIR, f"relatorio_{aluno_nome.replace(' ', '_')}_{data_inicio.strftime('%Y-%m-%d')}_{data_fim.strftime('%Y-%m-%d')}.pdf")
        doc = SimpleDocTemplate(nome_arquivo_pdf, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"Relatório de Alimentação de {aluno_nome}", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}", styles['Heading3']))
        story.append(Spacer(1, 0.2*inch))

        relatorio_alimentos = {}
        restricoes = session['alunos'].get(aluno_nome, {}).get('restricoes', [])
        avancos_restricoes = 0
        for data_str, eventos in session.get('calendario_alimentacao', {}).items():
            data_evento = datetime.strptime(data_str, '%Y-%m-%d').date()
            if data_inicio <= data_evento <= data_fim:
                for evento in eventos:
                    if evento['aluno'] == aluno_nome:
                        for alimento in evento.get('alimentos', []):
                            relatorio_alimentos[alimento] = relatorio_alimentos.get(alimento, 0) + 1
                            if alimento in restricoes and 'observacoes' in evento and evento['observacoes']:
                                avancos_restricoes += 1

        consumo_por_grupo = {}
        for grupo, alimentos in session['grupos_alimentos'].items():
            total_grupo = sum(relatorio_alimentos.get(a, 0) for a in alimentos if a in relatorio_alimentos)
            if total_grupo > 0:
                consumo_por_grupo[grupo] = total_grupo

        grupos_ordenados = sorted(consumo_por_grupo.items(), key=lambda x: x[1], reverse=True)[:3]
        story.append(Paragraph("Grupos de Alimentos Mais Consumidos:", styles['Heading2']))
        for grupo, qtd in grupos_ordenados:
            story.append(Paragraph(f"- {grupo}: {qtd} vezes", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        alimentos_ordenados = sorted(relatorio_alimentos.items(), key=lambda x: x[1], reverse=True)[:5]
        story.append(Paragraph("Alimentos Mais Consumidos:", styles['Heading2']))
        for alimento, qtd in alimentos_ordenados:
            story.append(Paragraph(f"- {alimento}: {qtd} vezes", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        story.append(Paragraph("Avanço na Alimentação:", styles['Heading2']))
        if restricoes:
            story.append(Paragraph(f"O aluno tem as seguintes restrições: {', '.join(restricoes)}", styles['Normal']))
            if avancos_restricoes > 0:
                story.append(Paragraph(f"Houve {avancos_restricoes} ocasiões em que o aluno consumiu alimentos de sua restrição com observações registradas, indicando progresso.", styles['Normal']))
            else:
                story.append(Paragraph("Não houve registro de consumo de alimentos restritos com observações neste período.", styles['Normal']))
        else:
            story.append(Paragraph("O aluno não possui restrições registradas.", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))

        if restricoes and relatorio_alimentos:
            plt.figure(figsize=(4, 3))
            restricoes_consumidas = sum(1 for a in relatorio_alimentos if a in restricoes)
            plt.bar(['Alimentos Restritivos', 'Outros Alimentos'], [restricoes_consumidas, len(relatorio_alimentos) - restricoes_consumidas], color=['#FF9999', '#66B2FF'])
            plt.title('Distribuição de Consumo')
            plt.ylabel('Quantidade')
            plt.savefig(os.path.join(TEMP_DIR, 'avanco_alimentacao.png'), bbox_inches='tight', dpi=100)
            plt.close()

            story.append(Paragraph("Gráfico de Avanço na Alimentação:", styles['Heading2']))
            story.append(Image(os.path.join(TEMP_DIR, 'avanco_alimentacao.png'), width=200, height=150))
        else:
            story.append(Paragraph("Não foi possível gerar um gráfico devido à ausência de restrições ou dados insuficientes.", styles['Normal']))

        if not story[-1].__class__.__name__ == 'Spacer':
            story.append(Paragraph("Fim do Relatório", styles['Normal']))

        doc.build(story)

        print(f"PDF gerado com sucesso e salvo em: {nome_arquivo_pdf}")
        return send_file(nome_arquivo_pdf, as_attachment=True, download_name=f"relatorio_{aluno_nome.replace(' ', '_')}_{data_inicio.strftime('%Y-%m-%d')}_{data_fim.strftime('%Y-%m-%d')}.pdf")
    else:
        return redirect(url_for('main.dashboard'))

@main_bp.route('/excluir_evento', methods=['POST'])
@login_required
def excluir_evento():
    init_session()
    data_excluir = request.form.get('data')
    aluno_excluir = request.form.get('aluno')
    refeicao_excluir = request.form.get('refeicao')
    alimentos_excluir = request.form.get('alimentos')

    if data_excluir and aluno_excluir and refeicao_excluir and alimentos_excluir:
        try:
            data_obj = datetime.strptime(data_excluir, '%Y-%m-%d').date()
            data_str_fmt = data_obj.strftime('%Y-%m-%d')
            if data_str_fmt in session['calendario_alimentacao']:
                eventos = session['calendario_alimentacao'][data_str_fmt]
                alimentos_list = [a.strip() for a in alimentos_excluir.split(',')]
                session['calendario_alimentacao'][data_str_fmt] = [
                    evento for evento in eventos
                    if not (evento['aluno'] == aluno_excluir and
                            evento['refeicao'] == refeicao_excluir and
                            set(evento['alimentos']) == set(alimentos_list))
                ]
                session.modified = True
                flash('Evento excluído com sucesso.', 'success')
            else:
                flash('Data do evento não encontrada.', 'error')
        except ValueError:
            flash('Formato de data inválido.', 'error')
    else:
        flash('Parâmetros de exclusão inválidos.', 'error')

    return redirect(url_for('main.calendario'))

