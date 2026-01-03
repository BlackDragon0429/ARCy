import discord
from discord import app_commands
from discord.ext import tasks
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# ======================
# 환경변수 로드
# ======================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")

DATA_FILE = "cw_schedule.json"

# ======================
# 시간대 설정 (KST)
# ======================
KST = timezone(timedelta(hours=9))

# ======================
# 디스코드 기본 설정
# ======================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ======================
# 알림 채널 설정
# ======================
ALERT_CHANNEL_ID = 1439182392798613527  # CW 알림 채널 ID
sent_alerts = set()

# ======================
# 데이터 처리
# ======================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ======================
# CW 자동 알림 (30분 / 10분 전)
# ======================
@tasks.loop(minutes=1)
async def cw_alert_task():
    now = datetime.now(KST)
    data = load_data()

    channel = client.get_channel(ALERT_CHANNEL_ID)
    if channel is None:
        return

    for cw in data:
        try:
            cw_time = datetime.strptime(
                f"{cw['date']} {cw['time']}",
                "%Y-%m-%d %H:%M"
            ).replace(tzinfo=KST)
        except:
            continue

        for minutes_before in (30, 10):
            alert_time = cw_time - timedelta(minutes=minutes_before)
            alert_key = f"{cw['date']}-{cw['time']}-{minutes_before}"

            if (
                alert_time <= now < alert_time + timedelta(minutes=1)
                and alert_key not in sent_alerts
            ):
                embed = discord.Embed(
                    title="🚨 ARC ROAD CW 알림 🚨",
                    color=0xE74C3C,
                    timestamp=now
                )
                embed.add_field(
                    name="⏰ 시작까지",
                    value=f"{minutes_before}분 남았습니다",
                    inline=False
                )
                embed.add_field(
                    name="📅 일정",
                    value=f"{cw['date']} {cw['time']}",
                    inline=True
                )
                embed.add_field(
                    name="🛡 상대 클랜",
                    value=cw["memo"],
                    inline=True
                )
                embed.set_footer(text="ARC ROAD RIVALS")

                await channel.send(content="@here", embed=embed)
                sent_alerts.add(alert_key)

# ======================
# 봇 준비 완료
# ======================
@client.event
async def on_ready():
    await tree.sync()
    if not cw_alert_task.is_running():
        cw_alert_task.start()
    print(f"✅ ARC ROAD CW 봇 로그인 완료: {client.user}")

# ======================
# /cw_add
# ======================
@tree.command(name="cw_add", description="CW 일정 추가")
@app_commands.describe(
    date="날짜 (YYYY-MM-DD)",
    time="시간 (HH:MM)",
    memo="상대 클랜"
)
async def cw_add(interaction: discord.Interaction, date: str, time: str, memo: str):
    await interaction.response.defer(ephemeral=True)

    data = load_data()
    data.append({
        "date": date,
        "time": time,
        "memo": memo
    })
    save_data(data)

    embed = discord.Embed(
        title="✅ CW 일정 등록 완료",
        color=0x2ECC71
    )
    embed.add_field(name="📅 일정", value=f"{date} {time}", inline=False)
    embed.add_field(name="🛡 상대 클랜", value=memo, inline=False)

    await interaction.followup.send(embed=embed)

# ======================
# /cw_list
# ======================
@tree.command(name="cw_list", description="CW 일정 목록")
async def cw_list(interaction: discord.Interaction):
    await interaction.response.defer()

    data = load_data()
    if not data:
        await interaction.followup.send("📭 등록된 CW 일정이 없습니다.")
        return

    embed = discord.Embed(
        title="📌 ARC ROAD CW 일정",
        color=0x3498DB
    )

    for i, cw in enumerate(data, 1):
        embed.add_field(
            name=f"{i}. {cw['date']} {cw['time']}",
            value=f"🛡 {cw['memo']}",
            inline=False
        )

    await interaction.followup.send(embed=embed)

# ======================
# /cw_remove
# ======================
@tree.command(name="cw_remove", description="CW 일정 삭제")
@app_commands.describe(index="삭제할 일정 번호")
async def cw_remove(interaction: discord.Interaction, index: int):
    await interaction.response.defer(ephemeral=True)

    data = load_data()
    if index < 1 or index > len(data):
        await interaction.followup.send("❌ 잘못된 번호입니다.")
        return

    removed = data.pop(index - 1)
    save_data(data)

    embed = discord.Embed(
        title="🗑️ CW 일정 삭제 완료",
        color=0x95A5A6
    )
    embed.add_field(
        name="삭제된 일정",
        value=f"{removed['date']} {removed['time']} - {removed['memo']}",
        inline=False
    )

    await interaction.followup.send(embed=embed)

# ======================
# 실행
# ======================
client.run(TOKEN)
