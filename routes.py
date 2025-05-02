from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from datetime import datetime, timedelta
from functools import wraps
from calendar import monthrange
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Define o backend para geração de gráficos sem interface gráfica
import matplotlib.pyplot as plt
import seaborn as sns  # Biblioteca para gráficos mais bonitos

# ================== CONFIGURAÇÃO INICIAL ==================
# Define caminhos críticos antes de qualquer outra coisa
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(r"C:\Users\gigie\Documents\001 PI 01 2025\sua_aplicacao_demo_msdos", "static")

# Garante que a pasta static existe
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

main_bp = Blueprint('main', __name__)

# Lista de turmas predefinidas
TURMAS = ["Turma A", "Turma B", "Turma C"]

# Inicializar variáveis na sessão se não existirem
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
            "FRUTAS": ["Banana", "Maçã", "Mamão", "Melancia"],
            "SUCO DE FRUTAS": ["Sucos diversos"],
        }

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session:
            return redirect(url_for('main.login'))
        return f(*args, **kwargs)
    return decorated_function

USUARIOS = {
    'admin': {'senha': 'senha', 'role': 'admin'},
    'responsavel1': {'senha': 'alimentacao1', 'role': 'alimentacao'},
    'responsavel2': {'senha': 'alimentacao2', 'role': 'alimentacao'}
}

@main_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    init_session()
    print(f"Usuário na página admin (role na sessão): {session.get('role')}")
    if session.get('role') != 'admin':
        abort(403)  # Erro 403: Forbidden
    if request.method == 'POST':
        aluno_nome = request.form.get('aluno_nome')
        turma = request.form.get('turma')
        restricoes = request.form.getlist('restricoes')
        print(f"Cadastrando aluno: {aluno_nome}, Turma: {turma}, Restrições: {restricoes}")
        if aluno_nome and turma and aluno_nome not in session['alunos']:
            session['alunos'][aluno_nome] = {'turma': turma, 'restricoes': restricoes}
            session.modified = True
            return redirect(url_for('main.admin'))
    print(f"Renderizando admin.html com alunos: {session['alunos']}, grupos_alimentos: {session['grupos_alimentos']}, turmas: {TURMAS}")
    return render_template('admin.html', alunos=session['alunos'], grupos_alimentos=session['grupos_alimentos'], turmas=TURMAS)

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

    # Filtra alunos para exibir apenas os que não estão excluídos no momento atual
    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    return render_template('alimentacao.html', alunos=alunos_ativos, turmas=TURMAS, aluno_selecionado=aluno_selecionado, turma_selecionada=turma_selecionada, eventos_aluno=eventos_aluno, eventos_turma=eventos_turma)

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

    # Converter as chaves da sessão de string para datetime antes de enviar ao template
    calendario_data = {
        datetime.strptime(data_str, "%Y-%m-%d").date(): eventos
        for data_str, eventos in session.get("calendario_alimentacao", {}).items()
    }

    return render_template('calendario.html', calendario=calendario_data)

