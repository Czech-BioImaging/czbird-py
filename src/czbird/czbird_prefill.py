"""Prefill factories — one minimal, valid, placeholder-filled instance per
strict CZBIRD class, for the current (cleanup-branch) model.

Each ``prefill_CZBIRDFoo()`` returns a fully valid instance whose scalar fields
carry obvious "(not yet defined)" placeholders and whose required arrays hold
exactly one prefilled item.

Notes on this model revision:
  * internal_id has been removed from every class.
  * CZBIRDTool.tool_description is a polymorphic (discriminated) field; the
    prefill uses the CZBIRDFulltextDescription variant.
  * employs_tool is now list[CZBIRDTool] (min 1 on most steps, min 0 on
    sample-preparation).
"""
from __future__ import annotations

from czbird import czbird_model as M

PLACEHOLDER = "(not yet defined)"
PLACEHOLDER_URL = "http://example.org/not-yet-defined"


# --- leaf / low-level ------------------------------------------------------ #
def prefill_CZBIRDOntologyTerm() -> M.CZBIRDOntologyTerm:
    return M.CZBIRDOntologyTerm(
        ontology_name=PLACEHOLDER, ontology_version=PLACEHOLDER,
        term_label=PLACEHOLDER, term_iri=PLACEHOLDER_URL,
        term_is_definite=False,
    )


def prefill_CZBIRDDigitalObjectSink() -> M.CZBIRDDigitalObjectSink:
    return M.CZBIRDDigitalObjectSink(data_path=PLACEHOLDER)


def prefill_CZBIRDDigitalImageSink() -> M.CZBIRDDigitalImageSink:
    return M.CZBIRDDigitalImageSink(
        images_path=PLACEHOLDER, images_metadata_kv_pairs=PLACEHOLDER)


def prefill_CZBIRDFulltextDescription() -> M.CZBIRDFulltextDescription:
    return M.CZBIRDFulltextDescription(
        description_type="explicit_description",
        title=PLACEHOLDER, description=PLACEHOLDER)


def prefill_CZBIRDReference() -> M.CZBIRDReference:
    return M.CZBIRDReference(
        description_type="reference_to_description", url=PLACEHOLDER_URL)


def prefill_CZBIRDTaxon() -> M.CZBIRDTaxon:
    return M.CZBIRDTaxon(
        accepted_scientific_name=prefill_CZBIRDOntologyTerm(),
        taxon_rank=prefill_CZBIRDOntologyTerm())


def prefill_CZBIRDOrganism() -> M.CZBIRDOrganism:
    return M.CZBIRDOrganism(belongs_to=prefill_CZBIRDTaxon())


def prefill_CZBIRDSpecimen() -> M.CZBIRDSpecimen:
    return M.CZBIRDSpecimen(
        title=PLACEHOLDER,
        is_part_of_organism=prefill_CZBIRDOrganism(),
        is_part_of=[prefill_CZBIRDOntologyTerm()],
        date_of_collection=PLACEHOLDER, place_of_collection=PLACEHOLDER)


def prefill_CZBIRDMethod() -> M.CZBIRDMethod:
    return M.CZBIRDMethod(
        method_type_label=[prefill_CZBIRDOntologyTerm()])


def prefill_CZBIRDTool() -> M.CZBIRDTool:
    return M.CZBIRDTool(
        is_software=False,
        tool_description=prefill_CZBIRDFulltextDescription())


# --- steps ----------------------------------------------------------------- #
def prefill_CZBIRDSamplePreparationStep() -> M.CZBIRDSamplePreparationStep:
    return M.CZBIRDSamplePreparationStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=[prefill_CZBIRDTool()])


def prefill_CZBIRDImageAcquisitionStep() -> M.CZBIRDImageAcquisitionStep:
    return M.CZBIRDImageAcquisitionStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=[prefill_CZBIRDTool()],
        main_digital_image=[prefill_CZBIRDDigitalImageSink()])


def prefill_CZBIRDImageProcessingStep() -> M.CZBIRDImageProcessingStep:
    return M.CZBIRDImageProcessingStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=[prefill_CZBIRDTool()])


def prefill_CZBIRDImageAnalysisStep() -> M.CZBIRDImageAnalysisStep:
    return M.CZBIRDImageAnalysisStep(
        step_label=PLACEHOLDER,
        realizes_method=prefill_CZBIRDMethod(),
        employs_tool=[prefill_CZBIRDTool()])


# --- pipelines ------------------------------------------------------------- #
def prefill_CZBIRDRawPipeline() -> M.CZBIRDRawPipeline:
    return M.CZBIRDRawPipeline(
        specimen=prefill_CZBIRDSpecimen(),
        image_acquisition_step=[prefill_CZBIRDImageAcquisitionStep()])


def prefill_CZBIRDProcessedPipeline() -> M.CZBIRDProcessedPipeline:
    return M.CZBIRDProcessedPipeline(
        input_data_url=[PLACEHOLDER_URL],
        image_processing_step=[prefill_CZBIRDImageProcessingStep()],
        result_data_image=[prefill_CZBIRDDigitalImageSink()])


def prefill_CZBIRDAnalysedPipeline() -> M.CZBIRDAnalysedPipeline:
    return M.CZBIRDAnalysedPipeline(
        input_data_url=[PLACEHOLDER_URL],
        image_analysis_step=[prefill_CZBIRDImageAnalysisStep()],
        result_data_object=[prefill_CZBIRDDigitalObjectSink()],
        result_data_image=[prefill_CZBIRDDigitalImageSink()])


# --- profiles -------------------------------------------------------------- #
def prefill_CZBIRDRawDataProfile() -> M.CZBIRDRawDataProfile:
    return M.CZBIRDRawDataProfile(
        profile_type="raw_data",
        raw_data_acquisition=[prefill_CZBIRDRawPipeline()])


def prefill_CZBIRDProcessedDataProfile() -> M.CZBIRDProcessedDataProfile:
    return M.CZBIRDProcessedDataProfile(
        profile_type="processed_data",
        data_processing=[prefill_CZBIRDProcessedPipeline()])


def prefill_CZBIRDAnalysedDataProfile() -> M.CZBIRDAnalysedDataProfile:
    return M.CZBIRDAnalysedDataProfile(
        profile_type="analysed_data",
        data_analysing=[prefill_CZBIRDAnalysedPipeline()])


def prefill_CZBIRDGeneralRecordProfile() -> M.CZBIRDGeneralRecordProfile:
    return M.CZBIRDGeneralRecordProfile(profile_type="general_record")


# --- root ------------------------------------------------------------------ #
def prefill_Metadata() -> M.Metadata:
    """A full, minimal, valid record using the raw-data profile."""
    return M.Metadata(
        internal_record_title=PLACEHOLDER,
        was_generated_by=prefill_CZBIRDRawDataProfile())


# --- dispatch -------------------------------------------------------------- #
PREFILL = {
    getattr(M, name[len("prefill_"):]): obj
    for name, obj in list(globals().items())
    if name.startswith("prefill_CZBIRD") and callable(obj)
}
PREFILL[M.Metadata] = prefill_Metadata


def prefill(cls):
    """Return a prefilled instance for a strict class (by class or name)."""
    if isinstance(cls, str):
        cls = getattr(M, cls)
    try:
        return PREFILL[cls]()
    except KeyError:
        raise ValueError(f"No prefill factory for {cls!r}")
