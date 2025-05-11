
from weasyprint import HTML

HTML(string="<h1>Teste</h1>").write_pdf("teste.pdf")
print("PDF gerado com sucesso!")