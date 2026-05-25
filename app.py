import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
from datetime import datetime
from google import genai

# 1. 網頁基本設定（設定為 wide 寬螢幕模式）
st.set_page_config(page_title="全球盤前 AI 戰情室", page_icon="🔮", layout="wide")

# 注入 CSS 讓 metric 顯示符合台灣習慣 (紅漲綠跌)
st.markdown("""
<style>
    div[data-testid="stMetricDelta"] > div svg {
        display: none; 
    }
    div[data-testid="stMetricDelta"] > div {
        color: #FF4B4B !important; 
    }
    div[data-testid="stMetricDelta"] > div:contains("-") {
        color: #00B050 !important; 
    }
    /* 隱藏左側側邊欄，讓版面更寬大乾淨 */
    [data-testid="stSidebar"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔮 全球股市盤前 AI 戰情室")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 自動從後台秘密環境變數中讀取 API 金鑰
# 只要在 Streamlit Cloud 後台設定好，這裡就會自動讀取，安全又省事！
api_key = st.secrets.get("GEMINI_API_KEY")

# 3. 網頁佈局：左半邊（數據與熱力圖） | 右半邊（AI 盤前消息摘要）
col_left, col_right = st.columns([1.2, 1.5])

# === 左半邊：數字大盤與 Finviz 熱力圖 ===
with col_left:
    st.subheader("📈 主要市場昨日表現")
    market_tickers = {
        "S&P 500 指數": "^GSPC",
        "費城半導體": "^SOX",
        "台積電 ADR": "TSM",
        "輝達 NVDA": "NVDA"
    }
    
    results = []
    for name, ticker in market_tickers.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                close_t = hist['Close'].iloc[-1]
                close_y = hist['Close'].iloc[-2]
                change = close_t - close_y
                pct = (change / close_y) * 100
                results.append({"項目": name, "價格": round(close_t, 2), "漲跌幅(%)": round(pct, 2)})
        except:
            pass
            
    df = pd.DataFrame(results)
    if not df.empty:
        metric_cols = st.columns(4)
        for idx, row in df.iterrows():
            with metric_cols[idx]:
                prefix = "+" if row["漲跌幅(%)"] > 0 else ""
                st.metric(label=row["項目"], value=row["價格"], delta=f"{prefix}{row['漲跌幅(%)']}%")
    
    st.divider()
    
        # 🎯 修正版：直接讀取 Finviz 即時圖片流，避開網頁嵌入限制
    st.subheader("🗺️ S&P 500 前一營業日板塊熱力圖")
    
    # Finviz 官方即時更新的靜態圖片 URL
    heatmap_url = "https://finviz.com"
    
    # 顯示圖片，並設定寬度自動填滿
    st.image(heatmap_url, use_container_width=True, caption="美股最新板塊分布圖")
    
    # 提供一個精美的按鈕，點擊可以直接跳轉到官網看完整的互動操作
    st.link_button("🔗 點此開啟 Finviz 互動式網頁版", "https://finviz.com")



# === 右半邊：AI 盤前消息與板塊分析 ===
with col_right:
    st.subheader("📰 AI 盤前重點消息與板塊分析")
    
    if not api_key:
        st.error("❌ 系統未偵測到內建 API 金鑰！請至 Streamlit Cloud 後台的 Advanced settings -> Secrets 設定 GEMINI_API_KEY。")
    else:
        with st.spinner("AI 秘書正透過 Google 搜尋昨晚最新財經大事與熱門板塊，請稍候..."):
            try:
                client = genai.Client(api_key=api_key)
                
                prompt = """
                請你使用內建的 Google 搜尋工具，搜尋以下主題最新、過去 24 小時內（或最新一個美股營業日）的新聞與動態：
                1. 「美股 最新消息 財經 大盤」
                2. 「美股 領漲 板塊 科技股 財報」
                3. 「輝達 NVIDIA Nvidia 晶片 科技新聞」
                4. 「SpaceX Tesla 馬斯克 最新動態」
                5. 「聯準會 Fed 利率 官員談話」
                
                結合你搜尋到的真實最新內容，為台灣投資人撰寫今天早上 08:30 的「全球盤前重點消息總覽」。
                
                【寫作與排版嚴格規範】
                1. 必須使用「台灣繁體中文」與台灣財經術語。
                2. 內文中的關鍵專有名詞、數據（例如：H100、20%、華許、CPI等）必須使用 **粗體** 標記。
                3. 每條新聞開頭必須加上一個對應的「功能性 Emoji」（例如：🇺🇸、🔥、💰、📈）。
                4. 標題前後絕對不要加上星號或斜體。嚴格依照下方格式與指定的三大區塊輸出：
                
                ### 核心市場消息
                - 
                - 
                
                ### 科技與企業動態（含昨日美股熱門板塊分析）
                - 
                - 
                （請在此區塊特別點出：昨晚美股表現最強勢與最弱勢的板塊是哪一個？有哪些權值股有重大進展或資金流入？）
                
                ### 本週關注焦點
                - 
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config={'tools': [{'google_search': {}}]} 
                )
                
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"AI 摘要生成失敗，錯誤訊息: {e}")
