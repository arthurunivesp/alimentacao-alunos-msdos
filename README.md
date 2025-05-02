# aplicação alimentação msdos
Projeto integrador em computação 1 da Univesp. Criar cadastro de alunos com restrições alimentares no colegio. Criar dois tipos de usuarios, o admin para cadastrar dados e o observador para acompanhar o desenvolvimento do aluno.
# Sistema de Gestão de Alimentação Escolar 🍎📚

[![Flask](https://img.shields.io/badge/Flask-2.0%2B-blue)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green)](https://www.python.org/)

Sistema para gestão de cardápios e restrições alimentares em instituições de ensino.

## 📋 Funcionalidades Principais
- **Autenticação de Usuários** com dois perfis:
  - 👨💼 Administrador (gerencia alunos e restrições)
  - 👩🍳 Nutrição (registra refeições e cardápios)
- **Cadastro de Alunos** com restrições alimentares
- **Agendamento de Refeições** por data e aluno
- **Grupos Alimentares** pré-definidos para padronização
- **Calendário Visual** de acompanhamento nutricional

## 🥦 Grupos Alimentares (Definidos em `routes.py`)
| Grupo           | Alimentos Incluídos                                   |
|-----------------|------------------------------------------------------|
| LEITE           | Leite puro, Achocolatado, Vitamina, Iogurte          |
| LEGUMES         | Abóbora, Abobrinha, Quiabo, Berinjela, Tomate...     |
| VERDURAS        | Acelga, Agrião, Alface, Espinafre, Repolho           |
| TUBÉRCULOS      | Batata, Mandioquinha                                 |
| PROTEÍNA        | Carnes bovina/suína, Aves, Peixes, Ovos              |
| CEREAIS         | Arroz, Pão, Bolacha                                  |
| GRÃOS           | Feijão                                               |
| FRUTAS          | Banana, Maçã, Mamão, Melancia                        |
| SUCO DE FRUTAS  | Sucos diversos                                       |

## 🖥 Como Funciona
```mermaid
sequenceDiagram
    Usuário->>Login: Acesso inicial
    Login-->>Admin: Credenciais válidas (admin)
    Login-->>Nutrição: Credenciais válidas (alimentacao)
    Admin->>Cadastro: Adiciona aluno + restrições
    Nutrição->>Refeição: Seleciona data/aluno
    Nutrição->>Cardápio: Escolhe alimentos do grupo
    Sistema->>Calendário: Armazena registro

Passo a Passo
1 Clone o repositório:
git clone https://github.com/seu-usuario/alimentacao-alunos-msdos.git

2 Crie e ative o ambiente virtual:
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

3 Instale as dependências:
pip install flask python-dotenv

4 Configure variáveis de ambiente:
echo "FLASK_APP=routes.py" > .flaskenv
echo "FLASK_ENV=development" >> .flaskenv

5 Execute a aplicação:
flask run

Acesse:
http://localhost:5000

🔑 Credenciais de Teste
Perfil	Usuário	Senha
Administrador	admin	senha
Nutrição	responsavel1	alimentacao1
Nutrição	responsavel2	alimentacao2

🚧 Melhorias Futuras
Implementar banco de dados SQL

Adicionar relatórios nutricionais

Criar módulo para pais/responsáveis

Desenvolver sistema de alertas

Adicionar autenticação OAuth

⚠️ Avisos Importantes
Dados Voláteis: Os registros são armazenados em memória

Segurança: Usar apenas para demonstração (senhas em texto plano)

Persistência: Reinicie o servidor para limpar os dados

📄 Licença
Projeto desenvolvido para [Univesp] sob licença MIT. Consulte o arquivo LICENSE para detalhes.

Desenvolvido por Arthur Univesp



