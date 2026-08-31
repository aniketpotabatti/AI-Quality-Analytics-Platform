"""Dataset and test-case use cases."""

from __future__ import annotations

from uuid import UUID

from has_api.application.ports.repositories import DatasetRepository, TestCaseRepository
from has_api.domain.entities import Dataset, TestCase
from has_api.domain.exceptions import NotFoundError


async def create_dataset(
    *,
    workspace_id: UUID,
    name: str,
    description: str | None,
    created_by_id: UUID,
    datasets: DatasetRepository,
) -> Dataset:
    ds = Dataset(
        workspace_id=workspace_id,
        name=name,
        description=description,
        created_by_id=created_by_id,
    )
    return await datasets.save(ds)


async def get_dataset(
    *,
    workspace_id: UUID,
    dataset_id: UUID,
    datasets: DatasetRepository,
) -> Dataset:
    ds = await datasets.get_by_id(workspace_id, dataset_id)
    if ds is None:
        raise NotFoundError("dataset", dataset_id)
    return ds


async def list_datasets(
    *,
    workspace_id: UUID,
    limit: int,
    offset: int,
    datasets: DatasetRepository,
) -> tuple[list[Dataset], int]:
    items = await datasets.list_by_workspace(workspace_id, limit=limit, offset=offset)
    total = await datasets.count_by_workspace(workspace_id)
    return items, total


async def update_dataset(
    *,
    workspace_id: UUID,
    dataset_id: UUID,
    name: str | None,
    description: str | None,
    datasets: DatasetRepository,
) -> Dataset:
    ds = await datasets.get_by_id(workspace_id, dataset_id)
    if ds is None:
        raise NotFoundError("dataset", dataset_id)
    if name is not None:
        ds.name = name
    if description is not None:
        ds.description = description
    return await datasets.save(ds)


async def delete_dataset(
    *,
    workspace_id: UUID,
    dataset_id: UUID,
    datasets: DatasetRepository,
) -> None:
    ds = await datasets.get_by_id(workspace_id, dataset_id)
    if ds is None:
        raise NotFoundError("dataset", dataset_id)
    await datasets.delete(workspace_id, dataset_id)


# ── Test cases ────────────────────────────────────────────────────────────────


async def create_test_case(
    *,
    dataset_id: UUID,
    prompt: str,
    response: str,
    context: str | None,
    ground_truth: str | None,
    external_id: str | None,
    sort_order: int,
    metadata: dict,
    test_cases: TestCaseRepository,
) -> TestCase:
    tc = TestCase(
        dataset_id=dataset_id,
        prompt=prompt,
        response=response,
        context=context,
        ground_truth=ground_truth,
        external_id=external_id,
        sort_order=sort_order,
        metadata=metadata,
    )
    return await test_cases.save(tc)


async def get_test_case(
    *,
    dataset_id: UUID,
    test_case_id: UUID,
    test_cases: TestCaseRepository,
) -> TestCase:
    tc = await test_cases.get_by_id(dataset_id, test_case_id)
    if tc is None:
        raise NotFoundError("test_case", test_case_id)
    return tc


async def list_test_cases(
    *,
    dataset_id: UUID,
    limit: int,
    offset: int,
    test_cases: TestCaseRepository,
) -> tuple[list[TestCase], int]:
    items = await test_cases.list_by_dataset(dataset_id, limit=limit, offset=offset)
    total = await test_cases.count_by_dataset(dataset_id)
    return items, total


async def bulk_create_test_cases(
    *,
    dataset_id: UUID,
    items: list[dict],
    test_cases: TestCaseRepository,
) -> list[TestCase]:
    tcs = [
        TestCase(
            dataset_id=dataset_id,
            prompt=item["prompt"],
            response=item["response"],
            context=item.get("context"),
            ground_truth=item.get("ground_truth"),
            external_id=item.get("external_id"),
            sort_order=item.get("sort_order", i),
            metadata=item.get("metadata", {}),
        )
        for i, item in enumerate(items)
    ]
    return await test_cases.save_many(tcs)


async def update_test_case(
    *,
    dataset_id: UUID,
    test_case_id: UUID,
    updates: dict,
    test_cases: TestCaseRepository,
) -> TestCase:
    tc = await test_cases.get_by_id(dataset_id, test_case_id)
    if tc is None:
        raise NotFoundError("test_case", test_case_id)
    for field, value in updates.items():
        if value is not None:
            setattr(tc, field, value)
    return await test_cases.save(tc)


async def delete_test_case(
    *,
    dataset_id: UUID,
    test_case_id: UUID,
    test_cases: TestCaseRepository,
) -> None:
    tc = await test_cases.get_by_id(dataset_id, test_case_id)
    if tc is None:
        raise NotFoundError("test_case", test_case_id)
    await test_cases.delete(dataset_id, test_case_id)
