import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
from google import genai

# 1. 網頁基本設定
st.set_page_config(page_title="全球盤前 AI 戰情室", page_icon="🔮", layout="wide")
st.title("🔮 全球股市盤前 AI 戰情室")
st.write(f"系統檢查時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 2. 側邊欄：設定您的 AI 金鑰（第一次使用需輸入）
st.sidebar.header("⚙️ 系統設定")
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password", help="請至 Google AI Studio 免費申請")

# 3. 左半邊：數字大盤數據
col_data, col_ai = st.columns([1, 1.5])

with col_data:
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
        for _, row in df.iterrows():
            st.metric(label=row["項目"], value=row["價格"], delta=f"{row['漲跌幅(%)']}%")
    
    st.divider()
    st.write("💡 *數據每 5 分鐘自動刷新。*")

# 4. 右半邊：AI 盤前消息摘要
# 右半邊：AI 盤前消息摘要
with col_ai:
    st.subheader("📰 AI 盤前重點消息總覽")
    
    if not api_key:
        st.info("🔑 請在左側欄位輸入您的 Gemini API 金鑰以啟動 AI 盤前摘要功能。")
    else:
        with st.spinner("AI 秘書正透過 Google 搜尋昨晚最新財經大事，請稍候..."):
            try:
                # 1. 啟用新版 Client
                client = genai.Client(api_key=api_key)
                
                # 2. 撰寫強力的 Prompt，並強制 AI 在寫報告前必須去 Google 搜尋以下關鍵字
                prompt = """
                請你使用內建的 Google 搜尋工具，搜尋以下主題的最新進展（特別是過去 24 小時內的新聞）：
                1. 「美股 最新消息 財經」
                2. 「輝達 NVIDIA Nvidia 晶片 科技新聞」
                3. 「SpaceX Tesla 馬斯克 最新動態」
                4. 「聯準會 Fed 利率」
                
                結合你搜尋到的真實最新內容，為台灣投資人撰寫今天早上 08:30 的「全球盤前重點消息總覽」。
                
                【嚴格拒絕廢話與罐頭回覆】
                如果搜尋到具體新聞，請直接寫出具體事件、公司名稱、數據或政策內容。
                絕對不准使用「目前並無重大突發新聞」、「交易清淡」、「暫無新的催化劑」等敷衍字眼。
                就算美股週末休市，也請統整週末期間科技巨頭（如馬斯克、輝達、台積電）的最新動態、國際總經或外媒週報焦點。
                
                【格式規範】
                必須使用「台灣繁體中文」與台灣財經術語，結構如下：
                
                ### 核心市場消息
                - 地緣政治與總經風險（請寫出具體國家或原油走勢事件）
                - 聯準會（Fed）動向與政策不確定性
                
                ### 科技與企業動態
                - AI 需求與科技硬體（如輝達、台積電最新進展，請寫出具體技術或晶片消息）
                - 傳統巨頭、車廠轉型（如福特、特斯拉、SpaceX 等）與市場重大動態
                
                ### 本週關注焦點
                - 本週即將公布財報的代表性企業或重要經濟數據預告
                """
                
                # 3. 呼叫 Gemini 並開啟 Google Search 擴充工具
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    # 關鍵：開啟 Google 搜尋工具
                    config={'tools': [{'google_search': {}}]} 
                )
                
                # 4. 渲染 AI 生成的精美 Markdown 內容
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"AI 摘要生成失敗，錯誤訊息: {e}")

