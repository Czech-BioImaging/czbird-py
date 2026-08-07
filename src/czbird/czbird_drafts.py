"""czbird_draft.py — auto-generated all-optional "draft" twins of the strict
CZBIRD models, for partial/incremental editing.

For every strict model ``CZBIRDFoo`` there is a ``CZBIRDFooDraft`` where every
field is optional (defaults to unset/None) and nested CZBIRD references point at
the corresponding draft twins, so a draft can be filled to any depth without
tripping required-field or min_items constraints. validate_assignment stays on,
so each assignment is still type-checked. Promote a completed draft to the
strict model with ``to_strict``.
"""
from __future__ import annotations

import types
import typing
from typing import Annotated, Optional, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, create_model

from czbird import czbird_model as _strict


_STRICT = [c for n, c in vars(_strict).items()
           if isinstance(c, type) and issubclass(c, BaseModel)
           and c.__module__ == _strict.__name__ and c is not _strict._Base]

_STRICT_TO_DRAFT: dict[type, type] = {c: None for c in _STRICT}
_CFG = ConfigDict(validate_assignment=True, extra="forbid")


def _draftify(ann):
    if isinstance(ann, type) and ann in _STRICT_TO_DRAFT:
        return _STRICT_TO_DRAFT[ann]
    # Annotated[union, Field(discriminator=...)] — the discriminated profile /
    # tool_description unions. Rebuild the SAME discriminated union over the
    # draft members, keeping each member's Literal discriminator so pydantic can
    # still route by it (dropping it would make matching lossy/ambiguous).
    if hasattr(ann, "__metadata__"):
        inner = _draftify(ann.__args__[0])
        for meta in ann.__metadata__:
            disc = getattr(meta, "discriminator", None)
            if disc:
                return Annotated[inner, Field(discriminator=disc)]
        return inner
    o = get_origin(ann)
    if o is None:
        return ann
    new = tuple(_draftify(a) for a in get_args(ann))
    if o in (Union, types.UnionType):
        return Union[new]
    try:
        return o[new] if len(new) != 1 else o[new[0]]
    except TypeError:
        return ann


_NS = vars(_strict)  # namespace for resolving forward-ref annotations


def _resolve(ann):
    """Resolve a possibly-string / ForwardRef annotation to a real type."""
    if isinstance(ann, str):
        return eval(ann, _NS)  # noqa: S307 - trusted, generated model namespace
    if type(ann).__name__ == "ForwardRef":
        return eval(ann.__forward_arg__, _NS)  # noqa: S307
    return ann


def _is_discriminated(resolved) -> bool:
    if hasattr(resolved, "__metadata__"):
        return any(getattr(m, "discriminator", None) for m in resolved.__metadata__)
    return False


def _build(cls):
    fields = {}
    for name, f in cls.model_fields.items():
        resolved = _resolve(f.annotation)
        if _is_discriminated(resolved):
            # Discriminated-union fields (CZBIRDTool.tool_description,
            # Metadata.was_generated_by) are kept as the STRICT type in drafts.
            # A discriminated union can't be relaxed to an all-optional draft
            # union: routing needs the discriminator value present, which an
            # empty draft member lacks. The field is therefore required in the
            # draft and holds a fully-valid strict member (build it with a
            # prefill factory before promoting). All OTHER fields are relaxed to
            # optional draft twins as usual.
            fields[name] = (Optional[resolved], None)
        else:
            fields[name] = (Optional[_draftify(resolved)], None)
    return create_model(f"{cls.__name__}Draft", __config__=_CFG, **fields)


for _c in _STRICT:
    _STRICT_TO_DRAFT[_c] = _build(_c)
for _d in _STRICT_TO_DRAFT.values():
    _d.model_rebuild()

_g = globals()
for _c, _d in _STRICT_TO_DRAFT.items():
    _g[_d.__name__] = _d

__all__ = [d.__name__ for d in _STRICT_TO_DRAFT.values()] + ["to_strict", "draft_for"]


def draft_for(strict_cls: type) -> type:
    return _STRICT_TO_DRAFT[strict_cls]


def to_strict(draft: BaseModel, strict_cls: type) -> BaseModel:
    """Promote a (believed-complete) draft into a validated strict instance."""
    return strict_cls.model_validate(draft.model_dump(exclude_none=True))
