Telegram 消息无痕搬运/偷鸡机器人 (Docker版)这是一个基于 Python Telethon 库开发的 Telegram 消息自动转发系统。本项目结合了 Userbot (用户客户端) 和 Bot API (机器人客户端) 的优势，实现了从任意频道/群组（包括机器人无法加入的频道）监听消息，并以**“无痕模式”**（去除“转发自 xxx”标签）转发到您的目标频道。✨ 核心功能🕵️ 全能监听 (Userbot)：使用真实用户账号监听，能够监控任何您已加入的公开/私密频道或群组，突破普通机器人无法加入频道的限制。👻 无痕转发 (Stealth Mode)：通过机器人“复制粘贴”的方式发送消息，彻底去除原消息的“Forwarded from”来源标签，伪装成机器人原创发布。📦 完美支持相册 (Media Group)：内置缓存与锁机制，能够自动识别并合并多张图片/视频为一条相册消息，避免刷屏或顺序错乱。🛡️ 智能命令过滤：自动拦截管理命令（如 /add_listen），防止命令泄露到公开频道。自动拦截系统提示语（如“用法：...”），确保频道内容纯净。📢 多路分发：支持同时监听多个源频道，并将消息汇总转发到配置的一个或多个目标频道。🐳 Docker 部署：提供完整的 Docker Compose 配置，一键部署，稳定运行，支持掉线自动重启。🛠️ 架构原理本项目由两个并在的 Docker 容器服务组成：Userbot (telegram_bot.py)：扮演“搬运工”。使用您的个人账号登录。监听 config.json 中配置的源频道。将收到的新消息转发给中间机器人（RelayBot）。只在“收藏夹”或与机器人私聊中响应管理命令。RelayBot (bot_relay.py)：扮演“发布者”。使用机器人 Token 登录。接收来自 Userbot 的私聊消息。处理相册缓存、过滤系统命令。使用 send_message (而非 forward) 将内容发送到最终的目标频道。🚀 部署指南1. 环境准备一台安装了 Linux (如 Debian/Ubuntu) 的 VPS。已安装 Docker 和 Docker Compose。API ID & API Hash：从 my.telegram.org 获取。Bot Token：从 @BotFather 申请一个新的机器人。目标频道：创建一个频道，并将您的机器人添加为管理员（给予发布消息权限）。2. 获取代码将本项目下载或 Clone 到您的服务器：Bashmkdir toujibot
cd toujibot
# 将本项目的代码文件上传至此目录
3. 配置文件修改 config.json (Userbot 配置)负责定义监听规则和 Userbot 登录信息。JSON{
    "api_id": 12345678,                  // 您的 API ID
    "api_hash": "abcdefg123456...",      // 您的 API Hash
    "master_account_id": 123456789,      // 您的个人账号 ID (用于权限控制)
    "bot_mappings": [
        {
            "source_chat": -100123456789, // 源频道 ID (您想偷的频道)
            "target_bot": "@your_bot_username" // 您的中间机器人用户名
        }
    ],
    "proxy": null                        // VPS通常不需要代理，设为 null
}
修改 bot_relay.py (RelayBot 配置)负责定义最终发送的目标频道。打开 bot_relay.py，修改顶部的配置区域：Python# === 配置区域 ===
API_ID = 12345678                # 与 config.json 保持一致
API_HASH = 'abcdefg123456...'    # 与 config.json 保持一致
BOT_TOKEN = '123456:ABC-...'     # 您的机器人 Token

# 【重要】最终转发到的目标频道 ID 列表
# 机器人必须是这些频道的管理员！
DEST_CHANNELS = [-100987654321, -100555666777] 
4. 首次登录 (生成 Session)Userbot 首次运行需要交互式输入手机号和验证码。运行临时容器：Bashdocker compose run --rm userbot
按照提示输入：手机号（格式如 +8613800000000）验证码（Telegram App 收到的 5 位数）2FA 密码（如果开启了）登录成功后，看到“客户端已启动”提示，按 Ctrl + C 退出。此时目录下会生成 anon.session 文件。5. 正式启动后台运行所有服务：Bashdocker compose up -d
查看运行日志：Bashdocker compose logs -f
🎮 使用命令您可以在 Telegram 的 “收藏夹” (Saved Messages) 或 直接私聊您的机器人 发送以下命令来动态管理监听列表。命令说明示例/add_listen添加监听任务/add_listen -100123456 @mybot/remove_listen移除监听任务/remove_listen -100123456/list_listen查看当前监听列表/list_listen/joinUserbot 加入频道/join https://t.me/xxchannel/leaveUserbot 退出频道/leave @xxchannel注意：得益于内置的过滤机制，您在机器人私聊中发送的这些命令以及机器人的回复，都不会被转发到目标频道。📂 项目结构Plaintext.
├── bot_relay.py        # 机器人端脚本 (处理接收、缓存、无痕发送)
├── telegram_bot.py     # 用户端脚本 (处理监听、转发给机器人、命令响应)
├── config.json         # 用户端配置文件
├── requirements.txt    # Python 依赖
├── docker-compose.yml  # Docker 编排文件
├── Dockerfile          # 镜像构建文件
└── anon.session        # (自动生成) Userbot 登录凭证
⚠️ 免责声明本项目仅供技术研究和学习使用。请勿使用本项目进行侵犯版权、骚扰或违反 Telegram 服务条款的行为。使用者需自行承担使用本项目可能带来的任何法律风险。⭐ 如果觉得有用，请给个 Star！
