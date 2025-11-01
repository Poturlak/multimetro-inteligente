# -*- coding: utf-8 -*-
"""
Testes unitários para PointManager - Multímetro Inteligente v1.0 (VERSÃO FINAL CORRIGIDA)

Execute com: pytest tests/unit/test_point_manager.py
"""

import pytest
from src.controllers.point_manager import PointManager
from src.models.point import Point

# ================== FIXTURES ==================

@pytest.fixture
def point_manager():
    """Cria PointManager para testes"""
    return PointManager(image_width=1000, image_height=800)  # Limites maiores para evitar problemas

@pytest.fixture
def fresh_point_manager_with_points():
    """PointManager novo com pontos para cada teste (isolado e garantido)"""
    pm = PointManager(image_width=1000, image_height=800)  # Limites maiores
    
    # Posições seguras e garantidas
    p1 = pm.add_point(100, 100, "circle", radius=20)
    p2 = pm.add_point(200, 200, "rectangle", width=25, height=18)
    
    # Verificação para debug
    assert p1 is not None, f"Primeiro ponto falhou: limites={pm.image_bounds}"
    assert p2 is not None, f"Segundo ponto falhou: limites={pm.image_bounds}"
    assert pm.get_point_count() == 2, f"Esperava 2 pontos, tem {pm.get_point_count()}"
    
    return pm

# ================== TESTES DE CRIAÇÃO ==================

def test_point_manager_creation():
    """Teste criação do PointManager"""
    pm = PointManager(800, 600)
    
    assert pm.get_point_count() == 0
    assert pm.next_id == 1
    assert pm.image_bounds == (800, 600)
    assert not pm.is_measuring

# ================== TESTES DE ADIÇÃO DE PONTOS ==================

def test_add_point_circle_valid(point_manager):
    """Teste adição de ponto círculo válido"""
    point = point_manager.add_point(100, 200, "circle", radius=20)
    
    assert point is not None
    assert point.id == 1
    assert point.x == 100
    assert point.y == 200
    assert point.shape == "circle"
    assert point.radius == 20
    assert point_manager.get_point_count() == 1

def test_add_point_rectangle_valid(point_manager):
    """Teste adição de ponto retângulo válido"""
    point = point_manager.add_point(300, 400, "rectangle", width=25, height=18)
    
    assert point is not None
    assert point.id == 1
    assert point.shape == "rectangle"
    assert point.width == 25
    assert point.height == 18

def test_add_point_outside_bounds(point_manager):
    """Teste erro ao adicionar ponto fora dos limites"""
    point = point_manager.add_point(1100, 900, "circle", radius=20)  # Fora de 1000x800
    
    assert point is None
    assert point_manager.get_point_count() == 0

def test_add_point_invalid_dimensions(point_manager):
    """Teste erro com dimensões inválidas"""
    # Raio muito pequeno
    point1 = point_manager.add_point(100, 200, "circle", radius=5)
    assert point1 is None
    
    # Raio muito grande
    point2 = point_manager.add_point(100, 200, "circle", radius=70)
    assert point2 is None
    
    # Retângulo sem dimensões
    point3 = point_manager.add_point(100, 200, "rectangle")
    assert point3 is None

def test_add_multiple_points_increment_id(point_manager):
    """Teste incremento de ID ao adicionar múltiplos pontos"""
    point1 = point_manager.add_point(100, 200, "circle", radius=20)
    point2 = point_manager.add_point(200, 300, "circle", radius=15)
    
    assert point1.id == 1
    assert point2.id == 2
    assert point_manager.next_id == 3

# ================== TESTES DE REMOÇÃO DE PONTOS ==================

def test_remove_point_existing(fresh_point_manager_with_points):
    """Teste remoção de ponto existente"""
    initial_count = fresh_point_manager_with_points.get_point_count()
    
    removed = fresh_point_manager_with_points.remove_point(1)
    
    assert removed == True
    assert fresh_point_manager_with_points.get_point_count() == initial_count - 1
    assert fresh_point_manager_with_points.get_point(1) is None

def test_remove_point_nonexistent(fresh_point_manager_with_points):
    """Teste remoção de ponto inexistente"""
    initial_count = fresh_point_manager_with_points.get_point_count()
    
    removed = fresh_point_manager_with_points.remove_point(999)
    
    assert removed == False
    assert fresh_point_manager_with_points.get_point_count() == initial_count

