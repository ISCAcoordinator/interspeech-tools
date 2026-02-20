from ..conf import Config
from .base import Serialiser
from .cmt import InterspeechCMTSerialiser

SERIALISERS = {"cmt": InterspeechCMTSerialiser}


def instanciate_serialiser(configuration: Config) -> Serialiser:
    """Get the serialiser based on its name

    Parameters
    ----------
    configuration: Config
        The configuration file

    Returns
    -------
    Serialiser
        the serialiser instnace

    Raises
    ------
    Exception
        No serialiser for the given name is available

    """
    serialiser_name = configuration["input_data"]["serialiser"].lower()
    if not (serialiser_name in SERIALISERS):
        raise Exception(f"{serialiser_name} is not a valid serialiser")

    return SERIALISERS[serialiser_name](configuration)


__all__ = ["InterspeechCMTSerialiser"]
