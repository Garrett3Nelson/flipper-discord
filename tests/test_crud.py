import pytest
import pytest_asyncio
import asyncio
import sys

from sqlalchemy.exc import IntegrityError

from sql.database import async_session, engine, Base
from sql import models, schemas, crud


# With a fresh database, run these two commands before pytest will work.
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_data():
    item = schemas.ItemCreate(id=2, name="Cannonball", market=1000, limit=5000, members=True, high_alch=10, low_alch=5)
    cat = schemas.CategoryCreate(name='Test', item_id=2)
    async with async_session() as session:
        await crud.create_item(session, item)
        await crud.create_category(session, cat)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    if sys.platform.startswith("win") and sys.version_info[:2] >= (3, 8):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
        # https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='module')
async def db_session():
    db = async_session()
    yield db


@pytest.mark.asyncio
class TestDB:
    @pytest.mark.xfail(raises=IntegrityError)
    async def test_create_item_fail(self, db_session):
        item = schemas.ItemCreate(id=2, name="Cannonball", market=1000, limit=5000, members=True, high_alch=10, low_alch=5)
        db = db_session

        async with db as session:
            await crud.create_item(session, item)

    async def test_create_item(self, db_session):
        item = schemas.ItemCreate(id=1, name="Test Cannonball", market=1000, limit=5000, members=True, high_alch=10, low_alch=5)
        db = db_session

        async with db as session:
            await crud.delete_item(db, item.id)
            result = await crud.create_item(session, item)

        assert isinstance(result, models.Items), "result is not an Item type"
        assert result.id == 1, "Correct ID was not returned in query"

        async with db as session:
            await crud.delete_item(session, result.id)

    async def test_create_category(self, db_session):
        cat = schemas.CategoryCreate(name='PyTest', item_id=2)
        db = db_session
        async with db as session:
            result = await crud.create_category(session, cat)

        assert isinstance(result, models.Category), "result is not a Category type"
        assert result.name == 'PyTest', 'Incorrect category name'

        async with db as session:
            await crud.delete_item(session, result.id)

    async def test_get_item(self, db_session):
        db = db_session
        async with db as session:
            result = await crud.get_item(session, item_id=2)

        assert isinstance(result, models.Items), "result is not an Item type"
        assert result.id == 2, "Correct ID was not returned in query"

    async def test_get_category(self, db_session):
        db = db_session
        async with db as session:
            result = await crud.get_category(session, cat_id=1)

        assert isinstance(result, models.Category), "result is not a Category type"
        assert result.name == "Test", "Correct name was not returned in query"
