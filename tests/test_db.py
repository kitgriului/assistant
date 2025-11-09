import pytest
import asyncio
from database.session import init_db, get_session


@pytest.mark.asyncio
async def test_init_db(tmp_path):
    db_path = tmp_path / "test.db"
    url = f"sqlite+aiosqlite:///{db_path}"
    await init_db(url)
    # get_session should now be callable
    sess = get_session()
    assert sess is not None
