"""验证命令处理器"""
import asyncio
import logging
import httpx
import io
import time
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from config import VERIFY_COST, ADMIN_USER_ID
from database_mysql import Database
from one.sheerid_verifier import SheerIDVerifier as OneVerifier
from k12.sheerid_verifier import SheerIDVerifier as K12Verifier
from spotify.sheerid_verifier import SheerIDVerifier as SpotifyVerifier
from youtube.sheerid_verifier import SheerIDVerifier as YouTubeVerifier
from Boltnew.sheerid_verifier import SheerIDVerifier as BoltnewVerifier
from utils.messages import get_insufficient_balance_message, get_verify_usage_message

# 尝试导入并发控制，如果失败则使用空实现
try:
    from utils.concurrency import get_verification_semaphore
except ImportError:
    # 如果导入失败，创建一个简单的实现
    def get_verification_semaphore(verification_type: str):
        return asyncio.Semaphore(3)

logger = logging.getLogger(__name__)


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /verify 命令 - Gemini One Pro"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify", "Gemini One Pro")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = OneVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("无效的 SheerID 链接，请检查后重试。")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("扣除积分失败，请稍后重试。")
        return
    # 本地生成学生信息与学生证 PNG后转发给管理员手动处理（不提交 SheerID）
    try:
        verifier = OneVerifier(verification_id)
        info, img_data = await asyncio.to_thread(verifier.prepare_package)
    except Exception:
        db.add_balance(user_id, VERIFY_COST)
        await update.message.reply_text("❌ 学生信息准备失败，已退回扣除的积分，请稍后重试。")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"📥 新的手动认证提交\n"
            f"服务：Gemini One Pro\n"
            f"用户ID：{user_id}\n"
            f"链接：{url}\n"
            f"姓名：{info['first_name']} {info['last_name']}\n"
            f"学校：{info['school_name']}\n"
            f"生日：{info['birth_date']}\n"
            f"邮箱：{info['email']}\n"
            f"已扣除 {VERIFY_COST} 积分"
        ),
    )
    await context.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=io.BytesIO(img_data),
        filename="student_card.png",
        caption="学生证 PNG - Gemini One Pro",
    )
    await update.message.reply_text("✅ 提交成功！\n\n您的认证链接已转发给管理员手动处理，请耐心等待。")
    return


async def verify2_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /verify2 命令 - ChatGPT Teacher K12"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify2", "ChatGPT Teacher K12")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    verification_id = K12Verifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("无效的 SheerID 链接，请检查后重试。")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("扣除积分失败，请稍后重试。")
        return
    # 本地生成教师信息与教师证明 PNG后转发给管理员手动处理（不提交 SheerID）
    try:
        verifier = K12Verifier(verification_id)
        info, img_data = await asyncio.to_thread(verifier.prepare_package)
    except Exception:
        db.add_balance(user_id, VERIFY_COST)
        await update.message.reply_text("❌ 学生信息准备失败，已退回扣除的积分，请稍后重试。")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"📥 新的手动认证提交\n"
            f"服务：ChatGPT Teacher K12\n"
            f"用户ID：{user_id}\n"
            f"链接：{url}\n"
            f"姓名：{info['first_name']} {info['last_name']}\n"
            f"学校：{info['school_name']}\n"
            f"生日：{info['birth_date']}\n"
            f"邮箱：{info['email']}\n"
            f"已扣除 {VERIFY_COST} 积分"
        ),
    )
    await context.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=io.BytesIO(img_data),
        filename="student_card.png",
        caption="学生证 PNG - ChatGPT Teacher K12",
    )
    await update.message.reply_text("✅ 提交成功！\n\n您的认证链接已转发给管理员手动处理，请耐心等待。")
    return


