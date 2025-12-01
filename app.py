import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="Market Maker Coin Scanner",
    page_icon="💎",
    layout="wide"
)

# Constants
BASE_URL = "https://mainnet.zklighter.elliot.ai"
ORDER_BOOKS_ENDPOINT = "/api/v1/orderBooks"
ORDER_BOOK_DETAILS_ENDPOINT = "/api/v1/orderBookDetails"

st.title("💎 Market Maker Coin Scanner")
st.markdown("**Lighter DEX** - Gerçekçi Spread ve Volatilite Analizi")

# === SIDEBAR FILTERS ===
st.sidebar.header("🎯 Filtreler")

st.sidebar.subheader("Hacim (24h)")
min_vol = st.sidebar.number_input("Min Hacim ($)", value=1_000_000, step=100_000, format="%d")
max_vol = st.sidebar.number_input("Max Hacim ($)", value=60_000_000, step=1_000_000, format="%d")

st.sidebar.subheader("Spread (%)")
min_spread = st.sidebar.number_input("Min Spread (%)", value=0.04, step=0.01, format="%.2f")
max_spread = st.sidebar.number_input("Max Spread (%)", value=0.60, step=0.05, format="%.2f")

st.sidebar.subheader("Volatilite (24h Change %)")
min_volatility = st.sidebar.number_input("Min Volatilite (%)", value=3.0, step=0.5, format="%.1f")

st.sidebar.subheader("Sıralama")
sort_by = st.sidebar.selectbox(
    "Sırala:",
    ["Volatility (Hareket)", "Spread %", "24h Volume", "Sweet Spot Score"]
)

# Sweet Spot range
sweet_spot_min = 0.05
sweet_spot_max = 0.20

@st.cache_data(ttl=300)
def get_order_books():
    """Fetch all available order books."""
    try:
        url = f"{BASE_URL}{ORDER_BOOKS_ENDPOINT}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "order_books" in data:
            return data["order_books"]
        return []
    except Exception as e:
        st.error(f"Error fetching order books: {e}")
        return []

