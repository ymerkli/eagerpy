from typing import TYPE_CHECKING, Union, overload, Tuple, TypeVar, Generic
import sys

from .tensor import Tensor
from .tensor import TensorType
from .tensor import istensor

from .tensor import PyTorchTensor
from .tensor import TensorFlowTensor
from .tensor import JAXTensor
from .tensor import NumPyTensor

from .types import NativeTensor

if TYPE_CHECKING:
    # for static analyzers
    import torch


def _get_module_name(x) -> str:
    # splitting is necessary for TensorFlow tensors
    return type(x).__module__.split(".")[0]


@overload
def astensor(x: TensorType) -> TensorType:
    ...


@overload
def astensor(x: "torch.Tensor") -> PyTorchTensor:
    ...


@overload
def astensor(x: NativeTensor) -> Tensor:
    ...


def astensor(x: Union[NativeTensor, Tensor]) -> Tensor:
    if isinstance(x, Tensor):
        return x
    # we use the module name instead of isinstance
    # to avoid importing all the frameworks
    name = _get_module_name(x)
    m = sys.modules
    if name == "torch" and isinstance(x, m[name].Tensor):  # type: ignore
        return PyTorchTensor(x)
    if name == "tensorflow" and isinstance(x, m[name].Tensor):  # type: ignore
        return TensorFlowTensor(x)
    if name == "jax" and isinstance(x, m[name].numpy.ndarray):  # type: ignore
        return JAXTensor(x)
    if name == "numpy" and isinstance(x, m[name].ndarray):  # type: ignore
        return NumPyTensor(x)
    raise ValueError(f"Unknown type: {type(x)}")


def astensors(*xs: Union[NativeTensor, Tensor]) -> Tuple[Tensor, ...]:
    return tuple(astensor(x) for x in xs)


T = TypeVar("T")


class RestoreTypeFunc(Generic[T]):
    def __init__(self, x: T):
        self.unwrap = not istensor(x)

    @overload
    def __call__(self, x: Tensor) -> T:
        ...

    @overload  # noqa: F811
    def __call__(self, x: Tensor, y: Tensor) -> Tuple[T, T]:
        ...

    @overload  # noqa: F811
    def __call__(self, x: Tensor, y: Tensor, z: Tensor, *args: Tensor) -> Tuple[T, ...]:
        ...

    def __call__(self, *args):  # noqa: F811
        result = tuple(x.raw for x in args) if self.unwrap else args
        if len(result) == 1:
            result, = result
        return result


def astensor_(x: T) -> Tuple[Tensor, RestoreTypeFunc[T]]:
    return astensor(x), RestoreTypeFunc[T](x)


def astensors_(x: T, *xs: T) -> Tuple[Tuple[Tensor, ...], RestoreTypeFunc[T]]:
    return astensors(x, *xs), RestoreTypeFunc[T](x)
