import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Stock Data Dashboard",
    layout="wide",
    page_icon="\U0001F4C8"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #444;
    }
    .metric-label {
        color: #aaa;
        font-size: 0.9em;
    }
    .metric-value {
        color: #fff;
        font-weight: 500;
    }
    .stock-card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #444;
        min-height: 400px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .stock-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #444;
    }
    .stock-metrics {
        background-color: #2A2A2A;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .stock-header a {
        text-decoration: none;
        color: white;
    }
    .stock-header a:hover {
        color: #00FFFF;
    }
    .about-section {
        background-color: #2A2A2A;
        padding: 15px;
        border-radius: 8px;
        margin-top: 15px;
        font-size: 0.9em;
        color: #ddd;
        max-height: 100px;
        overflow-y: auto;
    }
    .feature-container {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #444;
    }
    .section-title {
        color: #00FFFF;
        font-size: 1.2em;
        font-weight: 500;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid #444;
    }
    .feature-description {
        color: #888;
        font-size: 0.9em;
        margin-top: 5px;
        padding-left: 15px;
    }
    .filter-section {
        background-color: #2A2A2A;
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .stDateInput, .stSelectbox, .stTextInput {
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file):
    """Load and preprocess the data"""
    try:
        df = pd.read_csv(file)
        df["Today's Date"] = pd.to_datetime(df["Today's Date"])
        
        # Clean percentage change column
        df['%chng'] = df['%chng'].astype(str).str.replace('%', '').str.strip()
        df['%chng'] = pd.to_numeric(df['%chng'], errors='coerce')
        
        # Clean numeric columns
        numeric_columns = ['ROE', 'ROCE', 'P/E Ratio', 'Book Value', 'Dividend Yield']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('%', '').str.replace('₹', '')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean Market Cap column
        df['Market Cap'] = df['Market Cap'].astype(str).str.replace('₹', '').str.replace(',', '')
        df['Market Cap'] = pd.to_numeric(df['Market Cap'].str.extract(r'(\d+(?:\.\d+)?)', expand=False), errors='coerce')
        
        # Clean Symbol column
        df['Symbol'] = df['Symbol'].astype(str).str.strip().str.upper()
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def format_number(num):
    """Format numbers as currency with appropriate scale"""
    try:
        if pd.isna(num):
            return "N/A"
        if isinstance(num, str):
            num = float(num.replace('₹', '').replace(',', '').strip())
        if num >= 1e9:
            return f"₹{num/1e9:.2f}B"
        elif num >= 1e7:
            return f"₹{num/1e7:.2f}Cr"
        elif num >= 1e5:
            return f"₹{num/1e5:.2f}L"
        else:
            return f"₹{num:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def get_stock_highs(data, symbol):
    """Get dates when the stock made new highs"""
    if symbol:
        stock_data = data[data['Symbol'] == symbol].copy()
        if not stock_data.empty:
            stock_data = stock_data.sort_values("Today's Date")
            stock_data['High_LTP'] = stock_data['LTP'].cummax()
            high_dates = stock_data[stock_data['LTP'] == stock_data['High_LTP']].copy()
            return high_dates
    return pd.DataFrame()

def create_sector_chart(filtered_data):
    """Create a sector distribution bar chart"""
    sector_counts = filtered_data['Sector'].value_counts()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sector_counts.index,
        y=sector_counts.values,
        marker_color='rgba(0, 255, 255, 0.6)',
        text=sector_counts.values,
        textposition='auto',
    ))
    
    fig.update_layout(
        title={
            'text': 'Sector Distribution',
            'x': 0.5,
            'font_size': 20
        },
        xaxis_tickangle=-45,
        template='plotly_dark',
        showlegend=False,
        xaxis_title="Sector",
        yaxis_title="Number of Companies",
        height=400,
        margin=dict(t=50, b=100)
    )
    
    return fig