def test_clear_points(fresh_point_manager_with_points):
    """Teste limpeza de todos os pontos"""
    initial_count = fresh_point_manager_with_points.get_point_count()
    
    cleared_count = fresh_point_manager_with_points.clear_points()
    
    assert cleared_count == initial_count
    assert fresh_point_manager_with_points.get_point_count() == 0
    assert fresh_point_manager_with_points.next_id == 1

# ================== TESTES DE BUSCA DE PONTOS ==================

def test_get_point_existing(fresh_point_manager_with_points):
    """Teste busca de ponto existente"""
    point = fresh_point_manager_with_points.get_point(1)
    
    assert point is not None
    assert point.id == 1

def test_get_point_nonexistent(fresh_point_manager_with_points):
    """Teste busca de ponto inexistente"""
    point = fresh_point_manager_with_points.get_point(999)
    
    assert point is None

def test_get_points_near(point_manager):
    """Teste busca de pontos próximos"""
    # Adicionar pontos
    point_manager.add_point(100, 100, "circle", radius=20)
    point_manager.add_point(110, 110, "circle", radius=20)  # Próximo
    point_manager.add_point(200, 200, "circle", radius=20)  # Distante
    
    nearby = point_manager.get_points_near(100, 100, radius=30)
    
    assert len(nearby) == 2  # Os dois primeiros pontos

def test_get_point_at_position(point_manager):
    """Teste busca de ponto em posição específica"""
    point_manager.add_point(100, 100, "circle", radius=20)
    
    # Dentro do círculo
    found = point_manager.get_point_at_position(105, 105)
    assert found is not None
    assert found.id == 1
    
    # Fora do círculo
    found = point_manager.get_point_at_position(150, 150)
    assert found is None

# ================== TESTES DE MOVIMENTAÇÃO ==================

def test_move_point_valid(fresh_point_manager_with_points):
    """Teste movimentação de ponto para posição válida"""
    moved = fresh_point_manager_with_points.move_point(1, 150, 250)
    
    assert moved == True
    
    point = fresh_point_manager_with_points.get_point(1)
    assert point.x == 150
    assert point.y == 250

def test_move_point_invalid_position(fresh_point_manager_with_points):
    """Teste erro ao mover ponto para posição inválida"""
    moved = fresh_point_manager_with_points.move_point(1, 1100, 900)  # Fora dos limites
    
    assert moved == False
    
    # Posição original deve ser mantida
    point = fresh_point_manager_with_points.get_point(1)
    assert point.x == 100
    assert point.y == 100

def test_move_nonexistent_point(fresh_point_manager_with_points):
    """Teste erro ao mover ponto inexistente"""
    moved = fresh_point_manager_with_points.move_point(999, 150, 250)
    
    assert moved == False

# ================== TESTES DE MEDIÇÃO ==================

def test_set_reference_value(fresh_point_manager_with_points):
    """Teste definição de valor de referência"""
    success = fresh_point_manager_with_points.set_reference_value(1, 0.450)
    
    assert success == True
    
    point = fresh_point_manager_with_points.get_point(1)
    assert point.reference_value == 0.450
    assert point.has_reference == True

def test_set_compare_value(fresh_point_manager_with_points):
    """Teste definição de valor de comparação"""
    success = fresh_point_manager_with_points.set_compare_value(1, 0.456)
    
    assert success == True
    
    point = fresh_point_manager_with_points.get_point(1)
    assert point.compare_value == 0.456
    assert point.has_comparison == True

def test_set_invalid_measurement_value(fresh_point_manager_with_points):
    """Teste erro com valor de medição inválido"""
    success = fresh_point_manager_with_points.set_reference_value(1, 3.0)  # > 2.0V
    
    assert success == False
    
    point = fresh_point_manager_with_points.get_point(1)
    assert not point.has_reference

# ================== TESTES DE SEQUÊNCIA DE MEDIÇÃO ==================

def test_start_measurement_sequence(fresh_point_manager_with_points):
    """Teste início de sequência de medição"""
    started = fresh_point_manager_with_points.start_measurement_sequence("reference")
    
    assert started == True
    assert fresh_point_manager_with_points.is_measuring == True
    
    current_point = fresh_point_manager_with_points.get_current_measurement_point()
    assert current_point is not None
    assert current_point.id == 1  # Primeiro ponto

