import discord
from discord.ext import commands
import json
import os

# إعداد الصلاحيات (Intents)
intents = discord.Intents.default()
intents.members = True
intents.invites = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ملفات حفظ البيانات
DATA_FILE = "invites_data.json"

# دالة لتحميل البيانات من الملف
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"user_invites": {}, "available_keys": ["KEY-ABC123", "KEY-XYZ789", "KEY-DEF456", "KEY-UVW321"]}

# دالة لحفظ البيانات في الملف
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# تحميل البيانات عند بدء التشغيل
data = load_data()
user_invites_count = data["user_invites"]
available_keys = data["available_keys"]

# قاموس مؤقت لتتبع الروابط داخل السيرفر
invites_cache = {}

@bot.event
async def on_ready():
    print(f"=== تم تشغيل البوت بنجاح باسم: {bot.user.name} ===")
    # كاش للروابط عند الإقلاع
    for guild in bot.guilds:
        try:
            invites_cache[guild.id] = await guild.invites()
        except discord.HTTPException:
            print(f"⚠️ تنبيه: لا أملك صلاحية 'Manage Server' في سيرفر: {guild.name}")

@bot.event
async def on_member_join(member):
    guild = member.guild
    global user_invites_count, available_keys
    
    try:
        if guild.id not in invites_cache:
            invites_cache[guild.id] = await guild.invites()
            return

        invites_before = invites_cache[guild.id]
        invites_after = await guild.invites()
        
        inviter_user = None
        
        # مقارنة الروابط لمعرفة أي رابط زاد استخدامه
        for invite in invites_before:
            for new_invite in invites_after:
                if invite.code == new_invite.code and new_invite.uses > invite.uses:
                    inviter_user = invite.inviter
                    break
        
        # تحديث الكاش
        invites_cache[guild.id] = invites_after
        
        if inviter_user and not member.bot:
            user_id = str(inviter_user.id) # تحويل الـ ID إلى نص لملف JSON
            
            # زيادة العداد
            user_invites_count[user_id] = user_invites_count.get(user_id, 0) + 1
            current_count = user_invites_count[user_id]
            
            print(f"👤 {inviter_user.name} دعا عضواً جديداً ({member.name}). المجموع الحالي: {current_count}/5")
            
            # التحقق من الشرط (5 دعوات)
            if current_count >= 5:
                # التحقق إذا كان العضو قد استلم مفتاحاً سابقاً لتجنب التكرار
                if current_count == 5: 
                    if available_keys:
                        key_to_send = available_keys.pop(0) # سحب أول مفتاح
                        try:
                            await inviter_user.send(f"🎉 تهانينا! لقد قمت بدعوة 5 أشخاص بنجاح إلى السيرفر.\n🔑 إليك المفتاح الخاص بك: `{key_to_send}`")
                            print(f"📥 تم إرسال مفتاح بنجاح إلى {inviter_user.name}")
                        except discord.Forbidden:
                            print(f"❌ فشل إرسال رسالة خاصة لـ {inviter_user.name} (الحساب مغلق للرسائل الخاصة).")
                    else:
                        try:
                            await inviter_user.send("🎉 لقد وصلت إلى 5 دعوات، ولكن للأسف نفدت المفاتيح المتاحة حالياً! يرجى مراجعة الإدارة.")
                        except discord.Forbidden:
                            pass
            
            # حفظ التغييرات في الملف فوراً
            save_data({"user_invites": user_invites_count, "available_keys": available_keys})

    except Exception as e:
        print(f"حدث خطأ أثناء معالجة دخول العضو: {e}")

@bot.command()
async def myinvites(ctx):
    """أمر لمعرفة عدد الدعوات الخاصة بك"""
    count = user_invites_count.get(str(ctx.author.id), 0)
    await ctx.send(f"📊 {ctx.author.mention}، عدد دعواتك الحالية هي: **{count}/5**")

# ضع التوكن الذي نسخته من موقع المطورين هنا بين القوسين
bot.run("MTUwODUxNjM3Mjk5MTQ0MzE0NQ.GUI-X9.E5bv7ySUsR6bYQXZLaF41lqxJV-h8Qvf_k9RM8")