from src.Approval.AprovService import ServicoAprovacoes

# Example usage
servico_aprovacoes = ServicoAprovacoes()
response = servico_aprovacoes.cria_aprovacao("Approval Title", "Approval Description", ["approver1@example.com", "approver2@example.com"])
status = servico_aprovacoes.verifica_status("Approval Title")