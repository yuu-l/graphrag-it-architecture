"""app/graph/schema.py 的单元测试。"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.graph.schema import (
    BusinessScenario,
    Component,
    ComponentCategory,
    DeploymentTopology,
    ExtractionResult,
    Relation,
    RelationType,
    Requirement,
)


def test_component_category_has_ten_categories() -> None:
    """类别常量应为 10 类，且含「向量数据库」。"""
    assert len(ComponentCategory) == 10
    assert ComponentCategory.VECTOR_DB.value == "向量数据库"


def test_relation_type_has_five_types() -> None:
    """关系类型应为 5 类，无 WEAKENS。"""
    assert len(RelationType) == 5
    assert {t.value for t in RelationType} == {
        "DEPENDS_ON",
        "MUTUAL_EXCLUSIVE",
        "ENHANCES",
        "SUITABLE_FOR",
        "INSTANCE_OF",
    }


def test_component_instantiation_and_id() -> None:
    comp = Component(
        name="Redis",
        aliases=["redis", "Redis 缓存"],
        category=ComponentCategory.CACHE,
        description="内存键值缓存",
    )
    assert comp.id == "Redis"
    assert comp.category is ComponentCategory.CACHE
    assert comp.aliases == ["redis", "Redis 缓存"]


def test_component_accepts_category_by_value() -> None:
    """传入枚举的 value（中文类别名）也应解析为对应类别。"""
    comp = Component(name="MySQL", category="数据库")
    assert comp.category is ComponentCategory.DATABASE


def test_component_rejects_invalid_category() -> None:
    with pytest.raises(ValidationError):
        Component(name="X", category="不存在的类别")


def test_relation_instantiation() -> None:
    rel = Relation(source="MySQL", target="主从部署", relation_type=RelationType.INSTANCE_OF)
    assert rel.relation_type is RelationType.INSTANCE_OF


def test_relation_accepts_type_by_value() -> None:
    """关系类型也应能按 value（字符串）解析。"""
    rel = Relation(source="a", target="b", relation_type="DEPENDS_ON")
    assert rel.relation_type is RelationType.DEPENDS_ON


def test_requirement_and_topology_instantiation() -> None:
    req = Requirement(dimension="可用性", value="高")
    topo = DeploymentTopology(name="主从", description="一主一从，读写分离")
    scenario = BusinessScenario(name="高并发电商", description="大流量、高并发读多写少")
    assert req.dimension == "可用性"
    assert topo.name == "主从"
    assert scenario.name == "高并发电商"


def test_extraction_result_holds_entities_and_relations() -> None:
    """抽取结果容器应能承载多类实体与关系。"""
    result = ExtractionResult(
        components=[
            Component(name="MySQL", category=ComponentCategory.DATABASE),
            Component(name="Redis", category=ComponentCategory.CACHE),
        ],
        topologies=[DeploymentTopology(name="主从")],
        relations=[
            Relation(source="MySQL", target="主从", relation_type=RelationType.INSTANCE_OF),
        ],
    )
    assert len(result.components) == 2
    assert len(result.topologies) == 1
    assert len(result.relations) == 1


def test_component_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        Component(name="", category=ComponentCategory.CACHE)


def test_defaults_for_optional_fields() -> None:
    comp = Component(name="MySQL", category=ComponentCategory.DATABASE)
    assert comp.aliases == []
    assert comp.description == ""

    empty = ExtractionResult()
    assert empty.components == []
    assert empty.relations == []