@main_bp.route('/adicionar_evento', methods=['GET', 'POST'])
def adicionar_evento():
    init_session()
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

            # Verifica se o aluno está excluído a partir de uma data
            if aluno_nome in session['alunos'] and 'data_exclusao' in session['alunos'][aluno_nome]:
                data_exclusao = datetime.strptime(session['alunos'][aluno_nome]['data_exclusao'], '%Y-%m-%d').date()
                if data >= data_exclusao:
                    return f"O aluno {aluno_nome} foi excluído a partir de {data_exclusao.strftime('%Y-%m-%d')}. Não é possível adicionar eventos após essa data."

            data_str = data.strftime('%Y-%m-%d')  # Convertendo data para string

            if data_str not in session['calendario_alimentacao']:
                session['calendario_alimentacao'][data_str] = []

            session['calendario_alimentacao'][data_str].append({
                'aluno': aluno_nome,
                'refeicao': refeicao,
                'alimentos': alimentos,
                'observacoes': observacoes
            })

            if novo_aluno and novo_aluno not in session['alunos']:
                session['alunos'][novo_aluno] = {'turma': 'Turma A', 'restricoes': []}

            session.modified = True
            return redirect(url_for('main.calendario'))
        else:
            return "Por favor, selecione um aluno existente ou digite o nome de um novo aluno."
    else:
        # Filtra alunos para exibir apenas os que não estão excluídos no momento atual
        alunos_ativos = {
            nome: dados for nome, dados in session['alunos'].items()
            if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
        }
        return render_template('adicionar_evento.html', alunos=alunos_ativos, grupos_alimentos=session['grupos_alimentos'])

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
    
    # Inicialização segura de todas as variáveis
    graf_grupos = graf_alimentos = False
    relatorio_mensal = {}
    porcentagem_grupos = {}
    porcentagem_alimentos_por_grupo = {}
    total_geral = 0

    # Captura e tratamento de parâmetros
    aluno_selecionado = request.args.get('aluno', session.get('last_aluno', ''))
    
    # Lógica de datas padrão para teste
    mes_selecionado = 4  # Abril
    ano_selecionado = 2025

    # Sobrescreve com valores do formulário se existirem
    if request.method == 'POST':
        mes_selecionado = request.form.get('mes', '4').strip()
        ano_selecionado = request.form.get('ano', '2025').strip()
    else:
        mes_selecionado = request.args.get('mes', '4').strip()
        ano_selecionado = request.args.get('ano', '2025').strip()

    # Conversão segura para inteiros
    try:
        mes_selecionado = int(mes_selecionado) if mes_selecionado else 4
        ano_selecionado = int(ano_selecionado) if ano_selecionado else 2025
    except (ValueError, TypeError) as e:
        print(f"Erro na conversão: {str(e)}")
        mes_selecionado, ano_selecionado = 4, 2025  # Fallback para dados de teste

    # Debug controlado
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

    # Simulate the data to match the screenshot
    if not session.get('calendario_alimentacao'):
        session['calendario_alimentacao'] = {}
        # Simulate data for April 2025
        session['calendario_alimentacao']['2025-04-01'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Bolacha', 'Vitamina'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Banana', 'Ovos'], 'observacoes': ''},
        ]
        session['calendario_alimentacao']['2025-04-02'] = [
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Café da Manhã', 'alimentos': ['Bolacha', 'Vitamina'], 'observacoes': ''},
            {'aluno': aluno_selecionado or 'Aluno Teste', 'refeicao': 'Almoço', 'alimentos': ['Banana', 'Maçã'], 'observacoes': ''},
        ]
        session.modified = True

    # Processamento principal
    try:
        calendario = session.get('calendario_alimentacao', {})
        
        for data_str, eventos in calendario.items():
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
            
            if data.month == mes_selecionado and data.year == ano_selecionado:
                for evento in eventos:
                    if evento.get('aluno') == aluno_selecionado:
                        # Verifica se o aluno está excluído a partir de uma data
                        if aluno_selecionado in session['alunos'] and 'data_exclusao' in session['alunos'][aluno_selecionado]:
                            data_exclusao = datetime.strptime(session['alunos'][aluno_selecionado]['data_exclusao'], '%Y-%m-%d').date()
                            if data >= data_exclusao:
                                continue
                        for alimento in evento.get('alimentos', []):
                            relatorio_mensal[alimento] = relatorio_mensal.get(alimento, 0) + 1

        # Cálculos estatísticos
        if relatorio_mensal:  
            total_geral = sum(relatorio_mensal.values())  
            
            # Porcentagem por grupo
            consumo_por_grupo = {}
            for grupo, alimentos in session['grupos_alimentos'].items():
                total_grupo = sum(relatorio_mensal.get(a, 0) for a in alimentos)
                if total_grupo > 0:
                    consumo_por_grupo[grupo] = total_grupo
                    porcentagem_grupos[grupo] = (total_grupo / total_geral) * 100
                    
                    # Porcentagem por alimento dentro do grupo
                    porcentagem_alimentos_por_grupo[grupo] = {
                        a: (relatorio_mensal[a] / total_grupo * 100) 
                        for a in alimentos if a in relatorio_mensal
                    }

            # Geração de gráficos
            try:
                # Gráfico 1: Grupos de Alimentos Mais Consumidos
                grupos_ordenados = sorted(consumo_por_grupo.items(), key=lambda x: x[1], reverse=True)[:5]
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
                
                # Adiciona porcentagens
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
                
                plt.savefig(os.path.join(STATIC_DIR, "grupos_mais_consumidos.png"), bbox_inches='tight', dpi=150)
                plt.close()
                graf_grupos = True

                # Gráfico 2: Alimentos Mais Consumidos
                alimentos_ordenados = sorted(relatorio_mensal.items(), key=lambda x: x[1], reverse=True)[:5]
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
                
                # Adiciona porcentagens
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
                
                plt.savefig(os.path.join(STATIC_DIR, "alimentos_mais_consumidos.png"), bbox_inches='tight', dpi=150)
                plt.close()
                graf_alimentos = True

            except Exception as e:
                print(f"Erro nos gráficos: {str(e)}")
                graf_grupos = graf_alimentos = False

    except Exception as e:
        print(f"Erro crítico no processamento: {str(e)}")

    # Atualiza última seleção válida
    if aluno_selecionado in session['alunos']:
        session['last_aluno'] = aluno_selecionado
        session.modified = True

    # Filtra alunos para exibir apenas os que não estão excluídos no momento atual
    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    # Obtém a role do usuário da sessão
    user_role = session.get('role', '')

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
        user_role=user_role  # Passa a role do usuário para o template
    )

