import pytest
from src.models.project import BoardProject
from src.models.point import Point
from PIL import Image

def create_sample_project():
    return BoardProject(
        name="Projeto Teste",
        board_model="MOD123",
        is_fully_functional=True,
        notes="Projeto para testes unitários"
    )

def test_creation_valid():
    p = create_sample_project()
    assert p.name == "Projeto Teste"
    assert p.is_fully_functional

def test_creation_invalid_name():
    with pytest.raises(ValueError):
        BoardProject(name="", board_model="MOD123", is_fully_functional=True)

def test_creation_invalid_model():
    with pytest.raises(ValueError):
        BoardProject(name="Projeto", board_model="", is_fully_functional=True)

def test_creation_requires_problem_description():
    with pytest.raises(ValueError):
        BoardProject(name="Projeto", board_model="MOD123", is_fully_functional=False, problem_description="")

def test_add_and_remove_point():
    p = create_sample_project()
    img = Image.new('RGB', (800, 600), color='white')
    p.set_image(img)
    point = Point(id=1, x=100, y=100, shape="circle", radius=10)
    p.add_point(point)
    assert len(p.points) == 1
    removed = p.remove_point(point.id)
    assert removed is True
    assert len(p.points) == 0

def test_add_point_outside_image():
    p = create_sample_project()
    img = Image.new('RGB', (100, 100), color='white')
    p.set_image(img)
    point = Point(id=1, x=200, y=200, shape="circle", radius=10)
    with pytest.raises(ValueError):
        p.add_point(point)

def test_statistics_and_summary():
    p = create_sample_project()
    img = Image.new('RGB', (800, 600), color='white')
    p.set_image(img)
    point1 = Point(id=1, x=50, y=50, shape="circle", radius=10)
    point1.set_reference_value(0.45)
    point1.set_compare_value(0.46)
    p.add_point(point1)
    stats = p.get_statistics()
    assert stats['total_points'] == 1
    summary = p.get_summary()
    assert "Projeto: Projeto Teste" in summary

def test_serialization_to_from_dict():
    p = create_sample_project()
    img = Image.new('RGB', (800, 600), color='white')
    p.set_image(img)
    point = Point(id=1, x=50, y=50, shape="circle", radius=10)
    p.add_point(point)
    d = p.to_dict()
    p2 = BoardProject.from_dict(d, img, p.points)
    assert p.name == p2.name
    assert len(p2.points) == 1