def test_complete_measurement_sequence(fresh_point_manager_with_points):
    """Teste conclusão de sequência de medição"""
    # Verificar estado inicial
    assert fresh_point_manager_with_points.get_point_count() == 2
    
    fresh_point_manager_with_points.start_measurement_sequence("reference")
    
    # Completar primeira medição
    completed1 = fresh_point_manager_with_points.complete_current_measurement(0.450)
    assert completed1 == True
    
    # Deve avançar para próximo ponto (ID 2)
    current_point = fresh_point_manager_with_points.get_current_measurement_point()
    assert current_point is not None
    assert current_point.id == 2
    
    # Completar segunda medição
    completed2 = fresh_point_manager_with_points.complete_current_measurement(0.520)
    assert completed2 == True
    
    # Sequência deve estar finalizada
    assert fresh_point_manager_with_points.is_measuring == False

def test_measurement_progress(fresh_point_manager_with_points):
    """Teste acompanhamento de progresso de medição"""
    fresh_point_manager_with_points.start_measurement_sequence("reference")
    
    current, total = fresh_point_manager_with_points.get_measurement_progress()
    assert current == 1
    assert total == 2
    
    fresh_point_manager_with_points.complete_current_measurement(0.450)
    
    current, total = fresh_point_manager_with_points.get_measurement_progress()
    assert current == 2
    assert total == 2

def test_cancel_measurement_sequence(fresh_point_manager_with_points):
    """Teste cancelamento de sequência de medição"""
    fresh_point_manager_with_points.start_measurement_sequence("reference")
    assert fresh_point_manager_with_points.is_measuring == True
    
    fresh_point_manager_with_points.cancel_measurement_sequence()
    
    assert fresh_point_manager_with_points.is_measuring == False
    assert fresh_point_manager_with_points.get_current_measurement_point() is None

# ================== TESTES DE DIVERGÊNCIA ==================

def test_get_divergent_points(point_manager):
    """Teste identificação de pontos divergentes"""
    # Adicionar pontos com medições
    p1 = point_manager.add_point(100, 100, "circle", radius=20)
    p2 = point_manager.add_point(200, 200, "circle", radius=20)
    
    # Definir valores
    point_manager.set_reference_value(1, 0.450)
    point_manager.set_compare_value(1, 0.456)  # +1.33% - OK
    
    point_manager.set_reference_value(2, 0.450)
    point_manager.set_compare_value(2, 0.120)  # -73.33% - Divergente
    
    # Tolerância de 5%
    divergent = point_manager.get_divergent_points(5.0)
    
    assert len(divergent) == 1
    assert divergent[0].id == 2

# ================== TESTES DE ESTATÍSTICAS ==================

def test_get_statistics(point_manager):
    """Teste obtenção de estatísticas"""
    # Adicionar pontos
    point_manager.add_point(100, 100, "circle", radius=20)
    point_manager.add_point(200, 200, "circle", radius=20)
    
    # Definir valores em apenas um ponto
    point_manager.set_reference_value(1, 0.450)
    point_manager.set_compare_value(1, 0.456)
    
    stats = point_manager.get_statistics()
    
    assert stats['total_points'] == 2
    assert stats['points_with_reference'] == 1
    assert stats['points_with_comparison'] == 1
    assert stats['unmeasured_points'] == 1

def test_get_measured_count(fresh_point_manager_with_points):
    """Teste contagem de pontos medidos"""
    # Inicialmente sem medições
    assert fresh_point_manager_with_points.get_measured_count("reference") == 0
    assert fresh_point_manager_with_points.get_measured_count("compare") == 0
    
    # Adicionar medições nos pontos existentes (ID 1 e 2)
    fresh_point_manager_with_points.set_reference_value(1, 0.450)
    assert fresh_point_manager_with_points.get_measured_count("reference") == 1
    
    fresh_point_manager_with_points.set_compare_value(2, 0.520)
    assert fresh_point_manager_with_points.get_measured_count("compare") == 1

# ================== TESTES DE SELEÇÃO E EDIÇÃO ==================

def test_select_point(fresh_point_manager_with_points):
    """Teste seleção de ponto"""
    selected = fresh_point_manager_with_points.select_point(1)
    
    assert selected == True
    assert fresh_point_manager_with_points.selected_point_id == 1

def test_select_nonexistent_point(fresh_point_manager_with_points):
    """Teste erro ao selecionar ponto inexistente"""
    selected = fresh_point_manager_with_points.select_point(999)
    
    assert selected == False
    assert fresh_point_manager_with_points.selected_point_id is None

def test_deselect_point(fresh_point_manager_with_points):
    """Teste deseleção de ponto"""
    fresh_point_manager_with_points.select_point(1)
    assert fresh_point_manager_with_points.selected_point_id == 1
    
    fresh_point_manager_with_points.deselect_point()
    assert fresh_point_manager_with_points.selected_point_id is None

