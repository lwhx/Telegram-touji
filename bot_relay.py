import asyncio
import logging

from telethon import TelegramClient, events

from common_config import ConfigManager, load_relay_settings
from delivery import AsyncRateLimiter, with_retry, write_dlq
from structured_logger import get_logger, log_event

logger = get_logger("relaybot")
config_manager = ConfigManager()
settings = load_relay_settings(config_manager)

media_group_cache = {}
media_group_lock = asyncio.Lock()
rate_limiter = AsyncRateLimiter(rate_per_sec=8)
DLQ_PATH = "logs/relay_dlq.jsonl"

client = TelegramClient("bot_session", settings["api_id"], settings["api_hash"]).start(bot_token=settings["bot_token"])


def current_dest_channels() -> list[int]:
    global settings
    if config_manager.reload_if_changed():
        settings = load_relay_settings(config_manager)
        log_event(logger, logging.INFO, "config_hot_reloaded", dest_channels=settings["dest_channels"])
    return settings["dest_channels"]


@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handler(event):
    sender = await event.get_sender()
    if sender and sender.is_self:
        return

    stripped_text = (event.raw_text or "").strip()
    if stripped_text.startswith("/"):
        log_event(logger, logging.INFO, "command_blocked", text=stripped_text)
        return
    if stripped_text.startswith("🤖"):
        log_event(logger, logging.INFO, "system_reply_blocked", text=stripped_text)
        return

    if event.message.grouped_id:
        async with media_group_lock:
            gid = event.message.grouped_id
            if gid not in media_group_cache:
                media_group_cache[gid] = {"messages": [], "task": None}
            media_group_cache[gid]["messages"].append(event.message)
            if media_group_cache[gid]["task"]:
                media_group_cache[gid]["task"].cancel()
            media_group_cache[gid]["task"] = asyncio.create_task(process_media_group(gid))
        log_event(logger, logging.INFO, "album_cached", group_id=event.message.grouped_id)
    else:
        await send_copy(event.message)


async def process_media_group(gid: int):
    try:
        await asyncio.sleep(2)
        async with media_group_lock:
            if gid not in media_group_cache:
                return
            msgs = media_group_cache[gid]["messages"]
            del media_group_cache[gid]

        msgs.sort(key=lambda x: x.id)
        media = [m.media for m in msgs]
        caption = next((m.text for m in msgs if m.text), None)

        for cid in current_dest_channels():
            await rate_limiter.wait()
            try:
                await with_retry(
                    lambda: client.send_message(cid, message=caption, file=media),
                    retries=3,
                    base_delay=1,
                    logger=logger,
                    action="send_album",
                )
                log_event(logger, logging.INFO, "album_sent", channel_id=cid, group_id=gid)
            except Exception as exc:  # noqa: BLE001
                payload = {"channel_id": cid, "group_id": gid, "error": str(exc)}
                write_dlq(DLQ_PATH, payload)
                log_event(logger, logging.ERROR, "album_send_failed", **payload)
    except asyncio.CancelledError:
        return


async def send_copy(msg):
    for cid in current_dest_channels():
        await rate_limiter.wait()
        try:
            await with_retry(
                lambda: client.send_message(cid, message=msg, file=msg.media),
                retries=3,
                base_delay=1,
                logger=logger,
                action="send_message",
            )
            log_event(logger, logging.INFO, "message_sent", channel_id=cid, message_id=msg.id)
        except Exception as exc:  # noqa: BLE001
            payload = {"channel_id": cid, "message_id": msg.id, "error": str(exc)}
            write_dlq(DLQ_PATH, payload)
            log_event(logger, logging.ERROR, "message_send_failed", **payload)


log_event(logger, logging.INFO, "relaybot_started", dest_channels=settings["dest_channels"])
client.run_until_disconnected()