async def verify3_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /verify3 命令 - Spotify Student"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify3", "Spotify Student")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # 解析 verificationId
    verification_id = SpotifyVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("无效的 SheerID 链接，请检查后重试。")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("扣除积分失败，请稍后重试。")
        return
    # 本地生成学生信息与学生证 PNG 后转发给管理员手动处理（不提交 SheerID）
    try:
        verifier = SpotifyVerifier(verification_id)
        info, img_data = await asyncio.to_thread(verifier.prepare_package)
    except Exception:
        db.add_balance(user_id, VERIFY_COST)
        await update.message.reply_text("❌ 学生信息准备失败，已退回扣除的积分，请稍后重试。")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"📥 新的手动认证提交\n"
            f"服务：Spotify Student\n"
            f"用户ID：{user_id}\n"
            f"链接：{url}\n"
            f"姓名：{info['first_name']} {info['last_name']}\n"
            f"学校：{info['school_name']}\n"
            f"生日：{info['birth_date']}\n"
            f"邮箱：{info['email']}\n"
            f"已扣除 {VERIFY_COST} 积分"
        ),
    )
    await context.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=io.BytesIO(img_data),
        filename="student_card.png",
        caption="学生证 PNG - Spotify Student",
    )
    await update.message.reply_text("✅ 提交成功！\n\n您的认证链接已转发给管理员手动处理，请耐心等待。")
    return


async def verify4_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /verify4 命令 - Bolt.new Teacher（自动获取code版）"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify4", "Bolt.new Teacher")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # 解析 externalUserId 或 verificationId
    external_user_id = BoltnewVerifier.parse_external_user_id(url)
    verification_id = BoltnewVerifier.parse_verification_id(url)

    if not external_user_id and not verification_id:
        await update.message.reply_text("无效的 SheerID 链接，请检查后重试。")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("扣除积分失败，请稍后重试。")
        return
    # 本地生成教师信息与教师 PNG 文档后转发给管理员手动处理（不提交 SheerID）
    try:
        verifier = BoltnewVerifier(url, verification_id=verification_id)
        info, images = await asyncio.to_thread(verifier.prepare_package)
    except Exception:
        db.add_balance(user_id, VERIFY_COST)
        await update.message.reply_text("❌ 学生信息准备失败，已退回扣除的积分，请稍后重试。")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"📥 新的手动认证提交\n"
            f"服务：Bolt.new Teacher\n"
            f"用户ID：{user_id}\n"
            f"链接：{url}\n"
            f"姓名：{info['first_name']} {info['last_name']}\n"
            f"学校：{info['school_name']}\n"
            f"生日：{info['birth_date']}\n"
            f"邮箱：{info['email']}\n"
            f"已扣除 {VERIFY_COST} 积分"
        ),
    )
    for image in images:
        await context.bot.send_photo(
            chat_id=ADMIN_USER_ID,
            photo=io.BytesIO(image),
            filename="student_card.png",
            caption="学生证 PNG - Bolt.new Teacher",
        )
    await update.message.reply_text("✅ 提交成功！\n\n您的认证链接已转发给管理员手动处理，请耐心等待。")
    return