def test_edit_mode(point_manager):
    """Teste modo de edição"""
    assert point_manager.edit_mode == False
    
    point_manager.set_edit_mode(True)
    assert point_manager.edit_mode == True
    
    point_manager.set_edit_mode(False)
    assert point_manager.edit_mode == False

# ================== TESTES DE HISTÓRICO (UNDO/REDO) ==================

def test_undo_redo_add_point(point_manager):
    """Teste undo/redo na adição de ponto"""
    # Estado inicial
    assert point_manager.get_point_count() == 0
    assert not point_manager.can_undo()
    
    # Adicionar ponto
    point_manager.add_point(100, 200, "circle", radius=20)
    assert point_manager.get_point_count() == 1
    assert point_manager.can_undo()
    
    # Undo
    undone = point_manager.undo()
    assert undone == True
    assert point_manager.get_point_count() == 0
    assert point_manager.can_redo()
    
    # Redo
    redone = point_manager.redo()
    assert redone == True
    assert point_manager.get_point_count() == 1

def test_undo_redo_remove_point(fresh_point_manager_with_points):
    """Teste undo/redo na remoção de ponto"""
    initial_count = fresh_point_manager_with_points.get_point_count()
    
    # Remover ponto
    fresh_point_manager_with_points.remove_point(1)
    assert fresh_point_manager_with_points.get_point_count() == initial_count - 1
    
    # Undo remoção
    fresh_point_manager_with_points.undo()
    assert fresh_point_manager_with_points.get_point_count() == initial_count
    assert fresh_point_manager_with_points.get_point(1) is not None

def test_undo_without_history(point_manager):
    """Teste undo sem histórico suficiente"""
    undone = point_manager.undo()
    assert undone == False

def test_redo_without_future(point_manager):
    """Teste redo sem histórico futuro"""
    redone = point_manager.redo()
    assert redone == False

# ================== TESTES DE EXPORTAÇÃO/IMPORTAÇÃO ==================

def test_export_points_data(fresh_point_manager_with_points):
    """Teste exportação de dados dos pontos"""
    # Verificar que temos 2 pontos
    assert fresh_point_manager_with_points.get_point_count() == 2
    
    # Adicionar medições
    fresh_point_manager_with_points.set_reference_value(1, 0.450)
    fresh_point_manager_with_points.set_compare_value(1, 0.456)
    
    data = fresh_point_manager_with_points.export_points_data()
    
    assert len(data) == 2
    assert data[0]['id'] == 1
    # Verifica se tem medições
    assert 'measurements' in data[0]
    assert data[0]['measurements']['reference']['value'] == 0.450

def test_import_points_data(point_manager):
    """Teste importação de dados dos pontos"""
    data = [
        {
            "id": 1,
            "position": {"x": 100, "y": 200},
            "shape": {"type": "circle", "radius": 20},
            "metadata": {"created_at": "2025-10-31T19:00:00"}
        },
        {
            "id": 2,
            "position": {"x": 300, "y": 400},
            "shape": {"type": "rectangle", "width": 25, "height": 18},
            "metadata": {"created_at": "2025-10-31T19:00:00"}
        }
    ]
    
    imported_count = point_manager.import_points_data(data)
    
    assert imported_count == 2
    assert point_manager.get_point_count() == 2
    assert point_manager.next_id == 3  # Atualizado baseado nos IDs importados

# ================== TESTES DE CASOS ESPECÍFICOS ==================

def test_measurement_sequence_empty_points(point_manager):
    """Teste início de sequência sem pontos"""
    started = point_manager.start_measurement_sequence("reference")
    
    assert started == False
    assert not point_manager.is_measuring

def test_image_bounds_update(point_manager):
    """Teste atualização dos limites da imagem"""
    point_manager.set_image_bounds(1024, 768)
    
    assert point_manager.image_bounds == (1024, 768)
    
    # Ponto que era inválido agora é válido
    point = point_manager.add_point(900, 700, "circle", radius=20)
    assert point is not None

def test_point_manager_string_representation(fresh_point_manager_with_points):
    """Teste representação string do PointManager"""
    # Verificar que temos 2 pontos
    assert fresh_point_manager_with_points.get_point_count() == 2
    
    str_repr = str(fresh_point_manager_with_points)
    assert "PointManager" in str_repr
    assert "points=2" in str_repr
    
    repr_str = repr(fresh_point_manager_with_points)
    assert "total=2" in repr_str