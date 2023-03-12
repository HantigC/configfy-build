import importlib
from typing import Any, Dict, List, Callable


class BuildConfigException(Exception):
    """Raised in case of Configuration missmatch"""

    pass


class Build:
    def __init__(self, function_name, context, scope, name):
        self.function_name = function_name
        self.scope = scope
        self.name = name
        self.context = context
        self.build_function = None
        self._built_instance = None

    def build(self, config=None):
        if self.build_function is None:
            self.build_function = _load_function_dyn(self.function_name)
        return self.build_function(config or self.scope)

    def build_once(self, config=None):
        if self._built_instance is None:
            self._built_instance = self.build(config)
        return self._built_instance

    def build_component(self, component_name):
        return self.context.build(self.scope[component_name])

    @classmethod
    def from_scope(cls, scope, context):
        return cls(
            function_name=scope["function_name"],
            context=context,
            scope=scope,
            name=scope["name"],
        )


class ConfigBuild:
    def __init__(self):
        self._registry: Dict[str, Build] = {}
        self.entrypoint = None

    def build_one(self, name) -> Any:
        return self.get(name).build_once()

    def build_entrypoint(self):
        return self.build(self.entrypoint)

    def build(self, name: str) -> Any:
        return self.get(name).build()

    def get(self, name: str) -> Build:
        try:
            builder = self.typename_registry[name]
        except KeyError as e:
            raise BuildConfigException(
                f"typename `{name}` should be found in the registry"
            ) from e
        return builder

    def load_dict(self, config_dict: Dict[str, Any]):
        try:
            components: List[Dict[str, Any]] = config_dict["components"]
        except KeyError as e:
            raise BuildConfigException(
                "`components` field missing from the config"
            ) from e

        for component_config in components:
            builder = Build.from_scope(component_config, self)
            self._registry[builder.name] = builder

        self.entrypoint = config_dict["entrypoint"]

    def load_json(self, json_filename: str) -> None:
        import json

        with open(json_filename, "r") as json_file:
            config_dict = json.load(json_file)
        self.load_dict(config_dict)

    @classmethod
    def from_json(cls, json_filename: str) -> "ConfigBuild":
        obj = cls()
        obj.load_json(json_filename)
        return obj


def _load_function_dyn(function_path: str) -> Callable[[Build], Any]:
    from_where, function_name = function_path.rsplit(".", 1)
    module = importlib.import_module(from_where)
    function = getattr(module, function_name)
    return function
