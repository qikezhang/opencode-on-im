import base64
import json
import re
from typing import TYPE_CHECKING

import structlog
from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

if TYPE_CHECKING:
    from opencode_on_im.adapters.telegram.bot import TelegramAdapter

logger = structlog.get_logger()


def _mask_proxy_url(url: str) -> str:
    return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", url)


def _validate_proxy_url(url: str) -> bool:
    valid_schemes = ("http://", "https://", "socks5://", "socks4://")
    return any(url.startswith(s) for s in valid_schemes)


def setup_handlers(dp: Dispatcher, adapter: "TelegramAdapter") -> None:
    @dp.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        user_id = str(message.from_user.id) if message.from_user else ""

        instances = await adapter.session_manager.get_user_instances("telegram", user_id)

        if instances:
            await message.answer(
                "欢迎回来\\! 你已绑定的实例:\n"
                + "\n".join(f"• `{i}`" for i in instances)
                + "\n\n使用 /help 查看命令列表"
            )
        else:
            await message.answer(
                "欢迎使用 OpenCode\\-on\\-IM\\!\n\n"
                "请扫描 OpenCode 实例生成的二维码进行绑定\\。\n"
                "或者发送二维码内容进行绑定\\。"
            )

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        help_text = """
*命令列表*

/start \\- 开始使用
/help \\- 显示帮助
/status \\- 当前实例状态
/list \\- 列出所有绑定实例
/switch \\<name\\> \\- 切换活跃实例
/rename \\<new\\> \\- 重命名当前实例
/unbind \\<name\\> \\- 解绑实例
/reset\\-qr \\- 重新生成二维码
/web \\- 获取 Web Terminal 链接
/sessions \\- 列出 OpenCode 会话
/cancel \\- 取消当前任务
/proxy \\- 查看/设置代理配置
"""
        await message.answer(help_text)

    @dp.message(Command("status"))
    async def cmd_status(message: Message) -> None:
        user_id = str(message.from_user.id) if message.from_user else ""
        instances = await adapter.session_manager.get_user_instances("telegram", user_id)

        if not instances:
            await message.answer("未绑定任何实例\\。请先扫描二维码绑定\\。")
            return

        status_lines = ["*实例状态*\n"]
        for instance_id in instances:
            instance = adapter.instance_registry.get_instance(instance_id)
            if instance:
                online_status = adapter.notification_router.format_online_status(
                    instance_id, exclude_user=("telegram", user_id)
                )
                status_lines.append(f"📦 `{instance.name}`")
                if online_status:
                    status_lines.append(f"   {online_status}")

        await message.answer("\n".join(status_lines))

    @dp.message(Command("list"))
    async def cmd_list(message: Message) -> None:
        user_id = str(message.from_user.id) if message.from_user else ""
        instances = await adapter.session_manager.get_user_instances("telegram", user_id)

        if not instances:
            await message.answer("未绑定任何实例\\。")
            return

        lines = ["*已绑定实例*\n"]
        for instance_id in instances:
            instance = adapter.instance_registry.get_instance(instance_id)
            if instance:
                lines.append(f"• `{instance.name}` \\({instance_id[:8]}\\)")

        await message.answer("\n".join(lines))

    @dp.message(Command("switch"))
    async def cmd_switch(message: Message) -> None:
        if not message.text:
            return

        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.answer("用法: /switch \\<instance\\-name\\>")
            return

        instance_name = parts[1]
        instance = adapter.instance_registry.get_instance_by_name(instance_name)

        if not instance:
            await message.answer(f"实例 `{instance_name}` 不存在")
            return

        await message.answer(f"已切换到实例: `{instance_name}`")

    @dp.message(Command("web"))
    async def cmd_web(message: Message) -> None:
        port = adapter.settings.web_terminal_port
        terminal_type = adapter.settings.web_terminal

        await adapter.send_card(
            str(message.from_user.id) if message.from_user else "",
            "Web Terminal",
            f"类型: {terminal_type}\n端口: {port}",
            [{"text": "打开终端", "url": f"http://localhost:{port}"}],
        )

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message) -> None:
        await message.answer("已发送取消请求")

    @dp.message(Command("proxy"))
    async def cmd_proxy(message: Message) -> None:
        if not message.text:
            return

        parts = message.text.split(maxsplit=2)

        if len(parts) == 1:
            proxy = adapter.settings.proxy
            if proxy.enabled and proxy.url:
                masked_url = _mask_proxy_url(proxy.url)
                await message.answer(f"*代理状态*\n\n已启用: ✅\nURL: `{masked_url}`")
            else:
                await message.answer(
                    "*代理状态*\n\n已启用: ❌\n\n使用 `/proxy set \u003curl\u003e` 设置代理"
                )
            return

        action = parts[1].lower()

        if action == "off" or action == "disable":
            adapter.settings.proxy.enabled = False
            await message.answer("✅ 代理已禁用")
        elif action == "on" or action == "enable":
            if not adapter.settings.proxy.url:
                await message.answer("❌ 请先使用 `/proxy set \u003curl\u003e` 设置代理 URL")
                return
            adapter.settings.proxy.enabled = True
            await message.answer("✅ 代理已启用")
        elif action == "set" and len(parts) == 3:
            proxy_url = parts[2]
            if not _validate_proxy_url(proxy_url):
                await message.answer("❌ 无效的代理 URL\\. 格式: `socks5://user:pass@host:port`")
                return
            adapter.settings.proxy.url = proxy_url
            adapter.settings.proxy.enabled = True
            await message.answer(f"✅ 代理已设置: `{_mask_proxy_url(proxy_url)}`")
        else:
            await message.answer(
                "*代理命令*\n\n"
                "`/proxy` \\- 查看当前状态\n"
                "`/proxy set \u003curl\u003e` \\- 设置代理\n"
                "`/proxy on` \\- 启用代理\n"
                "`/proxy off` \\- 禁用代理"
            )

    @dp.message(F.text)
    async def handle_text(message: Message) -> None:
        if not message.text or not message.from_user:
            return

        user_id = str(message.from_user.id)
        text = message.text

        if text.startswith("eyJ"):
            try:
                qr_data = json.loads(base64.urlsafe_b64decode(text))
                instance_id = qr_data.get("instance_id")
                connect_secret = qr_data.get("connect_secret")

                if adapter.instance_registry.verify_connect_secret(instance_id, connect_secret):
                    await adapter.session_manager.bind_user("telegram", user_id, instance_id)
                    instance = adapter.instance_registry.get_instance(instance_id)
                    adapter.notification_router.register_online(instance_id, "telegram", user_id)

                    await message.answer(
                        f"绑定成功\\! 实例: `{instance.name if instance else instance_id}`"
                    )
                else:
                    await message.answer("二维码无效或已过期")
            except Exception as e:
                logger.error("qr_bind_failed", error=str(e))
                await message.answer("绑定失败，请检查二维码")
            return

        instances = await adapter.session_manager.get_user_instances("telegram", user_id)
        if not instances:
            await message.answer("请先绑定实例后再发送消息")
            return

        await adapter.session_manager.update_last_active("telegram", user_id)

        instance_id = instances[-1]
        instance = adapter.instance_registry.get_instance(instance_id)
        if not instance:
            await message.answer("实例不存在或已被删除，请重新绑定")
            return

        session_id = instance.opencode_session_id
        if not session_id:
            session = await adapter.opencode_client.create_session(
                title=f"Telegram:{instance.name}"
            )
            session_id = str(session.get("id"))
            instance.opencode_session_id = session_id
            adapter.instance_registry._save()

        response = await adapter.opencode_client.send_message(session_id=session_id, text=text)

        parts = response.get("parts", [])
        assistant_text = ""
        if isinstance(parts, list) and parts:
            assistant_text = str(parts[0].get("text", ""))

        await message.answer(assistant_text or "(no response)")

    @dp.message(F.voice)
    async def handle_voice(message: Message) -> None:
        if not message.voice or not message.from_user:
            return

        await message.answer("语音消息将直接转发给 OpenCode\\. \\(待实现\\)")
