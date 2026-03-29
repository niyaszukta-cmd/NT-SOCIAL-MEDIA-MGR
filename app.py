import streamlit as st
import os
import json
import base64
from datetime import datetime
from openai import OpenAI

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
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
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
    .char-count { font-size: 11px; color: #888; text-align: right; margin-top: 4px; }
    .char-ok  { color: #5DCAA5; }
    .char-warn{ color: #EF9F27; }
    .char-over{ color: #E24B4A; }
    .out-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888;
        margin-bottom: 8px;
        font-weight: 600;
    }
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

# ── OpenRouter model lists ────────────────────────────────────────────────────
OR_MODELS = {
    "Llama 3.3 70B (free)":   "meta-llama/llama-3.3-70b-instruct:free",
    "Llama 3.1 8B (free)":    "meta-llama/llama-3.1-8b-instruct:free",
    "Gemma 3 27B (free)":     "google/gemma-3-27b-it:free",
    "Gemma 3 12B (free)":     "google/gemma-3-12b-it:free",
    "Mistral 7B (free)":      "mistralai/mistral-7b-instruct:free",
    "DeepSeek R1 (free)":     "deepseek/deepseek-r1:free",
    "Qwen 2.5 72B (free)":    "qwen/qwen-2.5-72b-instruct:free",
}

OR_VISION_MODELS = {
    "Llama 3.2 11B Vision (free)": "meta-llama/llama-3.2-11b-vision-instruct:free",
    "Gemma 3 27B (free)":          "google/gemma-3-27b-it:free",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.markdown("**OpenRouter API Key**")
    or_key = st.text_input(
        "Paste key here",
        value=os.environ.get("OPENROUTER_API_KEY", ""),
        type="password",
        help="Free key at openrouter.ai",
        label_visibility="collapsed",
    )
    st.caption("🔗 [Get free key → openrouter.ai/keys](https://openrouter.ai/keys)")

    st.markdown("---")
    st.markdown("**Text model**")
    model_label = st.selectbox("Text model", list(OR_MODELS.keys()), label_visibility="collapsed")
    model_id    = OR_MODELS[model_label]

    st.markdown("**Vision model** (thumbnail analysis)")
    vision_label = st.selectbox("Vision model", list(OR_VISION_MODELS.keys()), label_visibility="collapsed")
    vision_id    = OR_VISION_MODELS[vision_label]

    st.markdown("---")
    st.markdown("**Brand defaults**")
    brand_name   = st.text_input("Channel / Brand",  value="NYZTrade")
    brand_url    = st.text_input("Website",           value="nyztrade.in")
    brand_handle = st.text_input("YouTube handle",   value="@NYZTrade")

    st.markdown("---")
    if "history" not in st.session_state:
        st.session_state.history = []
    st.markdown(f"**History** — {len(st.session_state.history)} generated")
    if st.session_state.history:
        if st.button("🗑️ Clear history"):
            st.session_state.history = []
            st.rerun()

# ── Layout ────────────────────────────────────────────────────────────────────
col_in, col_out = st.columns([1, 1], gap="large")

# ════════════════════════════════════════════════
# INPUT COLUMN
# ════════════════════════════════════════════════
with col_in:
    st.markdown("#### 📥 Content input")

    thumb_file = st.file_uploader(
        "Upload thumbnail / image (optional — AI will analyse it)",
        type=["png", "jpg", "jpeg", "webp"],
    )
    if thumb_file:
        st.image(thumb_file, use_column_width=True, caption="Thumbnail preview")

    st.markdown("---")

    topic = st.text_input(
        "Video topic / keyword *",
        placeholder="e.g. Nifty GEX analysis Monday expiry prediction",
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

    st.markdown("**Target platforms**")
    pc1, pc2, pc3, pc4, pc5 = st.columns(5)
    p_yt = pc1.checkbox("YouTube",   value=True)
    p_ig = pc2.checkbox("Instagram", value=False)
    p_tw = pc3.checkbox("X/Twitter", value=False)
    p_li = pc4.checkbox("LinkedIn",  value=False)
    p_fb = pc5.checkbox("Facebook",  value=False)

    platforms = [p for p, sel in [
        ("YouTube", p_yt), ("Instagram", p_ig), ("X/Twitter", p_tw),
        ("LinkedIn", p_li), ("Facebook", p_fb)] if sel]

    with st.expander("➕ Extra context (optional)"):
        key_levels    = st.text_input("Key price levels (e.g. Nifty 24500 support)")
        market_view   = st.selectbox("Market view", ["Neutral", "Bullish", "Bearish", "Sideways/range"])
        special_notes = st.text_area("Special notes / hooks",
            placeholder="e.g. Gamma blast signal triggered, must-watch before Monday open",
            height=80)

    generate = st.button("🚀 Generate viral content", use_container_width=True, type="primary")


# ════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════
def build_prompt(topic, niche, language, audience, content_type, platforms,
                 key_levels, market_view, special_notes,
                 brand_name, brand_url, brand_handle):

    lang_map = {
        "English": "All output must be in English.",
        "Malayalam (മലയാളം)": (
            "All titles, tags, and descriptions must be in Malayalam script "
            "(not transliteration). Use natural trading Malayalam."
        ),
        "Both English + Malayalam": (
            "Provide each section in BOTH English AND Malayalam. Label clearly."
        ),
    }
    lang_instruction = lang_map.get(language, "All output in English.")
    platform_str = ", ".join(platforms) if platforms else "YouTube"

    return f"""You are a viral YouTube SEO expert for Indian stock market content — channel {brand_name} ({brand_handle}).

{lang_instruction}

DETAILS:
Topic: {topic}
Niche: {niche}
Audience: {audience}
Content type: {content_type}
Platforms: {platform_str}
Market view: {market_view}
Key levels: {key_levels or 'not specified'}
Special notes: {special_notes or 'none'}

Return ONLY valid raw JSON — no markdown fences, no explanation:

{{
  "titles": [
    {{"title": "...", "viral_score": 95, "reason": "..."}},
    {{"title": "...", "viral_score": 90, "reason": "..."}},
    {{"title": "...", "viral_score": 85, "reason": "..."}}
  ],
  "tags": [
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "high"}},
    {{"tag": "...", "volume": "medium"}},
    {{"tag": "...", "volume": "medium"}},
    {{"tag": "...", "volume": "low"}}
  ],
  "tags_string": "comma separated YouTube tags under 500 chars",
  "description": "full YouTube description 400-600 words with emojis, sections, CTA, disclaimer, include {brand_url} and {brand_handle}",
  "short_description": "short Instagram/Twitter description under 150 chars",
  "hashtags": ["#tag1","#tag2","#tag3","#tag4","#tag5","#tag6","#tag7","#tag8","#tag9","#tag10"],
  "hook_ideas": ["hook 1", "hook 2"],
  "thumbnail_text_suggestions": ["overlay 1", "overlay 2", "overlay 3"]
}}

Rules: 15+ tags minimum, high-volume first, tags_string under 500 chars.
"""


def encode_image(f):
    return base64.b64encode(f.getvalue()).decode("utf-8") if f else None


def call_openrouter(prompt, api_key, model_id, vision_id, image_b64=None, image_type="image/jpeg"):
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://nyztrade.in",
            "X-Title": "NYZTrade Viral Content Generator",
        },
    )

    # Vision: describe thumbnail
    thumb_desc = ""
    if image_b64:
        try:
            vr = client.chat.completions.create(
                model=vision_id,
                messages=[{"role": "user", "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{image_type};base64,{image_b64}"}},
                    {"type": "text",
                     "text": "Describe this YouTube trading thumbnail briefly: text, charts, indicators shown. Under 80 words."},
                ]}],
                max_tokens=150,
            )
            thumb_desc = vr.choices[0].message.content.strip()
        except Exception:
            pass

    full_prompt = prompt + (f"\n\nThumbnail analysis: {thumb_desc}" if thumb_desc else "")

    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": full_prompt}],
        max_tokens=2500,
        temperature=0.75,
    )
    raw = resp.choices[0].message.content.strip()

    # Strip markdown fences robustly
    if "```" in raw:
        for part in raw.split("```"):
            part = part.strip().lstrip("json").strip()
            if part.startswith("{"):
                raw = part
                break

    # Extract JSON boundaries
    s, e = raw.find("{"), raw.rfind("}") + 1
    if s != -1 and e > s:
        raw = raw[s:e]

    return json.loads(raw), thumb_desc


