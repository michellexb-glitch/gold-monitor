"""
黄金投资监控系统 V3.0
- 6个核心指标 + VIX
- 交互式趋势图
- 手机优化显示
- 邮件提醒功能
"""

import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ============ 页面配置 ============
st.set_page_config(
    page_title="黄金数据监控",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS - 手机优化
st.markdown("""
<style>
    /* 手机端优化 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* 大字体显示数值 */
    .big-value {
        font-size: 2.5rem !important;
        font-weight: bold;
        color: #1f77b4;
        margin: 0;
    }
    
    /* 指标名称 */
    .metric-name {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .big-value {
            font-size: 2rem !important;
        }
        h1 {
            font-size: 1.8rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============ 数据获取 ============

@st.cache_data(ttl=3600)
def fetch_data(fred_key, days=90):
    """获取6个核心指标"""
    data = {}
    errors = []
    
    # 1. FRED数据
    try:
        fred = Fred(api_key=fred_key)
        start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        series = {
            'DGS10': '名义利率',
            'T10YIE': '通胀预期',
            'DFII10': '实际利率'
        }
        
        for code, name in series.items():
            try:
                s = fred.get_series(code, start)
                if s is not None and not s.empty:
                    data[name] = s
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
    except Exception as e:
        errors.append(f"FRED: {str(e)}")
    
    # 2. Yahoo Finance数据
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        
        tickers = {
            'GC=F': '黄金价格',
            'DX-Y.NYB': '美元指数',
            '^VIX': 'VIX恐慌指数'
        }
        
        for ticker, name in tickers.items():
            try:
                df = yf.download(ticker, start=start, end=end, progress=False)
                if not df.empty and 'Close' in df.columns:
                    data[name] = df['Close'].squeeze()
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
            
    except Exception as e:
        errors.append(f"Yahoo: {str(e)}")
    
    if not data:
        return pd.DataFrame(), errors
    
    try:
        df = pd.DataFrame(data)
        return df, errors
    except Exception as e:
        errors.append(f"数据合并错误: {str(e)}")
        return pd.DataFrame(), errors

def send_email_alert(to_email, subject, body, from_email="", password=""):
    """发送邮件提醒（需要配置SMTP）"""
    try:
        if not from_email or not password:
            return False, "邮件配置未设置"
            
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # QQ邮箱SMTP配置
        server = smtplib.SMTP_SSL('smtp.qq.com', 465)
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return True, "邮件发送成功"
    except Exception as e:
        return False, f"邮件发送失败: {str(e)}"

# ============ 主界面 ============

st.title("💰 黄金数据监控")
st.caption("核心6指标 + 交互式趋势图")

# 侧边栏配置
with st.sidebar:
    st.subheader("⚙️ 配置")
    
    fred_key = st.text_input(
        "FRED API密钥",
        value="08adf813c05015a73196c5338e2fec76",
        type="password"
    )
    
    st.markdown("---")
    st.subheader("📧 邮件提醒设置")
    st.caption("功能开发中，下一版本启用")
    
    enable_alert = st.checkbox("启用邮件提醒")
    alert_email = st.text_input("接收邮箱", value="66089278@qq.com")
    
    if enable_alert:
        st.info("💡 提示：邮件提醒需要配置SMTP服务器，当前版本暂未启用")

# 获取数据
with st.spinner('📊 加载数据...'):
    df, errors = fetch_data(fred_key)

st.caption(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据缓存1小时")

if errors:
    with st.expander("⚠️ 数据获取警告"):
        for e in errors:
            st.caption(e)

if df.empty:
    st.error("❌ 暂时无法获取数据")
    st.info("💡 可能原因：网络问题或API频率限制，请稍后刷新")
    st.stop()

# ============ 数据展示 ============

st.markdown("---")

metrics = [
    ('黄金价格', '$/盎司', '🏆', 'gold'),
    ('美元指数', '', '💵', 'green'),
    ('VIX恐慌指数', '', '⚡', 'red'),
    ('名义利率', '%', '📊', 'blue'),
    ('通胀预期', '%', '📈', 'purple'),
    ('实际利率', '%', '📉', 'orange')
]

for name, unit, emoji, color in metrics:
    if name in df.columns:
        series = df[name].dropna()
        if len(series) > 0:
            st.markdown(f"### {emoji} {name}")
            
            # 上半部分：当前值和变化
            col1, col2 = st.columns([2, 1])
            
            current = series.iloc[-1]
            
            with col1:
                st.markdown(f'<p class="big-value">{current:.2f}{unit}</p>', unsafe_allow_html=True)
            
            with col2:
                # 30日变化
                days_back = min(30, len(series) - 1)
                if days_back > 0:
                    previous = series.iloc[-days_back-1]
                    change = current - previous
                    change_pct = (change / previous * 100) if previous != 0 else 0
                    
                    delta_color = "normal"
                    st.metric(
                        label=f"30日变化",
                        value="",
                        delta=f"{change_pct:+.2f}%"
                    )
                    st.caption(f"公式: ({current:.2f} - {previous:.2f}) / {previous:.2f} × 100%")
            
            # 下半部分：趋势图
            st.markdown("**📈 趋势图**")
            
            # 准备图表数据
            chart_data = series.reset_index()
            chart_data.columns = ['日期', '数值']
            
            # 创建交互式图表
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=chart_data['日期'],
                y=chart_data['数值'],
                mode='lines+markers',
                name=name,
                line=dict(color=color, width=2),
                marker=dict(size=4),
                hovertemplate='<b>日期</b>: %{x|%Y-%m-%d}<br>' +
                              f'<b>{name}</b>: %{{y:.2f}}{unit}<br>' +
                              '<extra></extra>'
            ))
            
            # 添加30日前的参考点
            if days_back > 0:
                ref_date = chart_data['日期'].iloc[-days_back-1]
                ref_value = chart_data['数值'].iloc[-days_back-1]
                
                fig.add_trace(go.Scatter(
                    x=[ref_date],
                    y=[ref_value],
                    mode='markers',
                    name='30日前',
                    marker=dict(size=10, color='red', symbol='diamond'),
                    hovertemplate=f'<b>30日前</b><br>%{{x|%Y-%m-%d}}<br>{ref_value:.2f}{unit}<extra></extra>'
                ))
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=20, b=0),
                xaxis=dict(
                    title="",
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)'
                ),
                yaxis=dict(
                    title=f"{name} ({unit})",
                    showgrid=True,
                    gridcolor='rgba(128,128,128,0.2)'
                ),
                hovermode='x unified',
                showlegend=False,
                plot_bgcolor='rgba(240,240,240,0.5)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 最新日期
            st.caption(f"📅 最新数据: {series.index[-1].date()} | 数据点数: {len(series)}")
            
            st.markdown("---")

# ============ 数据表格 ============

with st.expander("📋 查看完整数据表（最近30天）"):
    recent = df.tail(30).sort_index(ascending=False)
    recent.index = recent.index.date
    st.dataframe(recent, use_container_width=True)

# ============ 下载和说明 ============

col1, col2 = st.columns(2)

with col1:
    csv = df.to_csv().encode('utf-8')
    st.download_button(
        "📥 下载CSV数据",
        csv,
        f"gold_data_{datetime.now():%Y%m%d}.csv",
        "text/csv",
        use_container_width=True
    )

with col2:
    with st.popover("ℹ️ 数据说明", use_container_width=True):
        st.markdown("""
        **数据来源：**
        - 黄金、美元、VIX：Yahoo Finance
        - 利率数据：FRED
        
        **30日变化公式：**
        ```
        变化率 = (今天值 - 30天前值) / 30天前值 × 100%
        ```
        
        **趋势图说明：**
        - 鼠标悬停可查看具体数值
        - 红色菱形标记30天前的参考点
        - 可对比任意两天的数据
        
        **关键关系：**
        - 实际利率 ≈ 名义利率 - 通胀预期
        - 实际利率↑ → 黄金通常↓
        - 美元指数↑ → 黄金通常↓
        - VIX↑ → 避险需求↑ → 黄金↑
        """)

st.caption("⚠️ 仅供参考，不构成投资建议")

# ============ 邮件提醒逻辑（待配置）============

# 检查是否需要发送提醒
if enable_alert and not df.empty:
    # 这里可以添加触发条件
    # 例如：实际利率 < 0, VIX > 30 等
    # 当前版本仅做界面，实际邮件发送需要配置SMTP
    pass
