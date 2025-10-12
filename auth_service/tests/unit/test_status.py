import pytest

@pytest.mark.asyncio
async def test_dummy_async():
    """
    Verifica que las pruebas asíncronas funcionen correctamente.
    """
    async def add(a, b):
        return a + b

    result = await add(2, 3)
    assert result == 5