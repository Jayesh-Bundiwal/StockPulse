from datetime import datetime, timedelta
import math
from flask import Blueprint, request, jsonify
from db import get_db, query_all
from auth_helpers import require_login

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/api/analytics/reorder-recommendations", methods=["GET"])
def get_reorder_recommendations():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401

    # Configurable parameters (defaults based on project spec)
    lead_time_days = int(request.args.get("lead_time", 5))       # 5-day lead time
    target_coverage_days = int(request.args.get("target_days", 14)) # 14-day target inventory
    recent_period = 14                                           # Last 14 days
    prior_period = 14                                            # Previous 14 days (days 15-28)

    today = datetime.now().date()
    cutoff_recent = (today - timedelta(days=recent_period - 1)).isoformat()
    cutoff_prior = (today - timedelta(days=recent_period + prior_period - 1)).isoformat()

    conn = get_db()
    try:
        # SQL query fetching stock along with recent and prior sales per product
        query = """
            SELECT 
                p.id, p.name, p.sku, p.category, p.stock, p.cost, p.price, p.threshold_qty AS threshold,
                COALESCE(SUM(CASE WHEN s.sale_date >= %s THEN s.qty ELSE 0 END), 0) AS sales_recent,
                COALESCE(SUM(CASE WHEN s.sale_date >= %s AND s.sale_date < %s THEN s.qty ELSE 0 END), 0) AS sales_prior
            FROM products p
            LEFT JOIN sales s ON s.product_id = p.id
            GROUP BY p.id, p.name, p.sku, p.category, p.stock, p.cost, p.price, p.threshold_qty
        """
        products = query_all(conn, query, (cutoff_recent, cutoff_prior, cutoff_recent))

        recommendations = []

        for p in products:
            stock = p["stock"]
            sales_recent = float(p["sales_recent"])
            sales_prior = float(p["sales_prior"])

            # 1. Calculate Average Daily Demand (ADD)
            add_recent = sales_recent / float(recent_period)
            add_prior = sales_prior / float(prior_period)

            # 2. Demand Trend %
            if add_prior > 0:
                trend_pct = ((add_recent - add_prior) / add_prior) * 100.0
            else:
                trend_pct = 100.0 if add_recent > 0 else 0.0

            # 3. Days of Stock Remaining (DSR)
            if add_recent > 0:
                dsr_days = stock / add_recent
            else:
                dsr_days = 999.0  # Safe / Infinite stock remaining

            # 4. Reorder Point (ROP) = Lead Time Demand + Safety Stock (1.5 * Lead Time Demand)
            lead_time_demand = add_recent * lead_time_days
            safety_stock = 1.5 * add_recent * math.sqrt(lead_time_days)
            reorder_point = lead_time_demand + safety_stock

            # 5. Suggested Reorder Quantity (ROQ)
            target_stock = target_coverage_days * add_recent
            suggested_reorder_qty = max(0, int(math.ceil(target_stock - stock)))

            # Determine if reorder is needed
            reorder_needed = (stock <= reorder_point) or (stock <= p["threshold"]) or (dsr_days <= lead_time_days)

            # 6. Generate Contextual / Explainable Reason
            reasons = []
            if dsr_days < 999.0:
                dsr_rounded = max(0, int(round(dsr_days)))
                reasons.append(f"Product may run out in {dsr_rounded} day(s) at current demand ({add_recent:.1f} units/day).")
            else:
                reasons.append(f"Current stock ({stock} units) is below threshold.")

            if trend_pct > 5.0:
                reasons.append(f"Sales increased {trend_pct:.1f}% over the last 14 days.")
            elif trend_pct < -5.0:
                reasons.append(f"Sales decreased {abs(trend_pct):.1f}% over the last 14 days.")
            else:
                reasons.append("Demand pace remains steady.")

            explainable_reason = " ".join(reasons)

            if reorder_needed:
                recommendations.append({
                    "product_id": p["id"],
                    "name": p["name"],
                    "sku": p["sku"],
                    "category": p["category"],
                    "current_stock": stock,
                    "threshold": p["threshold"],
                    "avg_daily_demand": round(add_recent, 2),
                    "days_remaining": round(dsr_days, 1) if dsr_days < 999.0 else "N/A",
                    "reorder_point": int(math.ceil(reorder_point)),
                    "suggested_reorder_qty": suggested_reorder_qty if suggested_reorder_qty > 0 else (p["threshold"] * 2),
                    "demand_trend_pct": round(trend_pct, 1),
                    "urgency": "CRITICAL" if dsr_days <= 3 or stock == 0 else "WARNING",
                    "reason": explainable_reason
                })

        # Sort recommendations by urgency (lowest days remaining first)
        recommendations.sort(key=lambda x: (x["urgency"] != "CRITICAL", x["days_remaining"] if isinstance(x["days_remaining"], float) else 999))

        return jsonify({
            "total_recommendations": len(recommendations),
            "lead_time_days": lead_time_days,
            "target_coverage_days": target_coverage_days,
            "recommendations": recommendations
        })

    finally:
        conn.close()


