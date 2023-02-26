from copy import deepcopy
from typing import Any, Dict, List


class BuildConfigException(Exception):
    """Raised in case of Configuration missmatch"""

    pass


class Build:
    def __init__(self, function, typename=None, config=None, name=None):
        self.function = function
        self.config = config
        self.typename = typename
        self.name = name
        self._built_instance = None

    def build(self, config=None):
        return self.function(config or self.config)

    def buil_once(self, config=None):
        if self._built_instance is None:
            self._built_instance = self.build(config)
        return self._built_instance


class ConfigBuild:
    def __init__(self):
        self.name_registry: Dict[str, Build] = {}
        self.typename_registry: Dict[str, Build] = {}
        self.entrypoint = None

    def register(self, typename):
        def wrapper(wrapee):
            self.typename_registry[typename] = Build(function=wrapee, typename=typename)
            return wrapee

        return wrapper

    def build_by_typename(self, typename: str) -> Any:
        return self.get_by_typename(typename).buil_once()

    def get_by_typename(self, typename: str) -> Build:
        try:
            builder = self.typename_registry[typename]
        except KeyError as e:
            raise BuildConfigException(
                f"typename `{typename}` should be found in the registry"
            ) from e
        return builder

    def build_by_name(self, name: str) -> Any:
        return self.get_by_name(name).buil_once()

    def get_by_name(self, name: str) -> Build:
        try:
            builder = self.name_registry[name]
        except KeyError as e:
            raise BuildConfigException(
                f"name `{name}` should be found in the registry"
            ) from e
        return builder

    def load_dict(self, config_dict: Dict[str, Any]):
        try:
            components: List[Dict[str, Any]] = config_dict["components"]
        except KeyError as e:
            raise BuildConfigException(
                "`components` field missing form the config"
            ) from e

        for component_config in components:
            name = _get_field(component_config, "name")
            self.name_registry[name] = self.make_builder(component_config)

    def make_builder(self, config):
        builder = self.get_by_typename(config["typename"])
        builder = deepcopy(builder)
        builder.config = config
        builder.name = config["name"]
        return builder

    def load_from_json(self, json_filename: str) -> None:
        import json

        with open(json_filename, "r") as json_file:
            config_dict = json.load(json_file)
        self.load_dict(config_dict)


def _get_field(dict_: Dict[str, Any], field_name: str) -> Any:
    try:
        field = dict_[field_name]
    except KeyError as e:
        raise BuildConfigException() from e
    else:
        return field
