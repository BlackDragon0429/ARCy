import discord
from discord import app_commands
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# ======================
# 환경변수 로드
# ======================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN 환경변수가 설정되지 않았습니다.")

DATA_FILE = "cw_schedule.json"

# ======================
# 디스코드 기본 설정
# ======================
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
# 봇 준비 완료
# ======================
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ ARC ROAD CW 봇 로그인 완료: {client.user}")

# ======================
# /cw_add
# ======================
@tree.command(name="cw_add", description="CW 일정 추가")
@app_commands.describe(
    date="날짜 (YYYY-MM-DD)",
    time="시간 (HH:MM)",
    memo="메모 (상대 클랜 등)"
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

    await interaction.followup.send(
        f"✅ **CW 일정 등록 완료**\n"
        f"📅 {date} {time}\n"
        f"🛡 {memo}"
    )

# ======================
# /cw_list
# ======================
@tree.command(name="cw_list", description="CW 일정 목록 확인")
async def cw_list(interaction: discord.Interaction):
    await interaction.response.defer()

    data = load_data()
    if not data:
        await interaction.followup.send("📭 등록된 CW 일정이 없습니다.")
        return

    msg = "**📌 ARC ROAD CW 일정**\n"
    for i, cw in enumerate(data, 1):
        msg += f"{i}. {cw['date']} {cw['time']} - {cw['memo']}\n"

    await interaction.followup.send(msg)

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

    await interaction.followup.send(
        f"🗑️ **삭제 완료**\n"
        f"{removed['date']} {removed['time']} - {removed['memo']}"
    )

# ======================
# 실행
# ======================
client.run(TOKEN)
