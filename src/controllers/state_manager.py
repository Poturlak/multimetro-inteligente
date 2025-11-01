# -*- coding: utf-8 -*-
"""
StateManager - Gerenciador de estados da aplicação Multímetro Inteligente.

Estados do sistema:
- INICIAL: Tela de boas-vindas, sem projeto carregado
- EDICAO: Imagem carregada, permitindo zoom/pan
- MARCACAO: Modo de marcação de pontos na imagem  
- MEDICAO: Processo de medição dos pontos marcados
- COMPARACAO: Análise e comparação dos resultados
"""

from enum import Enum
from typing import List, Dict, Optional, Callable, Any
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime


class AppState(Enum):
    """Enumera todos os estados possíveis da aplicação."""
    
    INICIAL = "inicial"        # Estado inicial - sem projeto
    EDICAO = "edicao"          # Visualização/edição da imagem
    MARCACAO = "marcacao"      # Marcação de pontos de medição
    MEDICAO = "medicao"        # Processo de medição
    COMPARACAO = "comparacao"  # Comparação e análise
    
    def to_index(self) -> int:
        """
        Converte estado para índice da toolbar stack.
        Usado para sincronizar com QStackedWidget das toolbars.
        """
        indices = {
            AppState.INICIAL: 0,
            AppState.EDICAO: 1,
            AppState.MARCACAO: 2,
            AppState.MEDICAO: 3,
            AppState.COMPARACAO: 4
        }
        return indices.get(self, 0)
    
    def get_display_name(self) -> str:
        """Obtém nome amigável do estado."""
        names = {
            AppState.INICIAL: "Inicial",
            AppState.EDICAO: "Edição",
            AppState.MARCACAO: "Marcação",
            AppState.MEDICAO: "Medição",
            AppState.COMPARACAO: "Comparação"
        }
        return names.get(self, self.value.title())
    
    def get_description(self) -> str:
        """Obtém descrição do estado."""
        descriptions = {
            AppState.INICIAL: "Carregue uma imagem ou projeto para começar",
            AppState.EDICAO: "Visualize e ajuste a imagem da placa",
            AppState.MARCACAO: "Marque os pontos de medição na placa",
            AppState.MEDICAO: "Meça os valores nos pontos marcados",
            AppState.COMPARACAO: "Compare e analise os resultados"
        }
        return descriptions.get(self, "")


class StateTransition:
    """Representa uma transição entre estados."""
    
    def __init__(self, from_state: AppState, to_state: AppState, 
                 condition: Callable[[], bool] = None, 
                 description: str = ""):
        self.from_state = from_state
        self.to_state = to_state  
        self.condition = condition or (lambda: True)
        self.description = description
        self.timestamp = datetime.now()


