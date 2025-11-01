import pytest
from src.models.point import Point

def test_point_creation_valid_circle():
    p = Point(id=1, x=50, y=100, shape="circle", radius=20)
    assert p.shape == "circle"
    assert p.radius == 20
    assert p.x == 50
    assert p.y == 100

def test_point_creation_valid_rectangle():
    p = Point(id=2, x=30, y=40, shape="rectangle", width=15, height=25)
    assert p.shape == "rectangle"
    assert p.width == 15
    assert p.height == 25

def test_point_invalid_shape():
    with pytest.raises(ValueError):
        Point(id=3, x=10, y=10, shape="triangle")

def test_point_radius_out_of_bounds():
    with pytest.raises(ValueError):
        Point(id=4, x=10, y=10, shape="circle", radius=100)

def test_point_difference_percent():
    p = Point(id=5, x=0, y=0, shape="circle", radius=10)
    p.set_reference_value(0.450)
    p.set_compare_value(0.456)
    assert round(p.difference_percent, 2) == 1.33

def test_point_is_divergent():
    p = Point(id=6, x=0, y=0, shape="circle", radius=10)
    p.set_reference_value(0.450)
    p.set_compare_value(0.120)
    assert p.is_divergent(5.0) == True

def test_point_to_dict_and_from_dict():
    p1 = Point(id=7, x=10, y=20, shape="rectangle", width=12, height=8)
    p1.set_reference_value(0.5)
    d = p1.to_dict()
    p2 = Point.from_dict(d)
    assert p1.id == p2.id
    assert p1.x == p2.x
    assert p1.shape == p2.shape
    assert p1.reference_value == p2.reference_value