# ════════════════════════════════════════════════
# OUTPUT COLUMN
# ════════════════════════════════════════════════
with col_out:
    st.markdown("#### 📤 Generated content")

    if generate:
        if not topic.strip():
            st.error("Please enter a video topic first.")
        elif not or_key:
            st.error("Please add your OpenRouter API key in the sidebar. It's free at openrouter.ai")
        else:
            with st.spinner("🤖 Generating via OpenRouter..."):
                try:
                    img_b64  = encode_image(thumb_file)
                    img_type = (thumb_file.type or "image/jpeg") if thumb_file else "image/jpeg"

                    prompt = build_prompt(
                        topic, niche, language, audience, content_type, platforms,
                        key_levels, market_view, special_notes,
                        brand_name, brand_url, brand_handle,
                    )

                    result, thumb_desc = call_openrouter(
                        prompt, or_key, model_id, vision_id, img_b64, img_type
                    )

                    st.session_state.history.append({
                        "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
                        "topic": topic,
                        "result": result,
                    })

                    if thumb_desc:
                        st.info(f"🖼️ **Thumbnail detected:** {thumb_desc}")

                    # Titles
                    st.markdown('<div class="out-label">🏆 Viral title options</div>', unsafe_allow_html=True)
                    titles = result.get("titles", [])
                    for t in titles:
                        score = t.get("viral_score", 0)
                        color = "#5DCAA5" if score >= 90 else "#EF9F27" if score >= 80 else "#E24B4A"
                        st.markdown(f"""<div class="title-card">
                            <span style="font-size:13px;color:#ddd;flex:1">{t['title']}</span>
                            <span class="score-badge" style="border-color:{color};color:{color}">{score}% viral</span>
                        </div>""", unsafe_allow_html=True)
                        with st.expander("💡 Why this works", expanded=False):
                            st.caption(t.get("reason", ""))

                    # Tags
                    st.markdown('<div class="out-label" style="margin-top:1rem">🏷️ SEO tags (high volume first)</div>', unsafe_allow_html=True)
                    tags = result.get("tags", [])
                    tag_html = "".join([
                        f'<span class="tag-pill {"tag-high" if tg.get("volume")=="high" else "tag-med" if tg.get("volume")=="medium" else "tag-low"}">{tg["tag"]}</span>'
                        for tg in tags
                    ])
                    st.markdown(f'<div style="line-height:2">{tag_html}</div>', unsafe_allow_html=True)

                    tags_string = result.get("tags_string", ", ".join([t["tag"] for t in tags]))
                    clen = len(tags_string)
                    ccls = "char-ok" if clen <= 450 else "char-warn" if clen <= 500 else "char-over"
                    st.markdown(f'<div class="char-count {ccls}">{clen}/500 characters</div>', unsafe_allow_html=True)
                    st.text_area("📋 Copy-ready tags string", value=tags_string, height=80, key="tags_area")

                    # Description
                    st.markdown('<div class="out-label" style="margin-top:1rem">📝 YouTube description</div>', unsafe_allow_html=True)
                    desc = result.get("description", "")
                    st.text_area("Full description", value=desc, height=250, key="desc_area")
                    st.caption(f"{len(desc)} characters")

                    # Short description
                    short_desc = result.get("short_description", "")
                    if short_desc:
                        st.markdown('<div class="out-label" style="margin-top:0.5rem">📱 Short description (Instagram / Twitter)</div>', unsafe_allow_html=True)
                        st.text_area("Short description", value=short_desc, height=80, key="short_area")

                    # Hashtags
                    st.markdown('<div class="out-label" style="margin-top:1rem">🔖 Hashtags</div>', unsafe_allow_html=True)
                    hashtags    = result.get("hashtags", [])
                    hashtag_str = " ".join(hashtags)
                    st.markdown(''.join([f'<span class="tag-pill tag-high">{h}</span>' for h in hashtags]), unsafe_allow_html=True)
                    st.text_area("Copy hashtags", value=hashtag_str, height=60, key="hashtags_area")

                    # Hooks
                    hooks = result.get("hook_ideas", [])
                    if hooks:
                        st.markdown('<div class="out-label" style="margin-top:1rem">🎣 Video opening hooks</div>', unsafe_allow_html=True)
                        for i, h in enumerate(hooks, 1):
                            st.markdown(f"**{i}.** {h}")

                    # Thumbnail text
                    thumb_texts = result.get("thumbnail_text_suggestions", [])
                    if thumb_texts:
                        st.markdown('<div class="out-label" style="margin-top:1rem">🖼️ Thumbnail text overlays</div>', unsafe_allow_html=True)
                        for tt in thumb_texts:
                            st.markdown(f"• `{tt}`")

                    # Export
                    st.markdown("---")
                    export_text = (
                        f"=== NYZTrade Viral Content Export ===\n"
                        f"Generated : {datetime.now().strftime('%d %b %Y %H:%M')}\n"
                        f"Topic     : {topic}\n"
                        f"Niche     : {niche}\n"
                        f"Language  : {language}\n"
                        f"Model     : {model_label}\n\n"
                        f"--- TITLES ---\n"
                        + "\n".join([f"{i+1}. {t['title']} ({t.get('viral_score','')}% viral)" for i,t in enumerate(titles)])
                        + f"\n\n--- TAGS (max 500 chars) ---\n{tags_string}"
                        + f"\n\n--- DESCRIPTION ---\n{desc}"
                        + f"\n\n--- HASHTAGS ---\n{hashtag_str}"
                        + f"\n\n--- HOOKS ---\n" + "\n".join([f"{i+1}. {h}" for i,h in enumerate(hooks)])
                        + f"\n\n--- THUMBNAIL TEXT ---\n" + "\n".join([f"• {tt}" for tt in thumb_texts])
                    )
                    st.download_button(
                        "⬇️ Download as .txt",
                        data=export_text,
                        file_name=f"nyztrade_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

                except json.JSONDecodeError as e:
                    st.error(f"AI returned invalid JSON — try a different model or regenerate. ({e})")
                except Exception as e:
                    st.error(f"Error: {e}")

    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem">
            <div style="font-size:3rem;margin-bottom:1rem">✨</div>
            <div style="font-size:1rem;margin-bottom:0.5rem;color:#aaa">Fill in your content details</div>
            <div style="font-size:0.85rem;color:#666">and click <strong>Generate viral content</strong></div>
        </div>""", unsafe_allow_html=True)

        if st.session_state.history:
            st.markdown("#### 🕐 Recent generations")
            for item in reversed(st.session_state.history[-5:]):
                with st.expander(f"📌 {item['topic']} — {item['timestamp']}"):
                    tl = item['result'].get('titles', [])
                    if tl:
                        st.markdown(f"**Top title:** {tl[0]['title']}")
                    ts = item['result'].get('tags_string', '')
                    if ts:
                        st.text_area("Tags", value=ts, height=60, key=f"h_{item['timestamp']}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:12px;color:#555'>"
    "NYZTrade Analytics Pvt. Ltd. · Powered by OpenRouter (free models) · "
    "<a href='https://nyztrade.in' style='color:#378ADD'>nyztrade.in</a>"
    "</div>",
    unsafe_allow_html=True,
)