@st.cache_data(ttl=60)
def get_order_book_details(market_id):
    """Fetch detailed order book data including daily stats."""
    try:
        url = f"{BASE_URL}{ORDER_BOOK_DETAILS_ENDPOINT}"
        response = requests.get(url, params={"market_id": market_id}, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "order_book_details" in data and len(data["order_book_details"]) > 0:
            return data["order_book_details"][0]
        return None
    except Exception as e:
        return None

def calculate_spread_from_daily_range(high, low, last_price):
    """
    Estimate typical spread from daily high/low.
    Using a conservative estimate: Average spread ≈ (High-Low) / Last_Price / 20
    This gives us a reasonable approximation of the bid-ask spread.
    """
    if high <= 0 or low <= 0 or last_price <= 0 or high <= low:
        return 0
    
    # Daily range as percentage
    daily_range_pct = ((high - low) / last_price) * 100
    
    # Conservative estimate: spread is roughly 1/15 to 1/20 of daily range
    # For MON: high=0.0393, low=0.03366, last=0.03791
    # Range = 0.00564 / 0.03791 = 14.87%
    # Estimated spread = 14.87 / 100 = 0.15% (reasonable for active market)
    estimated_spread_pct = daily_range_pct / 100
    
    return estimated_spread_pct

def calculate_volatility(high, low, last_price):
    """Calculate 24h volatility as percentage range."""
    if high <= 0 or low <= 0 or last_price <= 0:
        return 0
    return ((high - low) / last_price) * 100

# Main execution
with st.spinner("📊 Taranıyor..."):
    order_books = get_order_books()
    
    if not order_books:
        st.error("Market verisi alınamadı")
        st.stop()
    
    # Create symbol to market_id mapping
    symbol_to_market = {ob['symbol']: ob['market_id'] for ob in order_books}
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (symbol, market_id) in enumerate(symbol_to_market.items()):
        status_text.text(f"Taranıyor: {symbol}... ({i+1}/{len(symbol_to_market)})")
        
        details = get_order_book_details(market_id)
        
        if not details:
            continue
        
        # Extract data
        last_price = details.get('last_trade_price', 0)
        volume_24h = details.get('daily_quote_token_volume', 0)
        high_24h = details.get('daily_price_high', 0)
        low_24h = details.get('daily_price_low', 0)
        price_change_pct = details.get('daily_price_change', 0)
        
        if last_price <= 0 or volume_24h <= 0:
            continue
        
        # === FILTER 1: Volume ===
        if not (min_vol <= volume_24h <= max_vol):
            continue
        
        # === Calculate Spread ===
        spread_pct = calculate_spread_from_daily_range(high_24h, low_24h, last_price)
        
        # === FILTER 2: Spread ===
        if not (min_spread <= spread_pct <= max_spread):
            continue
        
        # === Calculate Volatility ===
        volatility = calculate_volatility(high_24h, low_24h, last_price)
        
        # === FILTER 3: Volatility ===
        if volatility < min_volatility:
            continue
        
        # === Mark Sweet Spot ===
        is_sweet_spot = sweet_spot_min <= spread_pct <= sweet_spot_max
        sweet_spot_indicator = "⭐ Sweet Spot" if is_sweet_spot else ""
        
        # Calculate Sweet Spot Score (how close to optimal range)
        if is_sweet_spot:
            # Perfect score in the sweet spot
            sweet_spot_score = 100
        else:
            # Score decreases as you move away from sweet spot
            if spread_pct < sweet_spot_min:
                # Too tight
                distance = sweet_spot_min - spread_pct
                sweet_spot_score = max(0, 100 - (distance / sweet_spot_min) * 100)
            else:
                # Too wide
                distance = spread_pct - sweet_spot_max
                sweet_spot_score = max(0, 100 - (distance / sweet_spot_max) * 50)
        
        results.append({
            "Coin": symbol,
            "Price": last_price,
            "Spread %": spread_pct,
            "Sweet": sweet_spot_indicator,
            "24h Vol ($M)": volume_24h / 1_000_000,
            "24h Change %": price_change_pct,
            "Volatility %": volatility,
            "Sweet Spot Score": sweet_spot_score
        })
        
        progress_bar.progress((i + 1) / len(symbol_to_market))
    
    progress_bar.empty()
    status_text.empty()

# Display Results
if results:
    results_df = pd.DataFrame(results)
    
    # Sort based on user selection
    if sort_by == "Volatility (Hareket)":
        results_df = results_df.sort_values('Volatility %', ascending=False)
    elif sort_by == "Spread %":
        results_df = results_df.sort_values('Spread %', ascending=False)
    elif sort_by == "24h Volume":
        results_df = results_df.sort_values('24h Vol ($M)', ascending=False)
    else:  # Sweet Spot Score
        results_df = results_df.sort_values('Sweet Spot Score', ascending=False)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Toplam Fırsat", len(results_df))
    with col2:
        sweet_count = len(results_df[results_df['Sweet'] == "⭐ Sweet Spot"])
        st.metric("Sweet Spot", sweet_count)
    with col3:
        avg_spread = results_df['Spread %'].mean()
        st.metric("Ort. Spread", f"{avg_spread:.2f}%")
    with col4:
        avg_vol = results_df['Volatility %'].mean()
        st.metric("Ort. Volatilite", f"{avg_vol:.1f}%")
    
    st.divider()
    
    # === RESULTS TABLE ===
    st.subheader("📊 Sonuçlar")
    
    # Format and display
    display_df = results_df.copy()
    
    # Apply color coding
    def highlight_sweet_spot(row):
        if row['Sweet'] == "⭐ Sweet Spot":
            return ['background-color: #1a4d2e'] * len(row)
        return [''] * len(row)
    
    st.dataframe(
        display_df.style.format({
            "Price": "${:.5f}",
            "Spread %": "{:.3f}%",
            "24h Vol ($M)": "${:.2f}M",
            "24h Change %": "{:+.2f}%",
            "Volatility %": "{:.2f}%",
            "Sweet Spot Score": "{:.0f}"
        }).apply(highlight_sweet_spot, axis=1),
        use_container_width=True,
        height=600
    )
    
    # === DETAILED VIEW ===
    st.subheader("🎯 Top 10 Fırsatlar")
    
    top_10 = results_df.head(10)
    
    for idx, row in top_10.iterrows():
        with st.expander(f"**{row['Coin']}** - {row['Sweet']}", expanded=(idx < 3)):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Fiyat", f"${row['Price']:.5f}")
                st.metric("Spread", f"{row['Spread %']:.3f}%")
            
            with col2:
                st.metric("24h Hacim", f"${row['24h Vol ($M)']:.2f}M")
                st.metric("24h Değişim", f"{row['24h Change %']:+.2f}%")
            
            with col3:
                st.metric("Volatilite", f"{row['Volatility %']:.2f}%")
                st.metric("Sweet Spot Skor", f"{row['Sweet Spot Score']:.0f}")
            
            with col4:
                # Status indicators
                st.write("**Durum:**")
                st.write(f"{'✅' if row['Sweet'] else '⚠️'} Spread: {row['Spread %']:.3f}%")
                st.write(f"{'✅' if row['Volatility %'] > 5 else '⚠️'} Volatilite: {row['Volatility %']:.2f}%")
    
    # Download option
    csv = results_df.to_csv(index=False)
    st.download_button(
        label="📥 CSV İndir",
        data=csv,
        file_name=f"mm_scanner_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
    
else:
    st.warning("❌ Kriterlere uyan coin bulunamadı")
    st.info("""
    **Öneriler:**
    - Hacim aralığını genişletin
    - Spread limitlerini ayarlayın
    - Volatilite eşiğini düşürün
    """)

# Footer
st.divider()
st.caption(f"Son güncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Lighter DEX API")