def create_stock_card(row):
    """Create stock card with metrics and details"""
    price_change = row['%chng']
    price_color = '#00FF00' if price_change >= 0 else '#FF0000'
    price_change_display = f"{price_change:+.2f}%" if not pd.isna(price_change) else "N/A"
    screener_url = f"https://www.screener.in/company/{row['Symbol']}/"
    
    about_text = row.get('About', 'N/A')
    if isinstance(about_text, str) and len(about_text) > 300:
        about_text = about_text[:297] + "..."
    
    return f"""
    <div class="stock-card">
        <div class="stock-header">
            <div>
                <a href="{screener_url}" target="_blank"><h3 style="margin: 0;">{row['Symbol']}</h3></a>
                <div style="color: #888; margin-top: 5px;">
                    <div>Sector: {row.get('Sector', 'N/A')}</div>
                    <div>Industry: {row.get('Industry', 'N/A')}</div>
                        <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 10px;">
        <div style="color: #888;">
            Appearances: <strong style="color: #00FFFF">{row['count']}</strong>
        </div>
        <div style="color: #888; text-align: right;">
            Last high (Days): <strong style="color: #00FFFF">{row['Days Since High']}</strong>
        </div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.2em; font-weight: 500;">{format_number(row['LTP'])}</div>
                <div style="color: {price_color};">{price_change_display}</div>
            </div>
        </div>
        <div class="stock-metrics">
            <div class="metric-row">
                <span class="metric-label">Market Cap</span>
                <span class="metric-value">{format_number(row.get('Market Cap', 'N/A'))}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">ROE</span>
                <span class="metric-value">{f"{row.get('ROE', 'N/A'):.2f}%" if pd.notnull(row.get('ROE')) else "N/A"}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">ROCE</span>
                <span class="metric-value">{f"{row.get('ROCE', 'N/A'):.2f}%" if pd.notnull(row.get('ROCE')) else "N/A"}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">P/E Ratio</span>
                <span class="metric-value">{f"{row.get('P/E Ratio', 'N/A'):.2f}" if pd.notnull(row.get('P/E Ratio')) else "N/A"}</span>
            </div>
            <div class="metric-row" style="border-bottom: none;">
                <span class="metric-label">Dividend Yield</span>
                <span class="metric-value">{f"{row.get('Dividend Yield', 'N/A'):.2f}%" if pd.notnull(row.get('Dividend Yield')) else "N/A"}</span>
            </div>
        </div>
        <div class="about-section">
            <strong>About:</strong> {about_text}
        </div>
    </div>
    """

def get_latest_stock_data(filtered_data):
    """Get the latest data for each stock with count"""
    stock_counts = filtered_data['Symbol'].value_counts().to_dict()
    latest_data = filtered_data.sort_values(["Today's Date", '%chng'], ascending=[False, False]).groupby('Symbol').first().reset_index()
    latest_data['count'] = latest_data['Symbol'].map(stock_counts)
    return latest_data.sort_values('count', ascending=False)

def create_feature_selector():
    """Create an enhanced feature selector with descriptions"""
    st.sidebar.markdown('<p class="section-title">🎯 Analysis Mode</p>', unsafe_allow_html=True)
    
    features = {
        "Specific Date⌚": {
            "description": "Analyze stocks for a specific date",
            "icon": "📅"
        },
        "Date Range": {
            "description": "Compare stock performance over a custom period",
            "icon": "📊"
        },
        "Month📅": {
            "description": "View monthly performance and trends",
            "icon": "📈"
        },
        "Search🔎": {
            "description": "Detailed analysis of a specific stock",
            "icon": "🔍"
        }
    }
    
    selected_feature = st.sidebar.radio(
        "Select Analysis Mode",
        list(features.keys()),
        format_func=lambda x: f"{features[x]['icon']} {x}"
    )
    
    st.sidebar.markdown(
        f'<div class="feature-description">{features[selected_feature]["description"]}</div>',
        unsafe_allow_html=True
    )
    
    return selected_feature

