import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
from google import genai

# 1. 網頁基本設定
st.set_page_config(page_title="盤前資訊整理", page_icon="🔮", layout="wide")

# 注入 CSS 讓 metric 顯示符合台灣習慣 (紅漲綠跌)
st.markdown("""
<style>
    div[data-testid="stMetricDelta"] > div svg { display: none; }
    div[data-testid="stMetricDelta"] > div { color: #FF4B4B !important; }
    div[data-testid="stMetricDelta"] > div:contains("-") { color: #00B050 !important; }
    [data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

st.title("🔮 盤前資訊整理")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 自動從後台秘密環境變數中讀取 API 金鑰
api_key = st.secrets.get("GEMINI_API_KEY")

# 🌟 數據源：權值股抓取（102檔無錯縮進版）
@st.cache_data(ttl=1800)
def build_custom_heatmap():
    stocks_data = {
        "Ticker": [
            # === 科技 Technology (26檔) ===
            "MSFT", "AAPL", "NVDA", "AVGO", "AMD", "QCOM", "TXN", "MU", "INTC", "ADI", 
            "AMAT", "LRCX", "KLAC", "ASML", "ORCL", "CRM", "ACN", "PANW", "FTNT", "SNPS", 
            "CDNS", "PLTR", "SMCI", "IBM", "CSCO", "HPE",
            
            # === 通訊 Communication (10檔) ===
            "GOOGL", "META", "NFLX", "DIS", "TMUS", "CMCSA", "VZ", "T", "EA", "TTWO",
            
            # === 消費 Consumer Cyclical & Defensive (22檔) ===
            "AMZN", "TSLA", "HD", "LOW", "NKE", "MCD", "SBUX", "BKNG", "TJX", "CMG",
            "WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "EL", "CL", "TGT", 
            "DG", "KR",
            
            # === 金融 Financials (15檔) ===
            "JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "V", "MA", "PYPL", 
            "BLK", "BRK-B", "SPGI", "MMC", "CB",
            
            # === 醫療 Healthcare (15檔) ===
            "LLY", "JNJ", "UNH", "VRTX", "MRK", "ABBV", "PFE", "BMY", "AMGN", "GILD", 
            "ISRG", "MDT", "SYK", "BSX", "TMO",
            
            # === 工業、能源與材料 Industrials & Energy & Materials (14檔) ===
            "GE", "CAT", "HON", "LMT", "RTX", "UPS", "FDX", "XOM", "CVX", "COP", 
            "SLB", "EOG", "LIN", "APD"
        ],
        "Sector": [
            # 科技
            "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology",
            "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology", "Technology",
            "Technology", "Technology", "Technology", "Technology", "Technology", "Technology",
            # 通訊
            "Communication", "Communication", "Communication", "Communication", "Communication", "Communication", "Communication", "Communication", "Communication", "Communication",
            # 消費
            "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer",
            "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer", "Consumer",
            "Consumer", "Consumer",
            # 金融
            "Financial", "Financial", "Financial", "Financial", "Financial", "Financial", "Financial", "Financial", "Financial", "Financial",
            "Financial", "Financial", "Financial", "Financial", "Financial",
            # 醫療
            "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
            "Healthcare", "Healthcare", "Healthcare", "Healthcare", "Healthcare",
            # 工業能源材料
            "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy",
            "Industrials & Energy", "Industrials & Energy", "Industrials & Energy", "Industrials & Energy"
        ],
        "Industry": [
            # 科技細分
            "Software", "Hardware", "Semiconductors", "Semiconductors", "Semiconductors", "Semiconductors", "Semiconductors", "Semiconductors", "Semiconductors", "Semiconductors",
            "Equipment", "Equipment", "Equipment", "Semiconductors", "Software", "Software", "IT Services", "Cybersecurity", "Cybersecurity", "Software",
            "Software", "AI & Software", "AI Hardware", "IT Services", "Hardware", "Hardware",
            # 通訊細分
            "Internet", "Internet", "Entertainment", "Entertainment", "Telecom", "Telecom", "Telecom", "Telecom", "Entertainment", "Entertainment",
            # 消費細分
            "Internet Retail", "Automotive", "Retail", "Retail", "Apparel", "Restaurants", "Restaurants", "Travel", "Retail", "Restaurants",
            "Mega Retail", "Mega Retail", "Household", "Beverages", "Beverages", "Tobacco", "Tobacco", "Personal Care", "Household", "Retail",
            "Retail", "Grocery",
            # 金融細分
            "Banking", "Banking", "Banking", "Banking", "Capital Markets", "Capital Markets", "Credit Services", "Credit Services", "Credit Services", "Credit Services",
            "Asset Management", "Insurance", "Financial Data", "Insurance Brokers", "Insurance",
            # 醫療細分
            "Pharma", "Pharma", "Healthcare Plans", "Biotech", "Pharma", "Pharma", "Pharma", "Pharma", "Biotech", "Biotech",
            "Medical Devices", "Medical Devices", "Medical Devices", "Medical Devices", "Diagnostics",
            # 工業能源材料細分
            "Aerospace", "Machinery", "Conglomerates", "Defense", "Defense", "Logistics", "Logistics", "Oil & Gas", "Oil & Gas", "Oil & Gas",
            "Oil Services", "Oil & Gas", "Chemicals", "Chemicals"
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
                
                rows.append({
                    "Ticker": ticker,
                    "Sector": stocks_data["Sector"][i],
                    "Industry": stocks_data["Industry"][i],
                    "Pct_Change": round(pct_change, 2),
                    "Market_Cap": market_cap,
                    "Label": f"{ticker}<br>{round(pct_change, 2)}%"
                })
        except:
            continue
            
    return pd.DataFrame(rows)


# 3. 網頁佈局
col_left, col_right = st.columns([1.3, 1.5])

# === 左半邊：數字大盤與自製熱力圖 ===
with col_left:
    st.subheader("📈 主要市場昨日表現")
    market_tickers = {"道瓊工業指數": "^DJI","S&P 500 指數": "^GSPC", "費城半導體": "^SOX", "台積電 ADR": "TSM", "輝達 NVDA": "NVDA"}
    results = []
    for name, ticker in market_tickers.items():
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            pct = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            results.append({"項目": name, "價格": round(hist['Close'].iloc[-1], 2), "漲跌幅(%)": round(pct, 2)})
        except: pass

    if results:
        # 建立第一排的 4 個格子
        u_cols = st.columns(4)
        # 建立第二排的 3 個格子
        t_cols = st.columns(3)
        
        for idx, row in enumerate(results):
            prefix = "+" if row["漲跌幅(%)"] > 0 else ""
            
            if idx < 4:
                # 前 4 個放第一排（道瓊、SP500、費半、台積電ADR）
                with u_cols[idx]:
                    st.metric(label=row["項目"], value=row["價格"], delta=f"{prefix}{row['漲跌幅(%)']}%")
            else:
                # 第 5 個（輝達）以及未來新增的台股項目，自動改放第二排
                with t_cols[idx - 4]:
                    st.metric(label=row["項目"], value=row["價格"], delta=f"{prefix}{row['漲跌幅(%)']}%")


    st.divider()
    
    # 呈現自製熱力圖
    st.subheader("🗺️ SP500熱力圖")
    with st.spinner("正在即時繪製美股板塊地圖..."):
        df_heatmap = build_custom_heatmap()
        
        if not df_heatmap.empty:
        # 建立樹狀圖（強制加上色彩範圍限制，徹底解決極端值稀釋顏色的問題）
            fig = px.treemap(
                df_heatmap,
                path=['Sector', 'Industry', 'Label'],
                values='Market_Cap',
                color='Pct_Change',
                # 標準美股原廠色階
                color_continuous_scale=[
                    [0.0, '#E22D30'],   # 大跌（鮮紅）
                    [0.35, '#441B1B'],  # 微跌（暗紅）
                    [0.5, '#1E1E1E'],   # 平盤（深灰黑）
                    [0.65, '#16291B'],  # 微漲（暗綠）
                    [1.0, '#00B050']    # 大漲（鮮綠）
                ],
                color_continuous_midpoint=0,
                range_color=[-3, 3],    # 🛠️ 核心修正點 1：強制鎖定色彩範圍在 -3% ~ +3% 之間
                template="plotly_dark"
            )

            
             # 安全調整排版：僅微調邊距與背景，不觸碰會報錯的文字內聯引數
            fig.update_layout(
                margin=dict(t=25, l=10, r=10, b=10), 
                height=530,
                coloraxis_showscale=False, # 🛠️ 核心修正點 2：確保隱藏右側的 3 到 -3 數字顏色條
                paper_bgcolor='rgba(0,0,0,0)',       
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            fig.update_traces(textposition="middle center")


            
            # 渲染互動圖表
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.write("💡 *滑鼠移到方塊上可看詳情，點擊板塊方塊可局部放大。*")
        else:
            st.warning("暫時無法即時繪製熱力圖，請重新整理網頁。")


# === 右半邊：AI 盤前消息與板塊分析 ===
with col_right:
    st.subheader("📰 盤前重點消息與板塊分析")
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
