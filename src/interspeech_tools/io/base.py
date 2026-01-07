from isca.model.core import ISCAObject
from isca.model.event import Conference


class Serialiser(ISCAObject):
    def load(self) -> Conference:
        raise NotImplementedError("This method should be implemented in a subclass")
