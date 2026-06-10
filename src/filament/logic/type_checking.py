import sys

from pydantic import BaseModel
from beartype import beartype


def export_models(models: list[type[BaseModel]]):
    for to_model in models:
        to_module = sys.modules[to_model.__module__]
        for from_model in models:
            if from_model is not to_model:
                setattr(to_module, from_model.__name__, from_model)


def rebuild_models(models: list[type[BaseModel]]):
    for model in models:
        model.model_rebuild()


def beartype_models(models: list[type[BaseModel]]):
    for model in models:
        beartype(model)
