# -*- coding: utf-8 -*-
"""
Testes unitários para StateManager - Multímetro Inteligente v1.0

Execute com: pytest tests/unit/test_state_manager.py
"""

import pytest
from src.controllers.state_manager import StateManager, AppState

# ================== FIXTURES ==================

@pytest.fixture
def state_manager():
    """Cria StateManager para testes"""
    return StateManager()

# ================== TESTES DE CRIAÇÃO ==================

def test_state_manager_creation():
    """Teste criação do StateManager"""
    sm = StateManager()
    
    assert sm.get_current_state() == AppState.INICIAL
    assert len(sm.get_state_history()) == 1
    assert sm.get_state_history()[0] == AppState.INICIAL

# ================== TESTES DE TRANSIÇÕES VÁLIDAS ==================

def test_valid_transition_inicial_to_edicao(state_manager):
    """Teste transição INICIAL → EDIÇÃO"""
    result = state_manager.change_state(AppState.EDICAO)
    
    assert result == True
    assert state_manager.get_current_state() == AppState.EDICAO

def test_valid_transition_edicao_to_marcacao(state_manager):
    """Teste transição EDIÇÃO → MARCAÇÃO"""
    # Primeiro vai para EDIÇÃO
    state_manager.change_state(AppState.EDICAO)
    
    # Depois para MARCAÇÃO
    result = state_manager.change_state(AppState.MARCACAO)
    
    assert result == True
    assert state_manager.get_current_state() == AppState.MARCACAO

def test_valid_transition_marcacao_to_medicao(state_manager):
    """Teste transição MARCAÇÃO → MEDIÇÃO"""
    # Caminho: INICIAL → EDIÇÃO → MARCAÇÃO → MEDIÇÃO
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    
    result = state_manager.change_state(AppState.MEDICAO)
    
    assert result == True
    assert state_manager.get_current_state() == AppState.MEDICAO

def test_valid_transition_medicao_to_comparacao(state_manager):
    """Teste transição MEDIÇÃO → COMPARAÇÃO"""
    # Caminho completo
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    state_manager.change_state(AppState.MEDICAO)
    
    result = state_manager.change_state(AppState.COMPARACAO)
    
    assert result == True
    assert state_manager.get_current_state() == AppState.COMPARACAO

# ================== TESTES DE TRANSIÇÕES INVÁLIDAS ==================

def test_invalid_transition_inicial_to_medicao(state_manager):
    """Teste transição inválida INICIAL → MEDIÇÃO"""
    result = state_manager.change_state(AppState.MEDICAO)
    
    assert result == False
    assert state_manager.get_current_state() == AppState.INICIAL

def test_invalid_transition_marcacao_to_edicao(state_manager):
    """Teste transição proibida MARCAÇÃO → EDIÇÃO"""
    # Chega até MARCAÇÃO
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    
    # Tenta voltar para EDIÇÃO (proibido por design)
    result = state_manager.change_state(AppState.EDICAO)
    
    assert result == False
    assert state_manager.get_current_state() == AppState.MARCACAO

# ================== TESTES DE VALIDAÇÃO DE CONTEXTO ==================

def test_state_validation_with_context(state_manager):
    """Teste validação com contexto de estado"""
    # Transição para MEDIÇÃO com contexto válido
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    
    result = state_manager.change_state(
        AppState.MEDICAO, 
        context={'points_count': 5, 'points_finalized': True}
    )
    
    assert result == True

def test_state_validation_invalid_context(state_manager):
    """Teste validação com contexto inválido"""
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    
    # Tentar ir para MEDIÇÃO sem pontos
    result = state_manager.change_state(
        AppState.MEDICAO,
        context={'points_count': 0}
    )
    
    assert result == False
    assert state_manager.get_current_state() == AppState.MARCACAO

# ================== TESTES DE VERIFICAÇÃO DE TRANSIÇÕES ==================

def test_can_transition_to(state_manager):
    """Teste verificação de transições possíveis"""
    # Em INICIAL, pode ir para EDIÇÃO
    assert state_manager.can_transition_to(AppState.EDICAO) == True
    
    # Em INICIAL, não pode ir direto para MEDIÇÃO
    assert state_manager.can_transition_to(AppState.MEDICAO) == False

def test_get_available_transitions(state_manager):
    """Teste listagem de transições disponíveis"""
    # Estado INICIAL
    transitions = state_manager.get_available_transitions()
    expected = [AppState.EDICAO, AppState.MARCACAO, AppState.MEDICAO, AppState.COMPARACAO]
    
    for state in expected:
        assert state in transitions