class StateManager(QObject):
    """
    Gerenciador de estados da aplicação.
    
    Responsabilidades:
    - Controlar transições entre estados
    - Validar se transições são permitidas
    - Manter histórico de estados
    - Notificar componentes sobre mudanças
    """
    
    # Sinais emitidos
    state_changed = pyqtSignal(AppState)                    # Quando estado muda
    state_transition_requested = pyqtSignal(AppState)       # Quando transição é solicitada
    state_transition_blocked = pyqtSignal(AppState, str)    # Quando transição é bloqueada
    
    def __init__(self):
        super().__init__()
        
        # Estado atual
        self.current_state = AppState.INICIAL
        self.previous_state: Optional[AppState] = None
        
        # Histórico
        self.state_history: List[StateTransition] = []
        self.max_history_size = 50
        
        # Validadores de transição
        self.transition_validators: Dict[tuple[AppState, AppState], Callable[[], tuple[bool, str]]] = {}
        
        # Callbacks por estado
        self.state_enter_callbacks: Dict[AppState, List[Callable]] = {}
        self.state_exit_callbacks: Dict[AppState, List[Callable]] = {}
        
        # Configuração inicial
        self._setup_default_transitions()
    
    def _setup_default_transitions(self):
        """Configura validadores padrão de transição."""
        
        # INICIAL → EDICAO: precisa ter imagem
        def can_go_to_edicao() -> tuple[bool, str]:
            # Esta validação será implementada pelo MainWindow
            return True, ""
        
        # EDICAO → MARCACAO: imagem deve estar carregada
        def can_go_to_marcacao() -> tuple[bool, str]:
            return True, ""
        
        # MARCACAO → MEDICAO: deve ter pelo menos um ponto
        def can_go_to_medicao() -> tuple[bool, str]:
            return True, ""
        
        # MEDICAO → COMPARACAO: deve ter medições
        def can_go_to_comparacao() -> tuple[bool, str]:
            return True, ""
        
        # Registra validadores
        self.transition_validators = {
            (AppState.INICIAL, AppState.EDICAO): can_go_to_edicao,
            (AppState.EDICAO, AppState.MARCACAO): can_go_to_marcacao,
            (AppState.MARCACAO, AppState.MEDICAO): can_go_to_medicao,
            (AppState.MEDICAO, AppState.COMPARACAO): can_go_to_comparacao
        }
    
    def change_state(self, new_state: AppState, force: bool = False) -> bool:
        """
        Solicita mudança de estado.
        
        Args:
            new_state: Estado de destino
            force: Se True, ignora validações
            
        Returns:
            True se mudança foi bem-sucedida
        """
        if new_state == self.current_state:
            return True  # Já está no estado desejado
        
        # Emite sinal de solicitação
        self.state_transition_requested.emit(new_state)
        
        # Validação de transição
        if not force:
            can_transition, reason = self._can_transition_to(new_state)
            if not can_transition:
                self.state_transition_blocked.emit(new_state, reason)
                return False
        
        # Executa transição
        return self._execute_transition(new_state)
    
    def _can_transition_to(self, target_state: AppState) -> tuple[bool, str]:
        """
        Verifica se pode transicionar para o estado alvo.
        
        Returns:
            (pode_transicionar, motivo)
        """
        # Verifica se existe validador específico
        validator_key = (self.current_state, target_state)
        if validator_key in self.transition_validators:
            return self.transition_validators[validator_key]()
        
        # Transições sempre permitidas (voltar estados anteriores)
        allowed_backward = [
            (AppState.EDICAO, AppState.INICIAL),
            (AppState.MARCACAO, AppState.EDICAO),
            (AppState.MEDICAO, AppState.MARCACAO),
            (AppState.COMPARACAO, AppState.MEDICAO),
            (AppState.COMPARACAO, AppState.EDICAO)  # Reiniciar análise
        ]
        
        if (self.current_state, target_state) in allowed_backward:
            return True, ""
        
        # Por padrão, não permite transições não definidas
        return False, f"Transição de {self.current_state.value} para {target_state.value} não permitida"
    
    def _execute_transition(self, new_state: AppState) -> bool:
        """
        Executa a transição de estado.
        
        Returns:
            True se transição foi bem-sucedida
        """
        try:
            old_state = self.current_state
            
            # Callbacks de saída do estado atual
            self._call_exit_callbacks(old_state)
            
            # Atualiza estado
            self.previous_state = old_state
            self.current_state = new_state
            
            # Registra no histórico
            transition = StateTransition(old_state, new_state)
            self.state_history.append(transition)
            
            # Limita tamanho do histórico
            if len(self.state_history) > self.max_history_size:
                self.state_history = self.state_history[-self.max_history_size:]
            
            # Callbacks de entrada do novo estado
            self._call_enter_callbacks(new_state)
            
            # Emite sinal de mudança
            self.state_changed.emit(new_state)
            
            # Log da transição
            print(f"🔄 Estado: {old_state.value} → {new_state.value}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na transição de estado: {e}")
            return False
    
    def _call_enter_callbacks(self, state: AppState):
        """Chama callbacks de entrada do estado."""
        callbacks = self.state_enter_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Erro em callback de entrada {state.value}: {e}")
    
    def _call_exit_callbacks(self, state: AppState):
        """Chama callbacks de saída do estado.""" 
        callbacks = self.state_exit_callbacks.get(state, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Erro em callback de saída {state.value}: {e}")
    
    # Métodos públicos de consulta
    def get_current_state(self) -> AppState:
        """Obtém estado atual."""
        return self.current_state
    
    def get_previous_state(self) -> Optional[AppState]:
        """Obtém estado anterior."""
        return self.previous_state
    
    def is_in_state(self, state: AppState) -> bool:
        """Verifica se está em um estado específico."""
        return self.current_state == state
    
    def is_in_states(self, states: List[AppState]) -> bool:
        """Verifica se está em qualquer um dos estados da lista."""
        return self.current_state in states
    
    def can_go_back(self) -> bool:
        """Verifica se pode voltar ao estado anterior."""
        return (self.previous_state is not None and 
                self._can_transition_to(self.previous_state)[0])
    
    def go_back(self) -> bool:
        """Volta ao estado anterior."""
        if not self.can_go_back():
            return False
        return self.change_state(self.previous_state)
    
    def get_state_history(self, limit: int = 10) -> List[StateTransition]:
        """Obtém histórico de transições."""
        return self.state_history[-limit:]
    
    # Métodos de configuração
    def register_transition_validator(self, from_state: AppState, to_state: AppState, 
                                    validator: Callable[[], tuple[bool, str]]):
        """Registra validador personalizado de transição."""
        self.transition_validators[(from_state, to_state)] = validator
    
    def add_state_enter_callback(self, state: AppState, callback: Callable):
        """Adiciona callback para entrada em estado."""
        if state not in self.state_enter_callbacks:
            self.state_enter_callbacks[state] = []
        self.state_enter_callbacks[state].append(callback)
    
    def add_state_exit_callback(self, state: AppState, callback: Callable):
        """Adiciona callback para saída de estado."""
        if state not in self.state_exit_callbacks:
            self.state_exit_callbacks[state] = []
        self.state_exit_callbacks[state].append(callback)
    
    def remove_state_callback(self, state: AppState, callback: Callable):
        """Remove callback de estado."""
        if state in self.state_enter_callbacks:
            try:
                self.state_enter_callbacks[state].remove(callback)
            except ValueError:
                pass
        
        if state in self.state_exit_callbacks:
            try:
                self.state_exit_callbacks[state].remove(callback)
            except ValueError:
                pass
    
    # Métodos de utilidade
    def reset_to_initial(self):
        """Reseta para estado inicial."""
        self.change_state(AppState.INICIAL, force=True)
    
    def get_available_transitions(self) -> List[AppState]:
        """Obtém lista de estados para os quais pode transicionar."""
        available = []
        for state in AppState:
            if state != self.current_state:
                can_go, _ = self._can_transition_to(state)
                if can_go:
                    available.append(state)
        return available
    
    def get_state_info(self) -> Dict[str, Any]:
        """Obtém informações completas do estado atual."""
        return {
            'current_state': self.current_state,
            'previous_state': self.previous_state,
            'display_name': self.current_state.get_display_name(),
            'description': self.current_state.get_description(),
            'can_go_back': self.can_go_back(),
            'available_transitions': self.get_available_transitions(),
            'history_count': len(self.state_history)
        }