"""业务域建模：实体/关系 Pydantic 模型 + 关系类型/类别常量。

对齐 `docs/BACKEND_STRUCTURE.md` §3（层间通信）/§4.1（知识图谱建模）与
`docs/IMPLEMENTATION_PLAN_DETAILED.md` Task 1 step 2。

模型设计原则：**通用** —— 既承载 LLM 抽取结果（Task 2 step 4），
也用于规则兜底校验（Task 4 step 4 的依赖/互斥/维度合法性）。
所有层间通信统一使用本模块模型，不绕过层边界。
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ComponentCategory(str, Enum):
    """组件类别常量（10 类）。

    每个枚举值即 Neo4j 中「类别实体」节点的 `name`；`Component.category`
    由此约束，非法类别在实例化阶段即被 Pydantic 校验拦截。
    """

    WEB_SERVER = "Web 服务器"
    APP_FRAMEWORK = "应用框架"
    DATABASE = "数据库"
    CACHE = "缓存"
    MESSAGE_QUEUE = "消息队列"
    SEARCH = "搜索"
    STORAGE = "存储"
    LOAD_BALANCER = "负载均衡"
    MONITORING = "监控"
    VECTOR_DB = "向量数据库"


class RelationType(str, Enum):
    """关系类型常量（5 类，无 WEAKENS）。

    - DEPENDS_ON：依赖（A 运行时依赖 B）
    - MUTUAL_EXCLUSIVE：互斥（A 与 B 不可同选）
    - ENHANCES：影响·增强（A 增强 B 的能力/效果）
    - SUITABLE_FOR：适配（A 适配某业务场景/部署形态）
    - INSTANCE_OF：归属（A 是某类别/部署形态的实例）
    """

    DEPENDS_ON = "DEPENDS_ON"
    MUTUAL_EXCLUSIVE = "MUTUAL_EXCLUSIVE"
    ENHANCES = "ENHANCES"
    SUITABLE_FOR = "SUITABLE_FOR"
    INSTANCE_OF = "INSTANCE_OF"


class Component(BaseModel):
    """组件实体（如 MySQL / Redis / Milvus）。"""

    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    category: ComponentCategory
    description: str = ""

    @property
    def id(self) -> str:
        """稳定实体 ID。消歧合并前以 `name` 为标识，loader 合并别名后统一。"""
        return self.name


class BusinessScenario(BaseModel):
    """业务场景实体（如高并发电商 / 数据仓库）。"""

    name: str = Field(min_length=1)
    description: str = ""


class Requirement(BaseModel):
    """需求维度实体（预算/规模/可用性/一致性 等业务维度取值）。"""

    dimension: str = Field(min_length=1)
    value: str = Field(min_length=1)


class DeploymentTopology(BaseModel):
    """部署形态实体（单机 / 主从 / 集群）。"""

    name: str = Field(min_length=1)
    description: str = ""


class Relation(BaseModel):
    """关系实例（source -[type]-> target），Neo4j 边的结构化表示。"""

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    relation_type: RelationType


class ExtractionResult(BaseModel):
    """LLM 实体/关系抽取结果容器（Task 2 step 4 产出，供 loader 消费）。"""

    components: list[Component] = Field(default_factory=list)
    scenarios: list[BusinessScenario] = Field(default_factory=list)
    requirements: list[Requirement] = Field(default_factory=list)
    topologies: list[DeploymentTopology] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
