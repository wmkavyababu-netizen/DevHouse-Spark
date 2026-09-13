from typing import Dict, Type

from app.pipeline.adapters.base import BaseDeviceAdapter
from app.pipeline.adapters.generic_adapter import GenericDeviceAdapter
from app.pipeline.adapters.jsf_adapter import JsfDeviceAdapter
from app.pipeline.adapters.png_adapter import PngMetadataAdapter
from app.pipeline.adapters.xtf_adapter import XtfDeviceAdapter

_ADAPTER_REGISTRY: Dict[str, Type[BaseDeviceAdapter]] = {
    "png": PngMetadataAdapter,
    "json": PngMetadataAdapter,
    "xtf": XtfDeviceAdapter,
    "jsf": JsfDeviceAdapter,
    "hsx": GenericDeviceAdapter,
    "sdf": GenericDeviceAdapter,
}


def get_device_adapter(file_format_or_extension: str) -> BaseDeviceAdapter:
    """
    Factory returning the appropriate device adapter for a given format or file extension.
    """
    norm = file_format_or_extension.lower().lstrip(".")
    adapter_cls = _ADAPTER_REGISTRY.get(norm, GenericDeviceAdapter)
    return adapter_cls()


__all__ = [
    "BaseDeviceAdapter",
    "PngMetadataAdapter",
    "XtfDeviceAdapter",
    "JsfDeviceAdapter",
    "GenericDeviceAdapter",
    "get_device_adapter",
]
