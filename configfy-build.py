from typing import Dict


class BuildConfigException(Exception):
    pass


class Build:
    def __init__(self, function, typename=None, config=None):
        self.function = function
        self.config = config
        self.typename = typename
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

    def register(self, typename):
        def wrapper(wrapee):
            self.typename_registry[typename] = Build(function=wrapee, typename=typename)
            return wrapee
        return wrapper

    def build_by_typename(self, typename):
        try:
            builder = self.typename_registry[typename]
        except KeyError as e:
            raise BuildConfigException(
                f"`{typename}` should be found in the registry") from e
        return builder.buil_once()

    def build_by_name(self, name):
        try:
            builder = self.name_registry[name]
        except KeyError as e:
            raise BuildConfigException(
                f"`{name}` should be found in the registry") from e
        return builder.buil_once()
