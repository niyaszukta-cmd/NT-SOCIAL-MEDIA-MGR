import streamlit as st
import os
import json
import base64
from datetime import datetime
from groq import Groq

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NYZTrade Viral Content Generator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }

    /* Header banner */
    .nyz-header {
        background: linear-gradient(135deg, #0f2744 0%, #185FA5 100%);
        border-radius: 12px;
        padding: 1.2rem 1.8rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .nyz-header h1 { color: #E6F1FB; font-size: 1.4rem; margin: 0; }
    .nyz-header p  { color: #85B7EB; font-size: 0.85rem; margin: 0; }

    /* Section cards */
    .section-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }

    /* Tag pills */
    .tag-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin: 3px;
        font-weight: 500;
    }
    .tag-high { background: #0c447c22; color: #85B7EB; border: 1px solid #185FA5; }
    .tag-med  { background: #41240222; color: #EF9F27; border: 1px solid #BA7517; }
    .tag-low  { background: #2a2a3a;   color: #888780; border: 1px solid #444441; }

    /* Title cards */
    .title-card {
        background: #12122a;
        border: 1px solid #2a2a4a;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Score badge */
    .score-badge {
        background: #0f6e5622;
        color: #5DCAA5;
        border: 1px solid #1D9E75;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 11px;
        white-space: nowrap;
        margin-left: 10px;
    }

    /* Platform pill */
    .platform-active {
        background: #185FA5;
        color: #E6F1FB;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
        margin: 2px;
    }

    /* Char counter */
    .char-count { font-size: 11px; color: #888; text-align: right; margin-top: 4px; }
    .char-ok    { color: #5DCAA5; }
    .char-warn  { color: #EF9F27; }
    .char-over  { color: #E24B4A; }

    /* Output section title */
    .out-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin-bottom: 8px;
        font-weight: 600;
    }

    /* Malayalam badge */
    .ml-badge {
        background: #26215c22;
        color: #AFA9EC;
        border: 1px solid #534AB7;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
        margin-left: 8px;
    }

    /* Hide Streamlit default elements */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }
    div[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nyz-header">
    <div style="font-size:2rem">📈</div>
    <div>
        <h1>NYZTrade — Viral Content Generator</h1>
        <p>AI-powered titles, tags, descriptions & hashtags for your trading content</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar — API key ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    groq_key = st.text_input(
        "Groq API Key",
        value=os.environ.get("GROQ_API_KEY", ""),
        type="password",
        help="Get free key at console.groq.com"
    )
    st.markdown("---")
    st.markdown("**Model**")
    model_choice = st.selectbox(
        "Groq model",
        ["llama-3.3-70b-versatile", "llama3-8b-8192", "mixtral-8x7b-32768"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Brand defaults**")
    brand_name   = st.text_input("Channel / Brand", value="NYZTrade")
    brand_url    = st.text_input("Website", value="nyztrade.in")
    brand_handle = st.text_input("YouTube handle", value="@NYZTrade")
    st.markdown("---")
    st.markdown("**History**")
    if "history" not in st.session_state:
        st.session_state.history = []
    if st.session_state.history:
        st.caption(f"{len(st.session_state.history)} generated so far")
        if st.button("🗑️ Clear history"):
            st.session_state.history = []
            st.rerun()

# ── Main layout — two columns ─────────────────────────────────────────────────
col_in, col_out = st.columns([1, 1], gap="large")

# ════════════════════════════════════════════════
# INPUT COLUMN
# ════════════════════════════════════════════════
with col_in:
    st.markdown("#### 📥 Content input")

    # Thumbnail upload
    thumb_file = st.file_uploader(
        "Upload thumbnail / image (optional — AI will analyse it)",
        type=["png", "jpg", "jpeg", "webp"],
        help="Upload your video thumbnail for AI-powered topic detection"
    )
    if thumb_file:
        st.image(thumb_file, use_column_width=True, caption="Thumbnail preview")

    st.markdown("---")

    # Topic & details
    topic = st.text_input(
        "Video topic / keyword *",
        placeholder="e.g. Nifty GEX analysis Monday expiry prediction",
        help="Main topic of your video"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        niche = st.selectbox("Niche", [
            "Stock market / Nifty analysis",
            "Options trading",
            "GEX / VANNA / DEX analytics",
            "Bank Nifty analysis",
            "Personal finance / investing",
            "Algo trading / Pine Script",
            "IPO / Fundamental analysis",
            "Crypto / global markets",
        ])
    with col_b:
        language = st.selectbox("Output language", [
            "English",
            "Malayalam (മലയാളം)",
            "Both English + Malayalam",
        ])

    col_c, col_d = st.columns(2)
    with col_c:
        audience = st.selectbox("Target audience", [
            "All retail traders",
            "Beginners / newcomers",
            "Intermediate traders",
            "Advanced / pro traders",
            "Options traders specifically",
        ])
    with col_d:
        content_type = st.selectbox("Content type", [
            "YouTube long video",
            "YouTube Shorts",
            "Instagram Reel",
            "Twitter / X thread",
            "LinkedIn post",
            "Live stream",
        ])

    # Platforms
    st.markdown("**Target platforms**")
    pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns(5)
    p_yt = pcol1.checkbox("YouTube", value=True)
    p_ig = pcol2.checkbox("Instagram", value=False)
    p_tw = pcol3.checkbox("X/Twitter", value=False)
    p_li = pcol4.checkbox("LinkedIn", value=False)
    p_fb = pcol5.checkbox("Facebook", value=False)

    platforms = []
    if p_yt: platforms.append("YouTube")
    if p_ig: platforms.append("Instagram")
    if p_tw: platforms.append("X/Twitter")
    if p_li: platforms.append("LinkedIn")
    if p_fb: platforms.append("Facebook")

    # Extra context
    with st.expander("➕ Extra context (optional)"):
        key_levels  = st.text_input("Key price levels (e.g. Nifty 24500 support)")
        market_view = st.selectbox("Market view", ["Neutral", "Bullish", "Bearish", "Sideways/range"])
        special_notes = st.text_area("Special notes / hooks", placeholder="e.g. Gamma blast signal triggered, must-watch before Monday open", height=80)

    # Generate button
    generate = st.button("🚀 Generate viral content", use_container_width=True, type="primary")


# ════════════════════════════════════════════════
# HELPER: build prompt
# ════════════════════════════════════════════════
def build_prompt(topic, niche, language, audience, content_type, platforms,
                 key_levels, market_view, special_notes,
                 brand_name, brand_url, brand_handle, thumb_desc=""):

    platform_str = ", ".join(platforms) if platforms else "YouTube"
    lang_instruction = {
        "English": "All output must be in English.",
        "Malayalam (മലയാളം)": "All titles, tags, and descriptions must be in Malayalam script (not transliteration). Use natural trading Malayalam as spoken by Kerala retail traders.",
        "Both English + Malayalam": "Provide each section in BOTH English AND Malayalam. Label them clearly.",
    }.get(language, "All output in English.")

    thumb_part = f"\nThumbnail description from image: {thumb_desc}" if thumb_desc else ""

    return f"""You are a viral YouTube SEO expert specialising in Indian stock market / trading content for the channel {brand_name} ({brand_handle}).

{lang_instruction}

CONTENT DETAILS:
- Topic: {topic}
- Niche: {niche}
- Audience: {audience}
- Content type: {content_type}
- Platforms: {platform_str}
- Market view: {market_view}
- Key levels: {key_levels if key_levels else 'not specified'}
- Special notes: {special_notes if special_notes else 'none'}
{thumb_part}

Generate the following in valid JSON format (no markdown code blocks, just raw JSON):

{{
  "titles": [
    {{"title": "...", "viral_score": 95, "reason": "why this works"}},
    {{"title": "...", "viral_score": 90, "reason": "why this works"}},
    {{"title": "...", "viral_score": 85, "reason": "why this works"}}
  ],
  "tags": [
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "medium"}},
    {{"tag": "...", "volume": "medium"}},
    {{"tag": "...", "volume": "low"}}
  ],
  "tags_string": "comma separated tags string under 500 characters for YouTube",
  "description": "full YouTube description with emojis, sections, CTAs, disclaimer. Include {brand_url} and {brand_handle}. 400-600 words.",
  "short_description": "2-3 sentence short description for Instagram/Twitter/LinkedIn under 150 characters",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5", "#tag6", "#tag7", "#tag8", "#tag9", "#tag10"],
  "hook_ideas": [
    "Opening hook line 1 for the video",
    "Opening hook line 2 for the video"
  ],
  "thumbnail_text_suggestions": ["text overlay idea 1", "text overlay idea 2", "text overlay idea 3"]
}}

Ensure:
- Titles are click-bait but accurate, use numbers/power words, include Nifty/BankNifty/GEX keywords
- Tags list: minimum 15 tags, high-volume first, mix of exact match and broad
- Tags string must be under 500 characters
- Description has clear sections: intro, what's covered (bullet list), CTA, disclaimer
- Hashtags are relevant to Indian trading community
- All content feels authentic for a Malayalam trading educator
"""


# ════════════════════════════════════════════════
# HELPER: encode image for vision
# ════════════════════════════════════════════════
def encode_image(uploaded_file):
    if uploaded_file is None:
        return None
    bytes_data = uploaded_file.getvalue()
    return base64.b64encode(bytes_data).decode("utf-8")


# ════════════════════════════════════════════════
# HELPER: call Groq
# ════════════════════════════════════════════════
def call_groq(prompt, api_key, model, image_b64=None, image_type="image/jpeg"):
    client = Groq(api_key=api_key)

    # Vision call to describe thumbnail first (Groq vision with llava if image provided)
    thumb_desc = ""
    if image_b64:
        try:
            vision_resp = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{image_type};base64,{image_b64}"}},
                        {"type": "text", "text": "Describe this YouTube trading video thumbnail briefly: what text, charts, indicators, or visuals are shown? Keep it under 80 words."}
                    ]
                }],
                max_tokens=150,
            )
            thumb_desc = vision_resp.choices[0].message.content.strip()
        except Exception:
            thumb_desc = ""

    # Main generation call
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt + (f"\n\nThumbnail analysis: {thumb_desc}" if thumb_desc else "")}],
        max_tokens=2500,
        temperature=0.75,
    )
    raw = resp.choices[0].message.content.strip()

    # Strip markdown code fences if model added them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    return data, thumb_desc


# ════════════════════════════════════════════════
# OUTPUT COLUMN
# ════════════════════════════════════════════════
with col_out:
    st.markdown("#### 📤 Generated content")

    if generate:
        if not topic.strip():
            st.error("Please enter a video topic first.")
        elif not groq_key:
            st.error("Please enter your Groq API key in the sidebar.")
        else:
            with st.spinner("🤖 Generating viral content with AI..."):
                try:
                    # Encode image if uploaded
                    img_b64 = None
                    img_type = "image/jpeg"
                    if thumb_file:
                        img_b64 = encode_image(thumb_file)
                        img_type = thumb_file.type or "image/jpeg"

                    prompt = build_prompt(
                        topic, niche, language, audience, content_type, platforms,
                        key_levels if 'key_levels' in dir() else "",
                        market_view if 'market_view' in dir() else "Neutral",
                        special_notes if 'special_notes' in dir() else "",
                        brand_name, brand_url, brand_handle
                    )

                    result, thumb_desc = call_groq(prompt, groq_key, model_choice, img_b64, img_type)

                    # Save to session history
                    st.session_state.history.append({
                        "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
                        "topic": topic,
                        "result": result
                    })

                    # ── Thumbnail AI description ──
                    if thumb_desc:
                        st.info(f"🖼️ **Thumbnail detected:** {thumb_desc}")

                    # ── TITLES ────────────────────
                    st.markdown('<div class="out-label">🏆 Viral title options</div>', unsafe_allow_html=True)
                    titles = result.get("titles", [])
                    for t in titles:
                        score = t.get("viral_score", "—")
                        color = "#5DCAA5" if score >= 90 else "#EF9F27" if score >= 80 else "#E24B4A"
                        st.markdown(f"""
                        <div class="title-card">
                            <span style="font-size:13px; color:#ddd; flex:1">{t['title']}</span>
                            <span class="score-badge" style="border-color:{color}; color:{color}">{score}% viral</span>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander(f"💡 Why this works", expanded=False):
                            st.caption(t.get("reason", ""))

                    # ── TAGS ──────────────────────
                    st.markdown('<div class="out-label" style="margin-top:1rem">🏷️ SEO Tags (high volume first)</div>', unsafe_allow_html=True)
                    tags = result.get("tags", [])
                    tag_html = ""
                    for tg in tags:
                        vol = tg.get("volume", "medium")
                        cls = "tag-high" if vol == "high" else "tag-med" if vol == "medium" else "tag-low"
                        tag_html += f'<span class="tag-pill {cls}">{tg["tag"]}</span>'
                    st.markdown(f'<div style="line-height:2">{tag_html}</div>', unsafe_allow_html=True)

                    tags_string = result.get("tags_string", ", ".join([t["tag"] for t in tags]))
                    char_len = len(tags_string)
                    char_class = "char-ok" if char_len <= 450 else "char-warn" if char_len <= 500 else "char-over"
                    st.markdown(f'<div class="char-count {char_class}">{char_len}/500 characters</div>', unsafe_allow_html=True)
                    st.text_area("📋 Copy-ready tags string", value=tags_string, height=80, key="tags_area")

                    # ── DESCRIPTION ───────────────
                    st.markdown('<div class="out-label" style="margin-top:1rem">📝 YouTube description</div>', unsafe_allow_html=True)
                    desc = result.get("description", "")
                    st.text_area("Full description", value=desc, height=250, key="desc_area")
                    st.caption(f"{len(desc)} characters")

                    # ── SHORT DESCRIPTION ─────────
                    short_desc = result.get("short_description", "")
                    if short_desc:
                        st.markdown('<div class="out-label" style="margin-top:0.5rem">📱 Short description (Instagram / Twitter)</div>', unsafe_allow_html=True)
                        st.text_area("Short description", value=short_desc, height=80, key="short_desc_area")

                    # ── HASHTAGS ──────────────────
                    st.markdown('<div class="out-label" style="margin-top:1rem">🔖 Hashtags</div>', unsafe_allow_html=True)
                    hashtags = result.get("hashtags", [])
                    hashtag_str = " ".join(hashtags)
                    ht_html = "".join([f'<span class="tag-pill tag-high">{h}</span>' for h in hashtags])
                    st.markdown(f'<div style="line-height:2">{ht_html}</div>', unsafe_allow_html=True)
                    st.text_area("Copy hashtags", value=hashtag_str, height=60, key="hashtags_area")

                    # ── HOOK IDEAS ────────────────
                    hooks = result.get("hook_ideas", [])
                    if hooks:
                        st.markdown('<div class="out-label" style="margin-top:1rem">🎣 Video opening hook ideas</div>', unsafe_allow_html=True)
                        for i, h in enumerate(hooks, 1):
                            st.markdown(f"**{i}.** {h}")

                    # ── THUMBNAIL TEXT ────────────
                    thumb_texts = result.get("thumbnail_text_suggestions", [])
                    if thumb_texts:
                        st.markdown('<div class="out-label" style="margin-top:1rem">🖼️ Thumbnail text overlay suggestions</div>', unsafe_allow_html=True)
                        for tt in thumb_texts:
                            st.markdown(f"• `{tt}`")

                    # ── EXPORT ────────────────────
                    st.markdown("---")
                    export_text = f"""=== NYZTrade Viral Content Export ===
Generated: {datetime.now().strftime('%d %b %Y %H:%M')}
Topic: {topic}
Niche: {niche}
Language: {language}

--- TITLES ---
{chr(10).join([f"{i+1}. {t['title']} ({t.get('viral_score','')}% viral)" for i, t in enumerate(titles)])}

--- TAGS (YouTube - copy below) ---
{tags_string}

--- DESCRIPTION ---
{desc}

--- HASHTAGS ---
{hashtag_str}

--- HOOK IDEAS ---
{chr(10).join([f"{i+1}. {h}" for i, h in enumerate(hooks)])}

--- THUMBNAIL TEXT SUGGESTIONS ---
{chr(10).join([f"• {tt}" for tt in thumb_texts])}
"""
                    st.download_button(
                        "⬇️ Download as .txt",
                        data=export_text,
                        file_name=f"nyztrade_content_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                except json.JSONDecodeError as e:
                    st.error(f"AI returned invalid JSON. Try again. ({e})")
                except Exception as e:
                    st.error(f"Error: {e}")

    else:
        # Placeholder state
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:#666">
            <div style="font-size:3rem; margin-bottom:1rem">✨</div>
            <div style="font-size:1rem; margin-bottom:0.5rem; color:#aaa">Fill in your content details</div>
            <div style="font-size:0.85rem; color:#666">and click <strong>Generate viral content</strong> to get<br>
            AI-powered titles, tags, and descriptions</div>
        </div>
        """, unsafe_allow_html=True)

        # Show history if any
        if st.session_state.history:
            st.markdown("#### 🕐 Recent generations")
            for item in reversed(st.session_state.history[-5:]):
                with st.expander(f"📌 {item['topic']} — {item['timestamp']}"):
                    titles = item['result'].get('titles', [])
                    if titles:
                        st.markdown(f"**Top title:** {titles[0]['title']}")
                    tags_str = item['result'].get('tags_string', '')
                    if tags_str:
                        st.text_area("Tags", value=tags_str, height=60, key=f"hist_{item['timestamp']}")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; font-size:12px; color:#555'>"
    "NYZTrade Analytics Pvt. Ltd. · Powered by Groq + Llama 3.3 · "
    "<a href='https://nyztrade.in' style='color:#378ADD'>nyztrade.in</a>"
    "</div>",
    unsafe_allow_html=True
)