def main():
    st.title("📊 Stock Market Analytics Dashboard")
    st.markdown("""
        <div style='background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 25px;'>
            <p style='margin: 0; color: #00FFFF;'>Comprehensive stock market analysis tool with multiple viewing options:</p>
            <ul style='margin: 10px 0 0 20px; color: #888;'>
                <li>Track specific dates or date ranges</li>
                <li>Analyze monthly trends</li>
                <li>Search and monitor individual stocks</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Load data
    data = load_data('financial_metrics.csv')
    if data.empty:
        st.error("No data available. Please check your CSV file.")
        return

    # Feature selection
    view_type = create_feature_selector()
    search_symbol = ""
    
    # Filters section
    st.sidebar.markdown('<p class="section-title">🔍 Filters</p>', unsafe_allow_html=True)
    
    if view_type == "Search🔎":
        search_symbol = st.sidebar.text_input(
            "🔍 Enter Stock Symbol",
            placeholder="e.g., RELIANCE",
            help="Enter the stock symbol to analyze"
        ).strip().upper()
        
        if search_symbol:
            high_dates = get_stock_highs(data, search_symbol)
            if not high_dates.empty:
                st.markdown(f"### Historical Highs for {search_symbol}")
                
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                with metrics_col1:
                    max_price = high_dates['LTP'].max()
                    st.metric("All-Time High", format_number(max_price))
                with metrics_col2:
                    total_highs = len(high_dates)
                    st.metric("Number of High Points", total_highs)
                with metrics_col3:
                    latest_high = high_dates["Today's Date"].max()
                    st.metric("Latest High Date", latest_high.strftime('%d %B %Y'))
                
                st.markdown("### High Points Timeline")
                display_df = high_dates.copy()
                display_df['Date'] = display_df["Today's Date"].dt.strftime('%d %B %Y')
                display_df['LTP'] = display_df['LTP'].apply(format_number)
                display_df['Change'] = display_df['%chng'].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")
                
                st.dataframe(
                    display_df[['Date', 'LTP', 'Change']].sort_values("Today's Date", ascending=False),
                    hide_index=True,
                    column_config={
                        "Date": "Date",
                        "LTP": "Stock Price",
                        "Change": "Daily Change"
                    }
                )              
                # Create price chart
# Price chart (continuing from previous code)
                fig.add_trace(go.Scatter(
                    x=stock_data["Today's Date"],
                    y=stock_data['LTP'],
                    name='Price',
                    line=dict(color='#00FFFF', width=1)
                ))
                
                fig.add_trace(go.Scatter(
                    x=high_dates["Today's Date"],
                    y=high_dates['LTP'],
                    mode='markers',
                    name='High Points',
                    marker=dict(
                        color='#00FF00',
                        size=10,
                        symbol='diamond'
                    )
                ))
                
                fig.update_layout(
                    title=f"Price History and High Points - {search_symbol}",
                    xaxis_title="Date",
                    yaxis_title="Price (₹)",
                    template='plotly_dark',
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                latest_data = get_latest_stock_data(data[data['Symbol'] == search_symbol])
                if not latest_data.empty:
                    st.markdown("### Current Stock Details")
                    st.markdown(create_stock_card(latest_data.iloc[0]), unsafe_allow_html=True)
            else:
                st.warning(f"No data found for symbol {search_symbol}")
        else:
            st.info("Please enter a stock symbol to view its analysis")
        return

    # Handle other view types
    if view_type == "Specific Date⌚":
        selected_date = st.sidebar.date_input(
            "📅 Select Date",
            data["Today's Date"].max(),
            min_value=data["Today's Date"].min(),
            max_value=data["Today's Date"].max(),
            help="Choose a specific date to analyze"
        )
        filtered_data = data[data["Today's Date"].dt.date == selected_date]
        date_display = selected_date.strftime('%d %B %Y')
    
    elif view_type == "Date Range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input(
                "📅 Start Date",
                data["Today's Date"].min(),
                help="Select range start date"
            )
        with col2:
            end_date = st.date_input(
                "📅 End Date",
                data["Today's Date"].max(),
                help="Select range end date"
            )
        
        if start_date <= end_date:
            filtered_data = data[
                (data["Today's Date"].dt.date >= start_date) &
                (data["Today's Date"].dt.date <= end_date)
            ]
            date_display = f"{start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}"
        else:
            st.error("❌ End date must be after start date")
            return
    
    else:  # Month view
        data['Month'] = data["Today's Date"].dt.strftime('%B %Y')
        months = sorted(data['Month'].unique(), 
                       key=lambda x: datetime.strptime(x, '%B %Y'))
        selected_month = st.sidebar.selectbox(
            "📅 Select Month",
            months,
            help="Choose a month to analyze"
        )
        filtered_data = data[data["Today's Date"].dt.strftime('%B %Y') == selected_month]
        date_display = selected_month

    # Stock symbol filter for non-Search views
    if view_type != "Search🔎":
        search_symbol = st.sidebar.text_input(
            "🔍 Filter by Stock Symbol",
            placeholder="e.g., RELIANCE",
            help="Enter a stock symbol to filter results"
        ).strip().upper()

    # Sector filter
    sectors = data['Sector'].unique()
    selected_sectors = st.sidebar.multiselect(
        "🏢 Filter by Sector",
        sectors,
        help="Select one or more sectors to filter"
    )

    # Apply filters
    if search_symbol:
        filtered_data = filtered_data[filtered_data['Symbol'] == search_symbol]
    if selected_sectors:
        filtered_data = filtered_data[filtered_data['Sector'].isin(selected_sectors)]

    # Display results
    if not filtered_data.empty:
        st.markdown(f"### 📊 Analysis for {date_display}")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📈 Total Stocks", len(filtered_data['Symbol'].unique()))
        with col2:
            st.metric("🏢 Total Sectors", len(filtered_data['Sector'].unique()))
        with col3:
            avg_change = filtered_data['%chng'].mean()
            st.metric("📊 Average Change", f"{avg_change:+.2f}%")

        # Sector distribution chart
        st.plotly_chart(create_sector_chart(filtered_data), use_container_width=True)
        
        # Stock cards
        st.markdown("### 📋 Stock Details")
        latest_stock_data = get_latest_stock_data(filtered_data)
        
        stock_col1, stock_col2 = st.columns(2)
        for idx, row in latest_stock_data.iterrows():
            with (stock_col1 if idx % 2 == 0 else stock_col2):
                st.markdown(create_stock_card(row), unsafe_allow_html=True)
    else:
        st.warning("⚠️ No data found for the selected filters.")

if __name__ == "__main__":
    main()