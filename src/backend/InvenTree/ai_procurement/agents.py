import datetime
import json
import random
import requests
import pandas as pd
from prophet import Prophet
from django.db.models import Sum

from part.models import Part
from stock.models import StockItem

# ==========================================
# AGENT 1: The Data Fetcher
# ==========================================
def fetch_part_data(part_id):
    """Gathers current stock and historical demand from InvenTree."""
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return None, "Part not found"

    # 1. Get current stock
    stock_items = StockItem.objects.filter(part=part)
    current_stock = stock_items.aggregate(total=Sum('quantity'))['total'] or 0

    # 2. Get demand history 
    # NOTE FOR MVP: InvenTree's actual stock tracking history is spread across multiple tables 
    # (StockItemTracking, SalesOrders, etc.). To get this working end-to-end right now, 
    # we generate a reliable mock dataframe of the last 180 days. 
    # We will swap this for a real ORM aggregation once the pipeline runs.
    dates = pd.date_range(end=datetime.date.today(), periods=180)
    history_df = pd.DataFrame({
        'ds': dates,
        'y': [random.randint(0, 5) for _ in range(180)] # Simulated daily usage
    })

    data = {
        'part_id': part.id,
        'part_name': part.name,
        'minimum_stock': part.minimum_stock or 0,
        'current_stock': current_stock,
        'history_df': history_df
    }
    return data, None


# ==========================================
# AGENT 2: The Forecaster (Prophet)
# ==========================================
def run_forecast(history_df, days_ahead=30):
    """Takes the history dataframe (ds, y) and predicts future demand."""
    # Suppress verbose prophet output for cleaner logs
    m = Prophet(daily_seasonality=True, yearly_seasonality=False)
    m.fit(history_df)
    
    future = m.make_future_dataframe(periods=days_ahead)
    forecast = m.predict(future)

    # Sum the forecasted demand for the upcoming period
    future_forecast = forecast.tail(days_ahead)
    predicted_demand = future_forecast['yhat'].sum()

    # Demand can't be negative
    return max(0, int(predicted_demand))


# ==========================================
# AGENT 3: The Decision Maker (Ollama)
# ==========================================
def get_procurement_decision(part_data, predicted_demand):
    """Feeds the context to local Llama3 and demands a JSON response."""
    prompt = f"""
    You are an AI procurement agent for a manufacturing company.
    Analyze the following data and decide if we need to order more stock.

    Part: {part_data['part_name']}
    Current Stock: {part_data['current_stock']}
    Minimum Required Stock: {part_data['minimum_stock']}
    Forecasted Demand (next 30 days): {predicted_demand}

    Based on this, should we order more? If yes, how much?
    Return ONLY a valid JSON object with exactly these keys:
    "decision" (string: "ORDER" or "DO_NOT_ORDER"),
    "quantity" (integer: amount to order, 0 if DO_NOT_ORDER),
    "reasoning" (string: 1-2 short sentences explaining why).
    """

    try:
        response = requests.post(
            'http://host.docker.internal:11434/api/generate',
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"  # Forces Ollama to output strictly valid JSON
            },
            timeout=45
        )
        response.raise_for_status()
        result = response.json().get('response', '{}')
        return json.loads(result)
    except Exception as e:
        return {
            "decision": "ERROR",
            "quantity": 0,
            "reasoning": f"Failed to reach Ollama or parse response: {str(e)}"
        }


# ==========================================
# ORCHESTRATOR
# ==========================================
def run_procurement_pipeline(part_id):
    """Runs all 3 agents in sequence and returns the final payload."""
    # 1. Fetch
    part_data, error = fetch_part_data(part_id)
    if error:
        return {"error": error}

    # 2. Forecast
    predicted_demand = run_forecast(part_data['history_df'])

    # 3. Decide
    decision = get_procurement_decision(part_data, predicted_demand)

    # 4. Package for the frontend
    return {
        "part_id": part_data['part_id'],
        "part_name": part_data['part_name'],
        "current_stock": part_data['current_stock'],
        "minimum_stock": part_data['minimum_stock'],
        "forecasted_demand_30d": predicted_demand,
        "recommendation": decision
    }