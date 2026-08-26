import asyncio
from backend.data.realtime_provider import realtime_provider_manager
from backend.data.providers.coinbase_ws_provider import CoinbaseWSProvider

def test_coinbase_ws_provider_lifecycle():
    async def _run():
        provider = CoinbaseWSProvider()
        
        # 1. First start
        await provider.start()
        assert provider._running is True
        assert provider._started is True
        first_task = provider._task
        assert first_task is not None
        
        # 2. Duplicate start (must be idempotent & non-duplicating)
        await provider.start()
        assert provider._task == first_task
        
        # 3. Restart
        await provider.restart()
        assert provider._running is True
        assert provider._started is True
        assert provider._task is not None
        
        # 4. Stop
        await provider.stop()
        assert provider._running is False
        assert provider._started is False
        assert provider._task is None

    asyncio.run(_run())

def test_realtime_provider_manager_lifecycle():
    async def _run():
        # 1. Start manager
        await realtime_provider_manager.start()
        assert realtime_provider_manager._running is True
        
        # 2. Duplicate start (idempotent)
        await realtime_provider_manager.start()
        assert realtime_provider_manager._running is True
        
        # 3. Restart
        await realtime_provider_manager.restart()
        assert realtime_provider_manager._running is True
        
        # 4. Stop
        await realtime_provider_manager.stop()
        assert realtime_provider_manager._running is False

    asyncio.run(_run())
