"""
黄金投资监控系统 V3.1
简洁现代手机UI
"""

import streamlit as st
import yfinance as yf
from fredapi import Fred
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ============ 页面配置 ============
st.set_page_config(
    page_title="黄金监控",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 现代化CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .main .block-container {
        padding: 1rem 1rem 2rem 1rem;
        max-width: 800px;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 标题样式 */
    h1 {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* 卡片容器 */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* 指标名称 */
    .metric-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.8rem;
    }
    
    .metric-emoji {
        font-size: 1.5rem;
    }
    
    .metric-name {
        font-size: 0.95rem;
        color: #666;
        font-weight: 500;
    }
    
    /* 数值显示 */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.3rem;
        line-height: 1.2;
    }
    
    /* 变化标签 */
    .change-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }
    
    .change-positive {
        background: #d4edda;
        color: #155724;
    }
    
    .change-negative {
        background: #f8d7da;
        color: #721c24;
    }
    
    .change-neutral {
        background: #e2e3e5;
        color: #383d41;
    }
    
    /* 日期标签 */
    .date-label {
        font-size: 0.75rem;
        color: #999;
        margin-top: 0.5rem;
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.8rem 1rem 0.8rem;
        }
        
        .metric-value {
            font-size: 1.9rem;
        }
        
        h1 {
            font-size: 1.5rem !important;
        }
    }
    
    /* 图表容器 */
    .chart-container {
        margin-top: 0.8rem;
        border-radius: 12px;
        overflow: hidden;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# ============ 数据获取 ============

@st.cache_data(ttl=3600)
def fetch_data(fred_key, days=90):
    """获取6个核心指标"""
    data = {}
    errors = []
    
    # FRED数据
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
    
    # Yahoo Finance数据
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

# ============ 主界面 ============

# 标题和更新时间
st.markdown("<h1>💰 黄金监控</h1>", unsafe_allow_html=True)
update_time = datetime.now().strftime('%m/%d %H:%M')
st.caption(f"🕐 {update_time} 更新 • 数据缓存1小时")

# 侧边栏配置
with st.sidebar:
    st.subheader("⚙️ 配置")
    fred_key = st.text_input(
        "FRED API",
        value="08adf813c05015a73196c5338e2fec76",
        type="password"
    )
    
    st.markdown("---")
    st.caption("📧 邮件提醒功能开发中")
    st.text_input("接收邮箱", value="66089278@qq.com", disabled=True)

# 获取数据
with st.spinner('加载中...'):
    df, errors = fetch_data(fred_key)

if errors:
    with st.expander("⚠️ 警告"):
        for e in errors:
            st.caption(e)

if df.empty:
    st.error("数据获取失败，请稍后刷新")
    st.stop()

# ============ 数据展示 ============

metrics = [
    ('黄金价格', '$/盎司', '🏆', '#f39c12'),
    ('美元指数', '', '💵', '#27ae60'),
    ('VIX恐慌指数', '', '⚡', '#e74c3c'),
    ('实际利率', '%', '📉', '#3498db'),
    ('通胀预期', '%', '📈', '#9b59b6'),
    ('名义利率', '%', '📊', '#34495e')
]

for name, unit, emoji, color in metrics:
    if name in df.columns:
        series = df[name].dropna()
        if len(series) == 0:
            continue
            
        current = series.iloc[-1]
        
        # 计算30日变化
        days_back = min(30, len(series) - 1)
        if days_back > 0:
            previous = series.iloc[-days_back-1]
            change = current - previous
            change_pct = (change / previous * 100) if previous != 0 else 0
        else:
            change_pct = 0
        
        # 卡片HTML
        change_class = "change-positive" if change_pct > 0 else "change-negative" if change_pct < 0 else "change-neutral"
        change_symbol = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-emoji">{emoji}</span>
                <span class="metric-name">{name}</span>
            </div>
            <div class="metric-value">{current:.2f}{unit}</div>
            <span class="change-badge {change_class}">{change_symbol} {abs(change_pct):.2f}% 30日</span>
            <div class="date-label">📅 {series.index[-1].date()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 趋势图 - 简化版
        chart_data = series.reset_index()
        chart_data.columns = ['日期', '数值']
        
        # 计算每个点相对于30天前的变化
        base_value = previous if days_back > 0 else series.iloc[0]
        chart_data['变化率'] = ((chart_data['数值'] - base_value) / base_value * 100).round(2)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_data['日期'],
            y=chart_data['数值'],
            mode='lines',
            name=name,
            line=dict(color=color, width=2.5),
            fill='tozeroy',
            fillcolor=f'rgba{tuple(list(bytes.fromhex(color[1:])) + [0.1])}',
            hovertemplate=(
                '<b>%{x|%Y-%m-%d}</b><br>' +
                f'{name}: %{{y:.2f}}{unit}<br>' +
                '相对30日前: %{customdata:.2f}%' +
                '<extra></extra>'
            ),
            customdata=chart_data['变化率']
        ))
        
        fig.update_layout(
            height=180,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                showticklabels=True,
                showgrid=True,
                gridcolor='rgba(128,128,128,0.1)',
                zeroline=False
            ),
            hovermode='x unified',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            # 禁用所有交互工具
            dragmode=False,
            modebar=dict(
                remove=['zoom', 'pan', 'select', 'lasso2d', 'zoomIn', 'zoomOut', 
                        'autoScale', 'resetScale', 'toImage']
            )
        )
        
        # 禁用缩放和平移
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)
        
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': False,  # 隐藏工具栏
            'staticPlot': False  # 保持可交互（仅悬停）
        })
        
        st.markdown("<br>", unsafe_allow_html=True)

# ============ 底部操作 ============

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    csv = df.to_csv().encode('utf-8')
    st.download_button(
        "📥 导出数据",
        csv,
        f"gold_{datetime.now():%Y%m%d}.csv",
        "text/csv",
        use_container_width=True
    )

with col2:
    with st.popover("ℹ️ 说明", use_container_width=True):
        st.markdown("""
        **数据来源**
        - FRED: 利率数据
        - Yahoo: 黄金、美元、VIX
        
        **趋势图说明**
        - 点击任意位置查看数值
        - 显示相对30日前的变化率
        
        **关键关系**
        - 实际利率↑ → 黄金↓
        - 美元指数↑ → 黄金↓
        - VIX↑ → 黄金↑
        """)

st.caption("⚠️ 仅供参考，不构成投资建议")
