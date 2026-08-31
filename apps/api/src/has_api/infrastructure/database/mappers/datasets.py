"""Maps dataset ORM models to domain entities."""

from has_api.domain.entities import Dataset, TestCase
from has_api.infrastructure.database.models.datasets import DatasetModel, TestCaseModel


def dataset_to_domain(model: DatasetModel) -> Dataset:
    if model.created_by_id is None:
        msg = "DatasetModel.created_by_id is required for domain mapping"
        raise ValueError(msg)
    return Dataset(
        id=model.id,
        workspace_id=model.workspace_id,
        name=model.name,
        description=model.description,
        created_by_id=model.created_by_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def dataset_to_orm(domain: Dataset, model: DatasetModel | None = None) -> DatasetModel:
    if model is None:
        model = DatasetModel(id=domain.id)
    model.workspace_id = domain.workspace_id
    model.name = domain.name
    model.description = domain.description
    model.created_by_id = domain.created_by_id
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model


def test_case_to_domain(model: TestCaseModel) -> TestCase:
    return TestCase(
        id=model.id,
        dataset_id=model.dataset_id,
        prompt=model.prompt,
        response=model.response,
        context=model.context,
        ground_truth=model.ground_truth,
        external_id=model.external_id,
        sort_order=model.sort_order,
        metadata=model.metadata_ or {},
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def test_case_to_orm(domain: TestCase, model: TestCaseModel | None = None) -> TestCaseModel:
    if model is None:
        model = TestCaseModel(id=domain.id)
    model.dataset_id = domain.dataset_id
    model.prompt = domain.prompt
    model.response = domain.response
    model.context = domain.context
    model.ground_truth = domain.ground_truth
    model.external_id = domain.external_id
    model.sort_order = domain.sort_order
    model.metadata_ = domain.metadata
    model.created_at = domain.created_at
    model.updated_at = domain.updated_at
    return model