@analytics_bp.route("/api/analytics/abc-xyz-matrix", methods=["GET"])
def get_abc_xyz_analysis():
    if not require_login():
        return jsonify({"error": "Not authenticated"}), 401

    days_window = int(request.args.get("days", 30))
    days_window = max(7, min(days_window, 365))

    today = datetime.now().date()
    cutoff_date = (today - timedelta(days=days_window - 1)).isoformat()

    conn = get_db()
    try:
        # 1. Fetch total sales revenue and units per product in the period
        products_query = """
            SELECT 
                p.id, p.name, p.sku, p.category, p.stock, p.price, p.cost,
                COALESCE(SUM(s.revenue), 0) AS total_revenue,
                COALESCE(SUM(s.qty), 0) AS total_units
            FROM products p
            LEFT JOIN sales s ON s.product_id = p.id AND s.sale_date >= %s
            GROUP BY p.id, p.name, p.sku, p.category, p.stock, p.price, p.cost
            ORDER BY total_revenue DESC
        """
        products = query_all(conn, products_query, (cutoff_date,))

        # 2. Fetch daily sales quantities for Coefficient of Variation (CV) calculation
        daily_sales_query = """
            SELECT product_id, sale_date, SUM(qty) AS daily_qty
            FROM sales
            WHERE sale_date >= %s
            GROUP BY product_id, sale_date
        """
        daily_sales = query_all(conn, daily_sales_query, (cutoff_date,))

        # Group daily sales by product_id
        daily_map = {}
        for row in daily_sales:
            pid = row["product_id"]
            if pid not in daily_map:
                daily_map[pid] = {}
            daily_map[pid][row["sale_date"]] = float(row["daily_qty"])

        # Calculate store-wide total revenue for ABC thresholds
        grand_total_revenue = sum(p["total_revenue"] for p in products)
        running_revenue = 0.0

        categorized_products = []
        matrix_counts = {
            "AX": 0, "AY": 0, "AZ": 0,
            "BX": 0, "BY": 0, "BZ": 0,
            "CX": 0, "CY": 0, "CZ": 0
        }

        for p in products:
            rev = float(p["total_revenue"])
            running_revenue += rev

            # --- A/B/C Classification ---
            cum_pct = (running_revenue / grand_total_revenue * 100.0) if grand_total_revenue > 0 else 100.0
            rev_share = (rev / grand_total_revenue * 100.0) if grand_total_revenue > 0 else 0.0

            if grand_total_revenue == 0 or cum_pct <= 80.0 or rev == max(pr["total_revenue"] for pr in products):
                abc_class = "A"
            elif cum_pct <= 95.0:
                abc_class = "B"
            else:
                abc_class = "C"

            # --- X/Y/Z Classification ---
            pid = p["id"]
            p_daily = daily_map.get(pid, {})
            
            # Fill 0 for days without sales to form a complete time series
            daily_series = []
            for d in range(days_window):
                day_str = (today - timedelta(days=d)).isoformat()
                daily_series.append(p_daily.get(day_str, 0.0))

            mean_qty = sum(daily_series) / days_window
            
            if mean_qty > 0:
                variance = sum((x - mean_qty) ** 2 for x in daily_series) / days_window
                std_dev = math.sqrt(variance)
                cv = std_dev / mean_qty
            else:
                cv = 999.0  # Infinite variability (no demand)

            if cv <= 0.5:
                xyz_class = "X"
            elif cv <= 1.0:
                xyz_class = "Y"
            else:
                xyz_class = "Z"

            combined_class = f"{abc_class}{xyz_class}"
            matrix_counts[combined_class] += 1

            # Strategy recommendation lookup
            strategy_map = {
                "AX": "Strict Stocking (High Value, Constant Demand)",
                "AY": "Continuous Monitoring (High Value, Fluctuating)",
                "AZ": "High-Risk Buffer Stock (High Value, Sporadic)",
                "BX": "Standard Automatic Reorder (Med Value, Stable)",
                "BY": "Periodic Safety Stock Review (Med Value, Variable)",
                "BZ": "Low Safety Stock (Med Value, Sporadic)",
                "CX": "Bulk Order / Low Touch (Low Value, Constant)",
                "CY": "Minimal Buffer (Low Value, Variable)",
                "CZ": "On-Demand / JIT (Low Value, Unpredictable)"
            }

            categorized_products.append({
                "product_id": p["id"],
                "name": p["name"],
                "sku": p["sku"],
                "category": p["category"],
                "stock": p["stock"],
                "total_revenue": round(rev, 2),
                "revenue_share_pct": round(rev_share, 1),
                "cumulative_revenue_pct": round(cum_pct, 1),
                "avg_daily_qty": round(mean_qty, 2),
                "cv": round(cv, 2) if cv < 999 else "N/A",
                "abc_class": abc_class,
                "xyz_class": xyz_class,
                "matrix_category": combined_class,
                "recommended_strategy": strategy_map[combined_class]
            })

        return jsonify({
            "days_window": days_window,
            "total_products": len(categorized_products),
            "grand_total_revenue": round(grand_total_revenue, 2),
            "matrix_distribution": matrix_counts,
            "products": categorized_products
        })

    finally:
        conn.close()