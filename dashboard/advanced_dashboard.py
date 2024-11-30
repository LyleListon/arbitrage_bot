import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def get_db_connection() -> sqlite3.Connection:
    return sqlite3.connect('arbitrage_bot.db')

def get_total_profit() -> float:
    conn = get_db_connection()
    try:
        profit = conn.execute("SELECT SUM(profit) FROM trades").fetchone()[0]
        return profit or 0  # Return 0 if profit is None
    except sqlite3.OperationalError as e:  # Handle potential errors if the table doesn't exist
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()


def get_success_rate() -> float:
    conn = get_db_connection()
    try:
        total_trades = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        profitable_trades = conn.execute("SELECT COUNT(*) FROM trades WHERE profit > 0").fetchone()[0]
        return (profitable_trades / total_trades) * 100 if total_trades else 0
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()


def get_average_roi() -> float:
    conn = get_db_connection()
    try:
        total_roi = conn.execute("SELECT SUM(profit / amount_in) FROM trades").fetchone()[0]
        total_trades = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        return (total_roi / total_trades) * 100 if total_trades else 0
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return 0
    finally:
        conn.close()



def get_performance_data() -> pd.DataFrame:
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        return df
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def create_performance_dashboard() -> None:
    st.title("Arbitrage Bot Performance Dashboard")

    total_profit = get_total_profit()
    success_rate = get_success_rate()
    average_roi = get_average_roi()

    st.metric("Total Profit", f"${total_profit:.2f}")
    st.metric("Success Rate", f"{success_rate:.2f}%")
    st.metric("Average ROI", f"{average_roi:.2f}%")

    performance_data = get_performance_data()
    st.dataframe(performance_data)



def main() -> None:
    create_performance_dashboard()

if __name__ == "__main__":
    main()
