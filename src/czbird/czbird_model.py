"""CZBIRD metadata model — Pydantic v2 models generated from metadata.yaml.

Auto-generated. Each class validates on construction AND on attribute
assignment (model_config validate_assignment=True), giving you type-checked
setters without hand-written @property code.

Regenerate with:
    python generate.py metadata.yaml -o czbird_model.py
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(
        validate_assignment=True,   # re-validate on every attribute set
        extra="forbid",             # mirrors NRP dynamic: strict
        validate_default=True,
    )


class CZBIRDOntologyTerm(_Base):
    ontology_name: str = Field(...)
    ontology_version: str = Field(...)
    term_label: str = Field(...)
    term_iri: str = Field(...)
    term_is_definite: bool = Field(...)


class CZBIRDDigitalObjectSink(_Base):
    data_path: str = Field(...)


class CZBIRDDigitalImageSink(_Base):
    images_path: str = Field(...)
    images_metadata_kv_pairs: Optional[str] = Field(default=None)


class CZBIRDTaxon(_Base):
    accepted_scientific_name: CZBIRDOntologyTerm = Field(...)
    taxon_rank: CZBIRDOntologyTerm = Field(...)


class CZBIRDOrganism(_Base):
    belongs_to: CZBIRDTaxon = Field(...)


class CZBIRDSpecimen(_Base):
    title: Optional[str] = Field(default=None)
    is_part_of_organism: CZBIRDOrganism = Field(...)
    is_part_of: list[CZBIRDOntologyTerm] = Field(min_length=1)
    date_of_collection: Optional[str] = Field(default=None)
    place_of_collection: Optional[str] = Field(default=None)
    additional_note: Optional[list[str]] = Field(default=None, min_length=1)


class CZBIRDMethod(_Base):
    method_type_label: list[CZBIRDOntologyTerm] = Field(min_length=1)
    additional_note: Optional[list[str]] = Field(default=None, min_length=1)


class CZBIRDTool(_Base):
    is_software: bool = Field(...)
    tool_description: Annotated[CZBIRDFulltextDescription | CZBIRDReference, Field(discriminator="description_type")] = Field(...)
    additional_note: Optional[list[str]] = Field(default=None, min_length=1)


class CZBIRDFulltextDescription(_Base):
    description_type: Literal["explicit_description"] = Field(...)
    title: str = Field(...)
    description: str = Field(...)


class CZBIRDReference(_Base):
    description_type: Literal["reference_to_description"] = Field(...)
    url: str = Field(...)


class CZBIRDSamplePreparationStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: list[CZBIRDTool] = Field(...)
    aux_digital_object: Optional[list[CZBIRDDigitalObjectSink]] = Field(default=None, min_length=1)


class CZBIRDImageAcquisitionStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: list[CZBIRDTool] = Field(min_length=1)
    aux_digital_object: Optional[list[CZBIRDDigitalObjectSink]] = Field(default=None, min_length=1)
    main_digital_image: list[CZBIRDDigitalImageSink] = Field(min_length=1)


class CZBIRDImageProcessingStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: list[CZBIRDTool] = Field(min_length=1)
    aux_digital_object: Optional[list[CZBIRDDigitalObjectSink]] = Field(default=None, min_length=1)
    aux_digital_image: Optional[list[CZBIRDDigitalImageSink]] = Field(default=None, min_length=1)


class CZBIRDImageAnalysisStep(_Base):
    step_label: str = Field(...)
    realizes_method: CZBIRDMethod = Field(...)
    employs_tool: list[CZBIRDTool] = Field(min_length=1)
    aux_digital_object: Optional[list[CZBIRDDigitalObjectSink]] = Field(default=None, min_length=1)
    aux_digital_image: Optional[list[CZBIRDDigitalImageSink]] = Field(default=None, min_length=1)


class CZBIRDRawPipeline(_Base):
    specimen: CZBIRDSpecimen = Field(...)
    sample_preparation_step: Optional[list[CZBIRDSamplePreparationStep]] = Field(default=None, min_length=1)
    image_acquisition_step: list[CZBIRDImageAcquisitionStep] = Field(min_length=1)


class CZBIRDProcessedPipeline(_Base):
    input_data_url: list[str] = Field(min_length=1)
    image_processing_step: list[CZBIRDImageProcessingStep] = Field(min_length=1)
    result_data_image: list[CZBIRDDigitalImageSink] = Field(min_length=1)


class CZBIRDAnalysedPipeline(_Base):
    input_data_url: list[str] = Field(min_length=1)
    image_processing_step: Optional[list[CZBIRDImageProcessingStep]] = Field(default=None, min_length=1)
    image_analysis_step: list[CZBIRDImageAnalysisStep] = Field(min_length=1)
    result_data_object: list[CZBIRDDigitalObjectSink] = Field(...)
    result_data_image: list[CZBIRDDigitalImageSink] = Field(...)


class CZBIRDRawDataProfile(_Base):
    profile_type: Literal["raw_data"] = Field(...)
    raw_data_acquisition: list[CZBIRDRawPipeline] = Field(min_length=1)


class CZBIRDProcessedDataProfile(_Base):
    profile_type: Literal["processed_data"] = Field(...)
    data_processing: list[CZBIRDProcessedPipeline] = Field(min_length=1)


class CZBIRDAnalysedDataProfile(_Base):
    profile_type: Literal["analysed_data"] = Field(...)
    data_analysing: list[CZBIRDAnalysedPipeline] = Field(min_length=1)


class CZBIRDGeneralRecordProfile(_Base):
    profile_type: Literal["general_record"] = Field(...)


class Metadata(_Base):
    internal_record_title: str = Field(...)
    was_generated_by: Annotated[CZBIRDRawDataProfile | CZBIRDProcessedDataProfile | CZBIRDAnalysedDataProfile | CZBIRDGeneralRecordProfile, Field(discriminator="profile_type")] = Field(...)



Metadata.model_rebuild()
