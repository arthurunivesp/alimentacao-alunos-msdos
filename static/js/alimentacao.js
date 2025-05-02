function createTurmaChart(eventosTurma) {
    const refeicoesPorAluno = {};
    for (const [aluno, eventos] of Object.entries(eventosTurma)) {
        if (eventos.length > 0) {
            refeicoesPorAluno[aluno] = eventos.length;
        }
    }

    if (Object.keys(refeicoesPorAluno).length > 0) {
        const ctxTurma = document.getElementById('graficoRefeicoesTurma').getContext('2d');
        new Chart(ctxTurma, {
            type: 'bar',
            data: {
                labels: Object.keys(refeicoesPorAluno),
                datasets: [{
                    label: 'Número de Refeições',
                    data: Object.values(refeicoesPorAluno),
                    backgroundColor: '#4A90E2',
                    borderColor: '#2E5A88',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Número de Refeições'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Alunos'
                        }
                    }
                }
            }
        });
    }
}

function createAlunoChart(eventosAluno) {
    const refeicoesPorTipo = {};
    eventosAluno.forEach(item => {
        const tipo = item.evento.refeicao || 'Desconhecido';
        refeicoesPorTipo[tipo] = (refeicoesPorTipo[tipo] || 0) + 1;
    });

    if (Object.keys(refeicoesPorTipo).length > 0) {
        const ctxAluno = document.getElementById('graficoRefeicoesAluno').getContext('2d');
        new Chart(ctxAluno, {
            type: 'bar',
            data: {
                labels: Object.keys(refeicoesPorTipo),
                datasets: [{
                    label: 'Número de Refeições',
                    data: Object.values(refeicoesPorTipo),
                    backgroundColor: '#4A90E2',
                    borderColor: '#2E5A88',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Número de Refeições'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Tipo de Refeição'
                        }
                    }
                }
            }
        });
    }
}