import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
from google import genai

# 1. 網頁基本設定
st.set_page_config(page_title="全球盤前 AI 戰情室", page_icon="🔮", layout="wide")

# 注入 CSS 讓 metric 顯示符合台灣習慣 (紅漲綠跌)
st.markdown("""
<style>
    div[data-testid="stMetricDelta"] > div svg { display: none; }
    div[data-testid="stMetricDelta"] > div { color: #FF4B4B !important; }
    div[data-testid="stMetricDelta"] > div:contains("-") { color: #00B050 !important; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("🔮 全球股市盤前 AI 戰情室")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 自動從後台秘密環境變數中讀取 API 金鑰
api_key = st.secrets.get("GEMINI_API_KEY")

# 🌟 數據源：逐一抓取權值股
@st.cache_data(ttl=1800)
def build_custom_heatmap():
    stocks_data = {
        "Ticker": [
            "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN", "META", "AVGO",
            "TSLA", "NFLX", "AMD", "INTC", "QCOM",
            "JPM", "BAC", "V", "MA",
            "XOM", "CVX", "LLY", "JNJ", "WMT", "COST"
        ],
        "Sector": [
            "科技 Technology", "科技 Technology", "科技 Technology", "通訊 Communication", "消費 Consumer", "通訊 Communication", "科技 Technology",
            "消費 Consumer", "通訊 Communication", "科技 Technology", "科技 Technology", "科技 Technology",
            "金融 Financial", "金融 Financial", "金融 Financial", "金融 Financial",
            "能源 Energy", "能源 Energy", "醫療 Healthcare", "醫療 Healthcare", "防守民生 Defensive", "防守民生 Defensive"
        ],
        "Industry": [
            "軟體 Software", "硬體 Hardware", "半導體 Semiconductors", "網路 Internet", "零售 Retail", "網路 Internet", "半導體 Semiconductors",
            "汽車 Automotive", "娛樂 Entertainment", "半導體 Semiconductors", "半導體 Semiconductors", "半導體 Semiconductors",
            "銀行 Banking", "銀行 Banking", "金融服務 Services", "金融服務 Services",
            "油氣 Oil & Gas", "油氣 Oil & Gas", "製藥 Pharma", "製藥 Pharma", "大型零售 Retail", "大型零售 Retail"
        ]
    }
    
    rows = []
    for i, ticker in enumerate(stocks_data["Ticker"]):
        try:
            stock_obj = yf.Ticker(ticker)
            hist = stock_obj.history(period="2d")
            
            if len(hist) >= 2:
                close_t = hist['Close'].iloc[-1]
                close_y = hist['Close'].iloc[-2]
                pct_change = ((close_t - close_y) / close_y) * 100
                
                market_cap = 500000000000 if ticker in ["MSFT", "AAPL", "NVDA", "GOOGL", "AMZN"] else 100000000000
                try:
                    market_cap = stock_obj.info.get("marketCap", market_cap)
                except:
                    pass
                
                # 格式化文字，讓代號與百分比漂亮地換行
                sign = "+" if pct_change > 0 else ""
                label_text = f"<b>{ticker}</b><br>{sign}{round(pct_change, 2)}%"
                
                rows.append({
                    "Ticker": ticker,
                    "Sector": stocks_data["Sector"][i],
                    "Industry": stocks_data["Industry"][i],
                    "Pct_Change": round(pct_change, 2),
                    "Market_Cap": market_cap,
                    "Label": label_text
                })
        except:
            continue
            
    return pd.DataFrame(rows)

# 3. 網頁佈局
col_left, col_right = st.columns([1.3, 1.5])

# === 左半邊：數字大盤與美化版熱力圖 ===
with col_left:
    st.subheader("📈 主要市場昨日表現")
    market_tickers = {"S&P 500 指數": "^GSPC", "費城半導體": "^SOX", "台積電 ADR": "TSM", "輝達 NVDA": "NVDA"}
    results = []
    for name, ticker in market_tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            pct = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            results.append({"項目": name, "價格": round(hist['Close'].iloc[-1], 2), "漲跌幅(%)": round(pct, 2)})
        except: pass
    
    if results:
        metric_cols = st.columns(4)
        for idx, row in enumerate(results):
            with metric_cols[idx]:
                prefix = "+" if row["漲跌幅(%)"] > 0 else ""
                st.metric(label=row["項目"], value=row["價格"], delta=f"{prefix}{row['漲跌幅(%)']}%")
    
    st.divider()
    
    # 呈現自製精美熱力圖
    st.subheader("🗺️ 美股權值股熱力圖 (高質感台股配色)")
    with st.spinner("正在優化渲染高質感地圖..."):
        df_heatmap = build_custom_heatmap()
        
        if not df_heatmap.empty:
            # 建立精細樹狀圖
            fig = px.treemap(
                df_heatmap,
                path=['Sector', 'Industry', 'Label'],
                values='Market_Cap',
                color='Pct_Change',
                # 調整更細緻的色階：鮮綠 -> 深灰黑 -> 鮮紅
                color_continuous_scale=[
                    [0.0, '#00A151'],   # 大跌（鮮綠）
                    [0.4, '#1A2E22'],   # 小跌
                    [0.5, '#1F1F1F'],   # 平盤（深灰黑）
                    [0.6, '#3A1E1E'],   # 小漲
                    [1.0, '#E22D30']    # 大漲（鮮紅）
                ],
                color_continuous_midpoint=0
            )
            
            # 🌟 視覺核心優化：細緻的外觀微調
            fig.update_layout(
                margin=dict(t=5, l=5, r=5, b=5),
                height=520,
                coloraxis_showscale=False,
                paper_bgcolor='rgba(0,0,0,0)', # 背景透明，完美融合 Streamlit 暗色主題
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            # 優化方塊內的文字樣式與邊框
            fig.update_traces(
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>市值權重依據：Market Cap<br>", # 乾淨的提示框
                marker=dict(
                    line=dict(width=1.5, color='#1E1E1E') # 將原本粗粗的黑框改為極細的高質感深色切線
                )
            )
            
            # 修正文字層級顯示，確保 Ticker 放大
            fig.update_layout(
                font=dict(family="Arial, sans-serif", size=13, color="white")
            )
            
            # 渲染互動圖表
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.write("💡 *方塊大小代表市值權重。滑鼠移到方塊上可看詳情，點擊板塊可局部放大。*")
        else:
            st.warning("暫時無法即時繪製熱力圖，請重新整理網頁。")


# === 右半邊：AI 盤前消息與板塊分析 ===
with col_right:
    st.subheader("📰 AI 盤前重點消息與板塊分析")
    if not api_key:
        st.error("❌ 系統未偵測到內建 API 金鑰！")
    else:
        with st.spinner("AI 秘書正透過 Google 搜尋昨晚最新財經大事..."):
            try:
                client = genai.Client(api_key=api_key)
                prompt = """
                請你使用內建的 Google 搜尋工具，搜尋以下主題最新、過去 24 小時內的新聞與動態：
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
                
                ### 本週關注焦點
                - 
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash', contents=prompt, config={'tools': [{'google_search': {}}]} 
                )
                st.markdown(response.text)
            except Exception as e:
                st.error(f"AI 摘要生成失敗: {e}")
