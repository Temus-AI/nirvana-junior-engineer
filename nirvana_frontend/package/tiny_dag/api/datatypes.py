from pydantic import BaseModel

class NodeData(BaseModel):
    id: int
    x: float
    y: float
    name: str
    target: str = ""
    input: list = []
    output: list = []
    code: str = ""
    fitness: float = 0.7
    reasoning: str = ""
    inputTypes: list = []
    outputTypes: list = []


class EdgeData(BaseModel):
    source: int
    target: int