async def _auto_get_reward_code(
    verification_id: str,
    max_wait: int = 20,
    interval: int = 5
) -> Optional[str]:
    """自动获取认证码（轻量级轮询，不影响并发）
    
    Args:
        verification_id: 验证ID
        max_wait: 最大等待时间（秒）
        interval: 轮询间隔（秒）
        
    Returns:
        str: 认证码，如果获取失败返回None
    """
    import time
    start_time = time.time()
    attempts = 0
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            elapsed = int(time.time() - start_time)
            attempts += 1
            
            # 检查是否超时
            if elapsed >= max_wait:
                logger.info(f"自动获取code超时({elapsed}秒)，让用户手动查询")
                return None
            
            try:
                # 查询验证状态
                response = await client.get(
                    f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    current_step = data.get("currentStep")
                    
                    if current_step == "success":
                        # 获取认证码
                        code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
                        if code:
                            logger.info(f"✅ 自动获取code成功: {code} (耗时{elapsed}秒)")
                            return code
                    elif current_step == "error":
                        # 审核失败
                        logger.warning(f"审核失败: {data.get('errorIds', [])}")
                        return None
                    # else: pending，继续等待
                
                # 等待下次轮询
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.warning(f"查询认证码出错: {e}")
                await asyncio.sleep(interval)
    
    return None


async def verify5_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /verify5 命令 - YouTube Student Premium"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    if not context.args:
        await update.message.reply_text(
            get_verify_usage_message("/verify5", "YouTube Student Premium")
        )
        return

    url = context.args[0]
    user = db.get_user(user_id)
    if user["balance"] < VERIFY_COST:
        await update.message.reply_text(
            get_insufficient_balance_message(user["balance"])
        )
        return

    # 解析 verificationId
    verification_id = YouTubeVerifier.parse_verification_id(url)
    if not verification_id:
        await update.message.reply_text("无效的 SheerID 链接，请检查后重试。")
        return

    if not db.deduct_balance(user_id, VERIFY_COST):
        await update.message.reply_text("扣除积分失败，请稍后重试。")
        return
    # 本地生成学生信息与学生证 PNG后转发给管理员手动处理（不提交 SheerID）
    try:
        verifier = YouTubeVerifier(verification_id)
        info, img_data = await asyncio.to_thread(verifier.prepare_package)
    except Exception:
        db.add_balance(user_id, VERIFY_COST)
        await update.message.reply_text("❌ 学生信息准备失败，已退回扣除的积分，请稍后重试。")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"📥 新的手动认证提交\n"
            f"服务：YouTube Student Premium\n"
            f"用户ID：{user_id}\n"
            f"链接：{url}\n"
            f"姓名：{info['first_name']} {info['last_name']}\n"
            f"学校：{info['school_name']}\n"
            f"生日：{info['birth_date']}\n"
            f"邮箱：{info['email']}\n"
            f"已扣除 {VERIFY_COST} 积分"
        ),
    )
    await context.bot.send_photo(
        chat_id=ADMIN_USER_ID,
        photo=io.BytesIO(img_data),
        filename="student_card.png",
        caption="学生证 PNG - YouTube Student Premium",
    )
    await update.message.reply_text("✅ 提交成功！\n\n您的认证链接已转发给管理员手动处理，请耐心等待。")
    return


async def getV4Code_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """处理 /getV4Code 命令 - 获取 Bolt.new Teacher 认证码"""
    user_id = update.effective_user.id

    if db.is_user_blocked(user_id):
        await update.message.reply_text("您已被拉黑，无法使用此功能。")
        return

    if not db.user_exists(user_id):
        await update.message.reply_text("请先使用 /start 注册。")
        return

    # 检查是否提供了 verification_id
    if not context.args:
        await update.message.reply_text(
            "使用方法: /getV4Code <verification_id>\n\n"
            "示例: /getV4Code 6929436b50d7dc18638890d0\n\n"
            "verification_id 在使用 /verify4 命令后会返回给您。"
        )
        return

    verification_id = context.args[0].strip()

    processing_msg = await update.message.reply_text(
        "🔍 正在查询认证码，请稍候..."
    )

    try:
        # 查询 SheerID API 获取认证码
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://my.sheerid.com/rest/v2/verification/{verification_id}"
            )

            if response.status_code != 200:
                await processing_msg.edit_text(
                    f"❌ 查询失败，状态码：{response.status_code}\n\n"
                    "请稍后重试或联系管理员。"
                )
                return

            data = response.json()
            current_step = data.get("currentStep")
            reward_code = data.get("rewardCode") or data.get("rewardData", {}).get("rewardCode")
            redirect_url = data.get("redirectUrl")

            if current_step == "success" and reward_code:
                result_msg = "✅ 认证成功！\n\n"
                result_msg += f"🎉 认证码：`{reward_code}`\n\n"
                if redirect_url:
                    result_msg += f"跳转链接：\n{redirect_url}"
                await processing_msg.edit_text(result_msg)
            elif current_step == "pending":
                await processing_msg.edit_text(
                    "⏳ 认证仍在审核中，请稍后再试。\n\n"
                    "通常需要 1-5 分钟，请耐心等待。"
                )
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                await processing_msg.edit_text(
                    f"❌ 认证失败\n\n"
                    f"错误信息：{', '.join(error_ids) if error_ids else '未知错误'}"
                )
            else:
                await processing_msg.edit_text(
                    f"⚠️ 当前状态：{current_step}\n\n"
                    "认证码尚未生成，请稍后重试。"
                )

    except Exception as e:
        logger.error("获取 Bolt.new 认证码失败: %s", e)
        await processing_msg.edit_text(
            f"❌ 查询过程中出现错误：{str(e)}\n\n"
            "请稍后重试或联系管理员。"
        )