@main_bp.route('/consulta_diaria', methods=['GET'])
@login_required
def consulta_diaria():
    init_session()
    data_selecionada = request.args.get('data')
    aluno_selecionado = request.args.get('aluno', session.get('last_aluno', ''))

    consulta_diaria = []
    if data_selecionada:
        try:
            data = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
            calendario_alimentacao = {
                datetime.strptime(data_str, "%Y-%m-%d").date() if isinstance(data_str, str) else data_str: eventos
                for data_str, eventos in session.get("calendario_alimentacao", {}).items()
            }
            if data in calendario_alimentacao:
                consulta_diaria = [evento for evento in calendario_alimentacao[data] if not aluno_selecionado or evento['aluno'] == aluno_selecionado]
            else:
                print(f"Data {data} não encontrada em calendario_alimentacao")
        except ValueError as e:
            print(f"Erro ao converter data {data_selecionada}: {e}")

    print(f"Consulta Diária - Data: {data_selecionada}, Aluno: {aluno_selecionado}, Resultado: {consulta_diaria}")

    # Reutilizar a lógica do dashboard para manter consistência
    mais_consumidos = {}
    menos_consumidos = {}
    relatorio_mensal = {}
    if aluno_selecionado and aluno_selecionado in session['alunos']:
        for data, eventos in calendario_alimentacao.items():
            for evento in eventos:
                if evento['aluno'] == aluno_selecionado:
                    # Verifica se o aluno está excluído a partir de uma data
                    if 'data_exclusao' in session['alunos'][aluno_selecionado]:
                        data_exclusao = datetime.strptime(session['alunos'][aluno_selecionado]['data_exclusao'], '%Y-%m-%d').date()
                        if data >= data_exclusao:
                            continue
                    for alimento in evento['alimentos']:
                        relatorio_mensal[alimento] = relatorio_mensal.get(alimento, 0) + 1

    if relatorio_mensal:
        ordenado = sorted(relatorio_mensal.items(), key=lambda x: x[1], reverse=True)
        mais_consumidos = dict(ordenado[:5])
        menos_consumidos = dict(ordenado[-5:])

        # Gerando gráficos
        plt.figure(figsize=(8, 6))
        sns.barplot(x=list(mais_consumidos.values()), y=list(mais_consumidos.keys()), hue=list(mais_consumidos.keys()), palette="Blues_d", legend=False)
        plt.title("Alimentos Mais Consumidos", fontsize=14, pad=20)
        plt.xlabel("Quantidade", fontsize=12)
        plt.ylabel("Alimentos", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(STATIC_DIR, "mais_consumidos.png"))
        plt.close()

        plt.figure(figsize=(8, 6))
        sns.barplot(x=list(menos_consumidos.values()), y=list(menos_consumidos.keys()), hue=list(menos_consumidos.keys()), palette="Reds_d", legend=False)
        plt.title("Alimentos Menos Consumidos", fontsize=14, pad=20)
        plt.xlabel("Quantidade", fontsize=12)
        plt.ylabel("Alimentos", fontsize=12)
        plt.tight_layout()
        plt.savefig(os.path.join(STATIC_DIR, "menos_consumidos.png"))
        plt.close()

    mais_consumidos_exists = os.path.exists(os.path.join(STATIC_DIR, "mais_consumidos.png"))
    menos_consumidos_exists = os.path.exists(os.path.join(STATIC_DIR, "menos_consumidos.png"))

    # Filtra alunos para exibir apenas os que não estão excluídos no momento atual
    alunos_ativos = {
        nome: dados for nome, dados in session['alunos'].items()
        if 'data_exclusao' not in dados or datetime.now() < datetime.strptime(dados['data_exclusao'], '%Y-%m-%d')
    }

    # Obtém a role do usuário da sessão
    user_role = session.get('role', '')

    return render_template(
        'dashboard.html',
        consulta_diaria=consulta_diaria,
        consulta_data=data_selecionada,
        alunos=alunos_ativos,
        aluno_selecionado=aluno_selecionado,
        mais_consumidos=mais_consumidos,
        menos_consumidos=menos_consumidos,
        relatorio_mensal=relatorio_mensal,
        grupos_alimentos=session.get('grupos_alimentos', {}),
        meses=range(1, 13),
        anos=range(2020, 2030),
        mais_consumidos_exists=mais_consumidos_exists,
        menos_consumidos_exists=menos_consumidos_exists,
        user_role=user_role  # Passa a role do usuário para o template
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
                # Define a data de exclusão como o primeiro dia do mês selecionado
                data_exclusao = f"{ano_exclusao}-{mes_exclusao.zfill(2)}-01"
                session['alunos'][aluno_nome]['data_exclusao'] = data_exclusao
                session.modified = True
                print(f"Aluno {aluno_nome} marcado como excluído a partir de {data_exclusao}")
                return redirect(url_for('main.admin'))
            except Exception as e:
                print(f"Erro ao marcar aluno como excluído: {str(e)}")
                return "Erro ao processar a exclusão do aluno."
    
    return render_template('deletar_aluno.html', alunos=session['alunos'])