def test_same_state_transition(state_manager):
    """Teste transição para o mesmo estado (sempre válida)"""
    result = state_manager.change_state(AppState.INICIAL)
    
    assert result == True
    assert state_manager.get_current_state() == AppState.INICIAL

# ================== TESTES DE RESET ==================

def test_reset_to_initial(state_manager):
    """Teste reset para estado inicial"""
    # Avança alguns estados
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    state_manager.set_state_context('test_data', 'some_value')
    
    # Reset
    state_manager.reset_to_initial()
    
    assert state_manager.get_current_state() == AppState.INICIAL
    assert state_manager.get_state_context('test_data') is None

# ================== TESTES DE CONTEXTO ==================

def test_state_context_operations(state_manager):
    """Teste operações de contexto do estado"""
    # Definir valores
    state_manager.set_state_context('key1', 'value1')
    state_manager.set_state_context('key2', 123)
    
    # Recuperar valores
    assert state_manager.get_state_context('key1') == 'value1'
    assert state_manager.get_state_context('key2') == 123
    assert state_manager.get_state_context('key3', 'default') == 'default'
    
    # Limpar contexto
    state_manager.clear_state_context()
    assert state_manager.get_state_context('key1') is None

# ================== TESTES DE VERIFICAÇÃO DE ESTADO ==================

def test_is_in_state(state_manager):
    """Teste verificação de estado atual"""
    assert state_manager.is_in_state(AppState.INICIAL) == True
    assert state_manager.is_in_state(AppState.EDICAO) == False
    
    # Múltiplos estados
    assert state_manager.is_in_state(AppState.INICIAL, AppState.EDICAO) == True
    assert state_manager.is_in_state(AppState.MEDICAO, AppState.COMPARACAO) == False

# ================== TESTES DE CONFIGURAÇÃO ==================

def test_get_toolbar_config(state_manager):
    """Teste configuração de toolbar por estado"""
    # Estado INICIAL
    config = state_manager.get_toolbar_config()
    assert config['superior']['visible'] == False
    assert len(config['dinamica']['buttons']) == 2  # Abrir Imagem, Abrir Projeto
    
    # Estado EDIÇÃO
    state_manager.change_state(AppState.EDICAO)
    config = state_manager.get_toolbar_config()
    assert config['superior']['visible'] == True
    assert len(config['dinamica']['buttons']) > 5  # Várias ferramentas de edição

def test_requires_save_confirmation(state_manager):
    """Teste verificação de necessidade de confirmação"""
    # Estado INICIAL não requer confirmação
    assert state_manager.requires_save_confirmation() == False
    
    # Estados com trabalho em progresso requerem
    state_manager.change_state(AppState.EDICAO)
    assert state_manager.requires_save_confirmation() == True

def test_get_state_description(state_manager):
    """Teste descrição textual do estado"""
    descriptions = {
        AppState.INICIAL: "Aguardando ação do usuário",
        AppState.EDICAO: "Editando imagem da placa",
        AppState.MARCACAO: "Marcando pontos de medição"
    }
    
    for state, expected_desc in descriptions.items():
        state_manager.current_state = state
        assert expected_desc in state_manager.get_state_description()

# ================== TESTES DE HISTÓRICO ==================

def test_state_history_tracking(state_manager):
    """Teste rastreamento do histórico de estados"""
    initial_history_len = len(state_manager.get_state_history())
    
    # Fazer algumas transições
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO)
    
    history = state_manager.get_state_history()
    assert len(history) == initial_history_len + 2
    assert history[-2] == AppState.EDICAO
    assert history[-1] == AppState.MARCACAO

# ================== TESTES DE CASOS ESPECIAIS ==================

def test_can_exit_current_state(state_manager):
    """Teste verificação de possibilidade de sair do estado"""
    # Estado normal - pode sair
    can_exit, reason = state_manager.can_exit_current_state()
    assert can_exit == True
    assert reason is None
    
    # Estado com processo em andamento
    state_manager.change_state(AppState.EDICAO)
    state_manager.change_state(AppState.MARCACAO) 
    state_manager.change_state(AppState.MEDICAO)
    state_manager.set_state_context('measurement_in_progress', True)
    
    can_exit, reason = state_manager.can_exit_current_state()
    assert can_exit == False
    assert "Medição em andamento" in reason

def test_force_state_change(state_manager):
    """Teste mudança forçada de estado"""
    # Mudança forçada para estado inválido
    state_manager.force_state_change(AppState.COMPARACAO, "Teste forçado")
    
    assert state_manager.get_current_state() == AppState.COMPARACAO
    assert state_manager.get_state_context('force_reason') == "Teste forçado"
