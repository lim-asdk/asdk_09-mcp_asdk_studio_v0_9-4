import asyncio
import threading
import logging
import os
import json
from typing import Optional, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client  # [New] SSE Support
from mcp.types import Tool

logger = logging.getLogger("LimChat.MCP")

class McpClientHandler:
    """
    [L1 Infrastructure Layer]
    역할: 외부 MCP 서버 프로세스와의 통신(Stdio/HTTP/SSE)을 관리합니다.
    비동기 통신을 담당하며, 세션 유지 및 도구 목록 조회를 수행합니다.
    """
    def __init__(self, name, server_config, project_root):
        self.name = name
        self.server_config = server_config
        self.project_root = project_root
        self.session: Optional[ClientSession] = None
        self.tools: List[Tool] = []
        self._loop = None
        self._thread = None
        self.status = "stopped"
        self.error_msg = ""
        self._stop_event = asyncio.Event()
        self._last_connect_ts = 0.0

        retry_cfg = server_config.get("retry", {}) if isinstance(server_config, dict) else {}
        self._max_retries = int(retry_cfg.get("max_retries", 0))  # 0 = infinite
        self._base_delay = float(retry_cfg.get("base_delay", 2.0))
        self._max_delay = float(retry_cfg.get("max_delay", 30.0))
        self._list_tools_retries = int(retry_cfg.get("list_tools_retries", 2))
        self._list_tools_delay = float(retry_cfg.get("list_tools_delay", 2.0))
        self._init_timeout = float(retry_cfg.get("init_timeout", 90.0))
        self._tools_timeout = float(retry_cfg.get("tools_timeout", 90.0))

    def start(self):
        self.status = "connecting"
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """서버 연결을 종료합니다."""
        self.status = "stopped"
        if self._loop:
            # 루프에 종료 시그널 전달
            self._loop.call_soon_threadsafe(self._stop_event.set)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    async def _connect(self):
        transport_type = self.server_config.get("transport", "stdio").lower()
        attempt = 0
        delay = self._base_delay

        while not self._stop_event.is_set():
            try:
                self.status = "connecting"
                self.error_msg = ""
                if transport_type == "stdio":
                    await self._connect_stdio()
                elif transport_type in ["sse", "http"]:
                    await self._connect_sse()
                else:
                    raise ValueError(f"Unknown transport type: {transport_type}")

                if self._stop_event.is_set():
                    break

                # If session ended without stop, treat as error and retry.
                self.status = "error"
                self.error_msg = "Disconnected (session ended)"
                logger.warning(f"[{self.name}] Session ended, will retry.")
            except Exception as e:
                self.status = "error"
                self.error_msg = str(e)
                logger.error(f"[{self.name}] Connection Failed: {e}")

            attempt += 1
            if self._max_retries > 0 and attempt > self._max_retries:
                logger.error(f"[{self.name}] Max retries reached, giving up.")
                break

            await asyncio.sleep(delay)
            delay = min(self._max_delay, delay * 2)

    async def _connect_stdio(self):
        """기존의 로컬 프로세스 실행 방식"""
        cmd = self.server_config.get("command", "python")
        args = self.server_config.get("args", [])
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env.update(self.server_config.get("env", {}))

        resolved_args = []
        for arg in args:
            if arg.endswith(".py") and not os.path.isabs(arg):
                abs_path = os.path.join(self.project_root, arg)
                resolved_args.append(abs_path if os.path.exists(abs_path) else arg)
            else:
                resolved_args.append(arg)
        
        # [Auto-CWD] 실행 스크립트(.py)가 있는 디렉토리를 작업 디렉토리로 설정 (Optional)
        cwd = None
        for arg in resolved_args:
            if arg.endswith(".py") and os.path.exists(arg):
                cwd = os.path.dirname(arg)
                break
        
        # PYTHONPATH 보정
        if cwd:
            env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")

        server_params = StdioServerParameters(command=cmd, args=resolved_args, env=env)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await self._manage_session(session)

    async def _connect_sse(self):
        """[New] URL 기반 원격 접속 방식 (HTTP/SSE)"""
        url = self.server_config.get("url")
        headers = self.server_config.get("headers", {})
        
        if not url:
            raise ValueError("URL is required for SSE transport")

        async with sse_client(url=url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await self._manage_session(session)

    async def _manage_session(self, session):
        """세션 초기화 및 유지 공통 로직"""
        self.session = session
        try:
            # 초기화 타임아웃 (기본 90초)
            await asyncio.wait_for(session.initialize(), timeout=self._init_timeout)

            # 도구 목록 조회 재시도
            last_error = None
            for i in range(self._list_tools_retries + 1):
                try:
                    result = await asyncio.wait_for(session.list_tools(), timeout=self._tools_timeout)
                    self.tools = result.tools
                    last_error = None
                    break
                except Exception as e:
                    last_error = e
                    if i < self._list_tools_retries:
                        await asyncio.sleep(self._list_tools_delay)
            if last_error:
                raise last_error
            
            self.status = "connected"
            self.error_msg = ""
            logger.info(f"[{self.name}] Connect Success. Tools: {len(self.tools)}")
        except asyncio.TimeoutError:
            self.status = "error"
            self.error_msg = "Connection timeout (Check if server has 'print' statements interfering with JSON)"
            logger.error(f"[{self.name}] {self.error_msg}")
            return
        except Exception as e:
            self.status = "error"
            self.error_msg = str(e)
            logger.error(f"[{self.name}] Session Init Failed: {e}")
            return
        
        # 연결 유지를 위해 대기 (종료 시그널이 올 때까지)
        await self._stop_event.wait()

    def call_tool_sync(self, name: str, arguments: dict):
        if not self.session or not self._loop:
            raise Exception("Session not connected")
        
        future = asyncio.run_coroutine_threadsafe(
            self.session.call_tool(name, arguments), 
            self._loop
        )
        try:
            result = future.result(timeout=60)
            texts = [c.text for c in result.content if c.type == 'text']
            full_text = "\n".join(texts)
            try:
                return json.loads(full_text)
            except:
                return {"raw_text": full_text}
        except Exception as e:
            raise e
